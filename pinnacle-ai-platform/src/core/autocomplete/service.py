"""
Core Auto-Completion Service

This module contains the main AutoCompletionService class that orchestrates
all auto-completion providers and manages caching, context, and request handling.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from .cache import AutoCompletionCache
from .context import AutoCompletionContext
from .providers.base import BaseAutoCompletionProvider
from .providers.ai_agent import AIAgentProvider
from .providers.api_endpoint import APIEndpointProvider
from .providers.database import DatabaseProvider
from .providers.ui import UIProvider
from .providers.cli import CLIProvider
from .providers.config import ConfigProvider
from .providers.search import SearchProvider


@dataclass
class AutoCompletionRequest:
    """Request model for auto-completion."""
    query: str
    context: str = ""
    provider_types: List[str] = field(default_factory=lambda: ["all"])
    max_results: int = 10
    timeout: float = 5.0
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutoCompletionResult:
    """Result model for auto-completion."""
    query: str
    completions: List[Dict[str, Any]]
    provider_used: str
    response_time: float
    cached: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutoCompletionService:
    """
    Main auto-completion service that orchestrates all providers.

    This service manages multiple auto-completion providers, caching,
    context handling, and provides a unified interface for auto-completion requests.
    """

    def __init__(self):
        """Initialize the auto-completion service."""
        self.logger = logging.getLogger(__name__)

        # Initialize cache
        self.cache = AutoCompletionCache()

        # Initialize context manager
        self.context_manager = AutoCompletionContext()

        # Initialize providers
        self.providers: Dict[str, BaseAutoCompletionProvider] = {}
        self._initialize_providers()

        # Thread pool for concurrent provider execution
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
            "provider_usage": {},
            "errors": 0
        }

        self.logger.info("AutoCompletionService initialized with providers: %s",
                        list(self.providers.keys()))

    def _initialize_providers(self):
        """Initialize all auto-completion providers."""
        try:
            # Initialize all 7 specialized providers
            self.providers["ai_agent"] = AIAgentProvider()
            self.providers["api_endpoint"] = APIEndpointProvider()
            self.providers["database"] = DatabaseProvider()
            self.providers["ui"] = UIProvider()
            self.providers["cli"] = CLIProvider()
            self.providers["config"] = ConfigProvider()
            self.providers["search"] = SearchProvider()

            self.logger.info("All auto-completion providers initialized successfully")

        except Exception as e:
            self.logger.error(f"Error initializing providers: {e}")
            raise

    async def get_completions(self, request: AutoCompletionRequest) -> AutoCompletionResult:
        """
        Get auto-completions for a given query.

        Args:
            request: AutoCompletionRequest containing query and parameters

        Returns:
            AutoCompletionResult with completions and metadata
        """
        start_time = time.time()
        self.metrics["total_requests"] += 1

        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self.cache.get(cache_key)

            if cached_result:
                self.metrics["cache_hits"] += 1
                response_time = time.time() - start_time
                self._update_metrics(response_time)

                return AutoCompletionResult(
                    query=request.query,
                    completions=cached_result,
                    provider_used="cache",
                    response_time=response_time,
                    cached=True,
                    metadata={"cache_key": cache_key}
                )

            self.metrics["cache_misses"] += 1

            # Get context for the request
            context = await self.context_manager.get_context(
                user_id=request.user_id,
                session_id=request.session_id
            )

            # Determine which providers to use
            providers_to_use = self._select_providers(request.provider_types, context)

            # Execute providers concurrently
            completions = await self._execute_providers(
                request, providers_to_use, context
            )

            # Merge and rank results
            merged_completions = self._merge_and_rank_completions(completions)

            # Limit results
            final_completions = merged_completions[:request.max_results]

            # Cache the result
            await self.cache.set(cache_key, final_completions, ttl=300)  # 5 minute TTL

            response_time = time.time() - start_time
            self._update_metrics(response_time)

            # Determine primary provider used
            primary_provider = self._determine_primary_provider(completions)

            return AutoCompletionResult(
                query=request.query,
                completions=final_completions,
                provider_used=primary_provider,
                response_time=response_time,
                cached=False,
                metadata={
                    "providers_used": list(providers_to_use.keys()),
                    "total_candidates": len(merged_completions),
                    "context_used": bool(context)
                }
            )

        except Exception as e:
            self.metrics["errors"] += 1
            response_time = time.time() - start_time
            self.logger.error(f"Error in get_completions: {e}")

            # Return fallback result
            return AutoCompletionResult(
                query=request.query,
                completions=[],
                provider_used="error",
                response_time=response_time,
                metadata={"error": str(e)}
            )

    def _generate_cache_key(self, request: AutoCompletionRequest) -> str:
        """Generate a cache key for the request."""
        key_components = [
            request.query,
            request.context,
            str(sorted(request.provider_types)),
            str(request.max_results),
            request.user_id or "",
            request.session_id or ""
        ]
        return f"ac:{hash(tuple(key_components))}"

    def _select_providers(self, provider_types: List[str],
                         context: Dict[str, Any]) -> Dict[str, BaseAutoCompletionProvider]:
        """Select which providers to use based on request and context."""
        if "all" in provider_types:
            return self.providers.copy()

        selected_providers = {}
        for provider_type in provider_types:
            if provider_type in self.providers:
                selected_providers[provider_type] = self.providers[provider_type]

        # If no specific providers requested, use context-aware selection
        if not selected_providers:
            selected_providers = self._context_aware_provider_selection(context)

        return selected_providers

    def _context_aware_provider_selection(self, context: Dict[str, Any]) -> Dict[str, BaseAutoCompletionProvider]:
        """Select providers based on context."""
        selected = {}

        # Always include core providers
        selected["ai_agent"] = self.providers["ai_agent"]
        selected["search"] = self.providers["search"]

        # Add context-specific providers
        if context.get("current_application") == "api":
            selected["api_endpoint"] = self.providers["api_endpoint"]

        if context.get("current_application") == "database":
            selected["database"] = self.providers["database"]

        if context.get("ui_context"):
            selected["ui"] = self.providers["ui"]

        if context.get("cli_context"):
            selected["cli"] = self.providers["cli"]

        if context.get("config_context"):
            selected["config"] = self.providers["config"]

        return selected

    async def _execute_providers(self, request: AutoCompletionRequest,
                               providers: Dict[str, BaseAutoCompletionProvider],
                               context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Execute providers concurrently with timeout."""
        tasks = {}
        results = {}

        # Create tasks for each provider
        for provider_name, provider in providers.items():
            task = asyncio.create_task(
                self._execute_provider_with_timeout(provider, request, context, request.timeout)
            )
            tasks[provider_name] = task

        # Wait for all tasks to complete
        for provider_name, task in tasks.items():
            try:
                result = await task
                if result:
                    results[provider_name] = result
            except asyncio.TimeoutError:
                self.logger.warning(f"Provider {provider_name} timed out")
                results[provider_name] = []
            except Exception as e:
                self.logger.error(f"Error executing provider {provider_name}: {e}")
                results[provider_name] = []

        return results

    async def _execute_provider_with_timeout(self, provider: BaseAutoCompletionProvider,
                                           request: AutoCompletionRequest,
                                           context: Dict[str, Any],
                                           timeout: float) -> List[Dict[str, Any]]:
        """Execute a single provider with timeout."""
        try:
            # Use thread pool for CPU-bound operations
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    provider.get_completions,
                    request.query,
                    request.context,
                    context
                ),
                timeout=timeout
            )
            return result
        except Exception as e:
            self.logger.error(f"Provider execution error: {e}")
            return []

    def _merge_and_rank_completions(self, provider_results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Merge and rank completions from all providers."""
        all_completions = []

        for provider_name, completions in provider_results.items():
            for completion in completions:
                # Add provider information to completion
                completion["_provider"] = provider_name
                completion["_score"] = completion.get("score", 0.5)
                all_completions.append(completion)

        # Sort by score (descending) and remove duplicates
        all_completions.sort(key=lambda x: x.get("_score", 0), reverse=True)

        # Remove duplicates based on completion text
        seen = set()
        unique_completions = []
        for completion in all_completions:
            completion_text = completion.get("completion", "")
            if completion_text not in seen:
                seen.add(completion_text)
                unique_completions.append(completion)

        return unique_completions

    def _determine_primary_provider(self, provider_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """Determine which provider provided the best results."""
        if not provider_results:
            return "none"

        # Find provider with highest scoring results
        best_provider = "ai_agent"  # Default fallback
        best_score = 0

        for provider_name, completions in provider_results.items():
            if completions:
                max_completion_score = max(
                    (c.get("score", 0) for c in completions),
                    default=0
                )
                if max_completion_score > best_score:
                    best_score = max_completion_score
                    best_provider = provider_name

        return best_provider

    def _update_metrics(self, response_time: float):
        """Update performance metrics."""
        total_requests = self.metrics["total_requests"]
        current_avg = self.metrics["average_response_time"]

        # Update rolling average
        self.metrics["average_response_time"] = (
            (current_avg * (total_requests - 1)) + response_time
        ) / total_requests

    async def get_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics."""
        return {
            **self.metrics,
            "cache_hit_rate": (
                self.metrics["cache_hits"] /
                max(self.metrics["total_requests"], 1)
            ),
            "error_rate": (
                self.metrics["errors"] /
                max(self.metrics["total_requests"], 1)
            ),
            "active_providers": len(self.providers),
            "timestamp": datetime.utcnow()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the service."""
        provider_status = {}
        for name, provider in self.providers.items():
            try:
                # Simple health check for each provider
                provider_status[name] = "healthy"
            except Exception as e:
                provider_status[name] = f"unhealthy: {str(e)}"

        cache_status = await self.cache.health_check()

        return {
            "service": "healthy",
            "providers": provider_status,
            "cache": cache_status,
            "metrics": await self.get_metrics()
        }

    async def refresh_providers(self):
        """Refresh all providers (useful for reloading configurations)."""
        self.logger.info("Refreshing all providers...")

        for name, provider in self.providers.items():
            try:
                await provider.refresh()
                self.logger.info(f"Provider {name} refreshed successfully")
            except Exception as e:
                self.logger.error(f"Error refreshing provider {name}: {e}")

    async def shutdown(self):
        """Shutdown the service and cleanup resources."""
        self.logger.info("Shutting down AutoCompletionService...")

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Shutdown providers
        for name, provider in self.providers.items():
            try:
                await provider.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down provider {name}: {e}")

        # Clear cache
        await self.cache.clear()

        self.logger.info("AutoCompletionService shutdown complete")