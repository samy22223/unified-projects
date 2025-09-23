"""
Auto-Completion API Endpoints

This module contains all API endpoints for the auto-completion system,
providing RESTful interfaces for completion requests and management.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import time

from src.core.autocomplete.service import AutoCompletionService, AutoCompletionRequest, AutoCompletionResult
from src.core.autocomplete.cache import AutoCompletionCache
from src.core.autocomplete.context import AutoCompletionContext

# Create router
router = APIRouter()
logger = logging.getLogger(__name__)

# Global service instances
autocomplete_service = AutoCompletionService()
cache_manager = AutoCompletionCache()
context_manager = AutoCompletionContext()


# Pydantic models for API requests/responses
class CompletionRequest(BaseModel):
    """Request model for auto-completion."""
    query: str = Field(..., description="The partial input to complete", min_length=1, max_length=1000)
    context: str = Field(default="", description="Additional context information")
    provider_types: List[str] = Field(default_factory=lambda: ["all"], description="Types of providers to use")
    max_results: int = Field(default=10, description="Maximum number of results", ge=1, le=50)
    timeout: float = Field(default=5.0, description="Request timeout in seconds", ge=0.1, le=30.0)
    user_id: Optional[str] = Field(None, description="User identifier for context")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "query": "agent create",
                "context": "Creating a new AI agent",
                "provider_types": ["ai_agent", "search"],
                "max_results": 10,
                "timeout": 3.0,
                "user_id": "user123",
                "session_id": "session456",
                "metadata": {"source": "ide", "language": "python"}
            }
        }


class CompletionResponse(BaseModel):
    """Response model for auto-completion results."""
    query: str
    completions: List[Dict[str, Any]]
    provider_used: str
    response_time: float
    cached: bool
    timestamp: datetime
    metadata: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "query": "agent create",
                "completions": [
                    {
                        "completion": "agent create --name",
                        "score": 0.95,
                        "provider": "ai_agent",
                        "metadata": {"type": "agent_command"}
                    }
                ],
                "provider_used": "ai_agent",
                "response_time": 0.045,
                "cached": False,
                "timestamp": "2025-01-22T10:30:00Z",
                "metadata": {"total_candidates": 15}
            }
        }


class BatchCompletionRequest(BaseModel):
    """Request model for batch auto-completion."""
    requests: List[CompletionRequest] = Field(..., description="List of completion requests", max_items=10)
    user_id: Optional[str] = Field(None, description="User identifier for context")
    session_id: Optional[str] = Field(None, description="Session identifier")


class BatchCompletionResponse(BaseModel):
    """Response model for batch auto-completion results."""
    results: List[CompletionResponse]
    total_time: float
    timestamp: datetime


class ContextUpdateRequest(BaseModel):
    """Request model for context updates."""
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    app_context: Optional[str] = Field(None, description="Application context")
    updates: Dict[str, Any] = Field(..., description="Context updates")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "session_id": "session456",
                "app_context": "api_development",
                "updates": {
                    "current_application": "api",
                    "current_task": "creating_endpoint",
                    "preferences": {"theme": "dark"}
                }
            }
        }


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    total_requests: int
    hit_rate: float
    redis_hits: int
    redis_misses: int
    memory_hits: int
    memory_misses: int
    cache_size: int
    evictions: int
    redis_available: bool
    memory_items: int
    redis_info: Dict[str, Any]
    timestamp: str


class ServiceStatsResponse(BaseModel):
    """Response model for service statistics."""
    total_requests: int
    cache_hit_rate: float
    error_rate: float
    average_response_time: float
    provider_usage: Dict[str, int]
    active_providers: int
    timestamp: str


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    service_status: str
    cache_status: str
    context_status: str
    providers_status: Dict[str, str]
    timestamp: str


# Dependency functions
async def get_autocomplete_service() -> AutoCompletionService:
    """Dependency to get autocomplete service instance."""
    return autocomplete_service


async def get_cache_manager() -> AutoCompletionCache:
    """Dependency to get cache manager instance."""
    return cache_manager


async def get_context_manager() -> AutoCompletionContext:
    """Dependency to get context manager instance."""
    return context_manager


@router.post("/completions", response_model=CompletionResponse)
async def get_completions(
    request: CompletionRequest,
    background_tasks: BackgroundTasks,
    service: AutoCompletionService = Depends(get_autocomplete_service)
):
    """
    Get auto-completion suggestions for a query.

    This endpoint provides intelligent auto-completion suggestions based on
    the query, context, and available providers.
    """
    try:
        start_time = time.time()

        # Create internal request object
        internal_request = AutoCompletionRequest(
            query=request.query,
            context=request.context,
            provider_types=request.provider_types,
            max_results=request.max_results,
            timeout=request.timeout,
            user_id=request.user_id,
            session_id=request.session_id,
            metadata=request.metadata
        )

        # Get completions
        result = await service.get_completions(internal_request)

        # Update context with the request
        if request.user_id or request.session_id:
            background_tasks.add_task(
                update_context_background,
                request.user_id,
                request.session_id,
                request.query,
                result.provider_used
            )

        logger.info(f"Completion request processed in {result.response_time:.3f}s for query: {request.query}")

        return CompletionResponse(
            query=result.query,
            completions=result.completions,
            provider_used=result.provider_used,
            response_time=result.response_time,
            cached=result.cached,
            timestamp=result.timestamp,
            metadata=result.metadata
        )

    except Exception as e:
        logger.error(f"Error processing completion request: {e}")
        raise HTTPException(status_code=500, detail=f"Completion request failed: {str(e)}")


async def update_context_background(user_id: str, session_id: str, query: str, provider_used: str):
    """Update context in background."""
    try:
        updates = {
            "current_query": query,
            "last_provider_used": provider_used,
            "last_activity": datetime.utcnow()
        }
        await context_manager.update_user_context(user_id, session_id, updates)
    except Exception as e:
        logger.error(f"Error updating context: {e}")


@router.post("/completions/batch", response_model=BatchCompletionResponse)
async def get_batch_completions(
    request: BatchCompletionRequest,
    background_tasks: BackgroundTasks,
    service: AutoCompletionService = Depends(get_autocomplete_service)
):
    """
    Get auto-completion suggestions for multiple queries.

    This endpoint processes multiple completion requests concurrently
    for improved performance.
    """
    try:
        start_time = time.time()

        # Process all requests concurrently
        tasks = []
        for completion_request in request.requests:
            internal_request = AutoCompletionRequest(
                query=completion_request.query,
                context=completion_request.context,
                provider_types=completion_request.provider_types,
                max_results=completion_request.max_results,
                timeout=completion_request.timeout,
                user_id=request.user_id or completion_request.user_id,
                session_id=request.session_id or completion_request.session_id,
                metadata=completion_request.metadata
            )
            tasks.append(service.get_completions(internal_request))

        # Wait for all completions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        completion_responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch completion {i}: {result}")
                # Return error response for failed request
                completion_responses.append(CompletionResponse(
                    query=request.requests[i].query,
                    completions=[],
                    provider_used="error",
                    response_time=0.0,
                    cached=False,
                    timestamp=datetime.utcnow(),
                    metadata={"error": str(result)}
                ))
            else:
                completion_responses.append(CompletionResponse(
                    query=result.query,
                    completions=result.completions,
                    provider_used=result.provider_used,
                    response_time=result.response_time,
                    cached=result.cached,
                    timestamp=result.timestamp,
                    metadata=result.metadata
                ))

        total_time = time.time() - start_time

        # Update context for batch request
        if request.user_id or request.session_id:
            background_tasks.add_task(
                update_batch_context_background,
                request.user_id,
                request.session_id,
                request.requests
            )

        return BatchCompletionResponse(
            results=completion_responses,
            total_time=total_time,
            timestamp=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error processing batch completion request: {e}")
        raise HTTPException(status_code=500, detail=f"Batch completion request failed: {str(e)}")


async def update_batch_context_background(user_id: str, session_id: str, requests: List[CompletionRequest]):
    """Update context for batch requests in background."""
    try:
        # Update with batch information
        updates = {
            "batch_request_count": len(requests),
            "batch_queries": [req.query for req in requests],
            "last_batch_time": datetime.utcnow()
        }
        await context_manager.update_user_context(user_id, session_id, updates)
    except Exception as e:
        logger.error(f"Error updating batch context: {e}")


@router.post("/context", response_model=Dict[str, str])
async def update_context(
    request: ContextUpdateRequest,
    context_mgr: AutoCompletionContext = Depends(get_context_manager)
):
    """
    Update context information for better auto-completion.

    This endpoint allows updating user preferences, application context,
    and other contextual information that improves completion quality.
    """
    try:
        # Update user context
        if request.user_id or request.session_id:
            await context_mgr.update_user_context(
                request.user_id or "",
                request.session_id or "",
                request.updates
            )

        # Update application context
        if request.app_context:
            await context_mgr.update_application_context(request.app_context, request.updates)

        # Update session context
        if request.session_id:
            await context_mgr.update_session_context(request.session_id, request.updates)

        return {"message": "Context updated successfully"}

    except Exception as e:
        logger.error(f"Error updating context: {e}")
        raise HTTPException(status_code=500, detail=f"Context update failed: {str(e)}")


@router.get("/context/{user_id}", response_model=Dict[str, Any])
async def get_context(
    user_id: str,
    context_mgr: AutoCompletionContext = Depends(get_context_manager)
):
    """
    Get context information for a user.

    This endpoint provides access to user context, preferences,
    and learned patterns for debugging and analysis.
    """
    try:
        context = await context_mgr.get_context(user_id=user_id)
        return context

    except Exception as e:
        logger.error(f"Error getting context for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    cache_mgr: AutoCompletionCache = Depends(get_cache_manager)
):
    """
    Get cache performance statistics.

    This endpoint provides detailed statistics about cache performance,
    hit rates, and memory usage for monitoring and optimization.
    """
    try:
        stats = await cache_mgr.get_stats()
        return CacheStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Cache stats retrieval failed: {str(e)}")


@router.get("/service/stats", response_model=ServiceStatsResponse)
async def get_service_stats(
    service: AutoCompletionService = Depends(get_autocomplete_service)
):
    """
    Get service performance statistics.

    This endpoint provides statistics about the auto-completion service
    including request counts, response times, and provider usage.
    """
    try:
        stats = await service.get_metrics()
        return ServiceStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        raise HTTPException(status_code=500, detail=f"Service stats retrieval failed: {str(e)}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    service: AutoCompletionService = Depends(get_autocomplete_service),
    cache_mgr: AutoCompletionCache = Depends(get_cache_manager),
    context_mgr: AutoCompletionContext = Depends(get_context_manager)
):
    """
    Get health status of the auto-completion system.

    This endpoint provides comprehensive health information for all
    components of the auto-completion system.
    """
    try:
        # Get health status from all components
        service_health = await service.health_check()
        cache_health = await cache_mgr.health_check()
        context_health = await context_mgr.health_check()

        # Aggregate provider status
        providers_status = {}
        for provider_name, status in service_health.get("providers", {}).items():
            providers_status[provider_name] = status

        # Determine overall status
        overall_status = "healthy"
        if (cache_health.get("status") != "healthy" or
            context_health.get("status") != "healthy" or
            "unhealthy" in providers_status.values()):
            overall_status = "degraded"

        return HealthCheckResponse(
            status=overall_status,
            service_status=service_health.get("status", "unknown"),
            cache_status=cache_health.get("status", "unknown"),
            context_status=context_health.get("status", "unknown"),
            providers_status=providers_status,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error performing health check: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(
    cache_mgr: AutoCompletionCache = Depends(get_cache_manager)
):
    """
    Clear the auto-completion cache.

    This endpoint clears all cached completion results. Use with caution
    as it will impact performance until cache is rebuilt.
    """
    try:
        await cache_mgr.clear()
        return {"message": "Cache cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.post("/cache/warmup")
async def warmup_cache(
    keys: List[str],
    cache_mgr: AutoCompletionCache = Depends(get_cache_manager)
):
    """
    Warm up the cache with pre-computed completions.

    This endpoint pre-populates the cache with completions for common queries
    to improve initial response times.
    """
    try:
        await cache_mgr.warmup(keys)
        return {"message": f"Cache warmup initiated for {len(keys)} keys"}

    except Exception as e:
        logger.error(f"Error warming up cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache warmup failed: {str(e)}")


@router.delete("/context/{user_id}")
async def clear_user_context(
    user_id: str,
    context_mgr: AutoCompletionContext = Depends(get_context_manager)
):
    """
    Clear context information for a specific user.

    This endpoint removes all learned context and preferences for a user.
    """
    try:
        await context_mgr.clear_user_context(user_id)
        return {"message": f"Context cleared for user: {user_id}"}

    except Exception as e:
        logger.error(f"Error clearing user context: {e}")
        raise HTTPException(status_code=500, detail=f"Context clear failed: {str(e)}")


# Error handlers
@router.exception_handler(HTTPException)
async def autocomplete_http_exception_handler(request, exc):
    """Custom HTTP exception handler for auto-completion endpoints."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.exception_handler(Exception)
async def autocomplete_general_exception_handler(request, exc):
    """General exception handler for auto-completion endpoints."""
    logger.error(f"Auto-completion API error: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "status_code": 500,
        "path": str(request.url),
        "timestamp": datetime.utcnow().isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }
