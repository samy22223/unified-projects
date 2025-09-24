"""
Usage Tracking Middleware for AI Platform
Automatically tracks API usage for billing and rate limiting
"""

import time
import logging
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.core.subscriptions.subscription_manager import subscription_manager

logger = logging.getLogger(__name__)

class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API usage for billing"""

    def __init__(self, app, excluded_paths: list = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            '/health', '/docs', '/openapi.json', '/metrics'
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tracking for excluded paths
        if any(path in request.url.path for path in self.excluded_paths):
            return await call_next(request)

        # Get user ID from request (would come from JWT token)
        user_id = self._get_user_id_from_request(request)
        if not user_id:
            # Allow request but don't track usage
            return await call_next(request)

        start_time = time.time()

        # Process the request
        response = await call_next(request)

        processing_time = time.time() - start_time

        # Track usage asynchronously (don't block response)
        if response.status_code < 400:  # Only track successful requests
            await self._track_request_usage(request, user_id, processing_time, response)

        return response

    def _get_user_id_from_request(self, request: Request) -> str:
        """Extract user ID from request (JWT token, API key, etc.)"""
        # Check Authorization header for JWT
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In production, decode JWT to get user ID
            # For now, return placeholder
            return "user_123"

        # Check for API key
        api_key = request.headers.get('X-API-Key') or request.query_params.get('api_key')
        if api_key:
            # In production, validate API key and get user ID
            return f"api_user_{hash(api_key) % 10000}"

        return None

    async def _track_request_usage(
        self,
        request: Request,
        user_id: str,
        processing_time: float,
        response: Response
    ):
        """Track API request usage"""
        try:
            # Determine resource type from path
            path = request.url.path
            method = request.method

            # Map endpoints to resources
            resource_mapping = {
                '/api/v1/ai/': 'ai_requests',
                '/api/v1/chat': 'chat_requests',
                '/api/v1/images/': 'image_requests',
                '/api/v1/audio/': 'audio_requests',
                '/api/v1/files/': 'file_operations',
                '/api/v1/analytics': 'analytics_requests',
            }

            resource = 'api_calls'  # Default
            for endpoint, res in resource_mapping.items():
                if endpoint in path:
                    resource = res
                    break

            # Track the request
            await subscription_manager.record_usage(user_id, resource, 1)

            # Track processing time for performance analytics
            await self._track_performance_metrics(path, method, processing_time)

            # Check rate limits
            rate_limit_exceeded = await self._check_rate_limits(user_id, resource)
            if rate_limit_exceeded:
                logger.warning(f"Rate limit exceeded for user {user_id} on {resource}")

        except Exception as e:
            logger.error(f"Failed to track usage: {e}")

    async def _track_performance_metrics(self, path: str, method: str, processing_time: float):
        """Track API performance metrics"""
        try:
            # Store performance data in Redis for monitoring
            perf_key = f"performance:{path}:{method}"
            subscription_manager.redis.lpush(perf_key, processing_time)
            subscription_manager.redis.ltrim(perf_key, 0, 999)  # Keep last 1000 measurements
            subscription_manager.redis.expire(perf_key, 86400)  # 24 hours

        except Exception as e:
            logger.error(f"Failed to track performance: {e}")

    async def _check_rate_limits(self, user_id: str, resource: str) -> bool:
        """Check if user has exceeded rate limits"""
        try:
            # Get user's plan limits
            subscription = await subscription_manager.get_user_subscription(user_id)
            plan = subscription_manager.plans.get(
                subscription.plan_id if subscription else 'free',
                subscription_manager.plans['free']
            )

            # Check current usage against limits
            allowed, limits = await subscription_manager.check_usage_limits(
                user_id, resource, 0  # Check without incrementing
            )

            return not allowed

        except Exception as e:
            logger.error(f"Failed to check rate limits: {e}")
            return False

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

async def check_rate_limit(request: Request, user_id: str) -> bool:
    """Check rate limit for a request (can be used in route handlers)"""
    path = request.url.path

    # Define rate limits per endpoint (requests per minute)
    rate_limits = {
        '/api/v1/ai/generate': 60,    # 60 requests per minute
        '/api/v1/chat': 120,          # 120 requests per minute
        '/api/v1/images/generate': 30, # 30 requests per minute
        '/api/v1/audio/transcribe': 20, # 20 requests per minute
    }

    # Get default limit
    limit = 100  # Default 100 requests per minute
    for endpoint, endpoint_limit in rate_limits.items():
        if endpoint in path:
            limit = endpoint_limit
            break

    # Check current usage in last minute
    current_minute = time.strftime('%Y%m%d%H%M')
    rate_key = f"rate_limit:{user_id}:{path}:{current_minute}"

    current_usage = subscription_manager.redis.get(rate_key) or 0
    current_usage = int(current_usage)

    if current_usage >= limit:
        return False

    # Increment usage
    subscription_manager.redis.incr(rate_key)
    subscription_manager.redis.expire(rate_key, 60)  # Expire in 1 minute

    return True

def rate_limit_middleware(threshold: int = 100, window_seconds: int = 60):
    """Decorator for route-specific rate limiting"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and user_id from args/kwargs
            request = None
            user_id = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            # Check rate limit
            if request and user_id:
                allowed = await check_rate_limit(request, user_id)
                if not allowed:
                    raise RateLimitExceeded("Rate limit exceeded")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Custom exception handler for rate limits
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded exceptions"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": 60  # seconds
        },
        headers={"Retry-After": "60"}
    )

# Usage tracking for specific AI operations
async def track_ai_usage(user_id: str, operation: str, tokens_used: int = 0, model: str = None):
    """Track AI-specific usage metrics"""
    try:
        # Track the operation
        await subscription_manager.record_usage(user_id, f"ai_{operation}", 1)

        # Track token usage if applicable
        if tokens_used > 0:
            await subscription_manager.record_usage(user_id, "ai_tokens", tokens_used)

        # Track model usage
        if model:
            model_usage_key = f"model_usage:{user_id}:{model}"
            subscription_manager.redis.incr(model_usage_key)
            subscription_manager.redis.expire(model_usage_key, 2592000)  # 30 days

        # Check if user is approaching limits
        allowed, limits = await subscription_manager.check_usage_limits(user_id, "monthly_requests", 0)
        if not allowed:
            logger.warning(f"User {user_id} has exceeded monthly request limit")

    except Exception as e:
        logger.error(f"Failed to track AI usage: {e}")

# Billing integration helpers
async def calculate_prorated_amount(
    current_plan_price: int,
    new_plan_price: int,
    days_remaining: int,
    total_days: int
) -> int:
    """Calculate prorated amount for plan changes"""
    if days_remaining <= 0:
        return 0

    # Calculate unused portion of current plan
    unused_amount = (current_plan_price * days_remaining) // total_days

    # Calculate new plan cost for remaining period
    new_plan_prorated = (new_plan_price * days_remaining) // total_days

    # Return difference (positive = credit, negative = charge)
    return new_plan_prorated - unused_amount

async def generate_invoice_preview(
    user_id: str,
    new_plan_id: str,
    billing_cycle: str = "month"
) -> Dict[str, Any]:
    """Generate invoice preview for plan changes"""
    try:
        subscription = await subscription_manager.get_user_subscription(user_id)
        if not subscription:
            return {"error": "No active subscription"}

        current_plan = subscription_manager.plans[subscription.plan_id]
        new_plan = subscription_manager.plans[new_plan_id]

        # Calculate dates
        now = time.time()
        period_end = subscription.current_period_end.timestamp()
        days_remaining = int((period_end - now) / 86400)
        total_days = 30 if billing_cycle == "month" else 365

        # Calculate prorated amounts
        current_price = current_plan.price_monthly if billing_cycle == "month" else current_plan.price_yearly
        new_price = new_plan.price_monthly if billing_cycle == "month" else new_plan.price_yearly

        prorated_amount = await calculate_prorated_amount(
            current_price, new_price, days_remaining, total_days
        )

        return {
            "current_plan": current_plan.name,
            "new_plan": new_plan.name,
            "billing_cycle": billing_cycle,
            "days_remaining": days_remaining,
            "prorated_amount": prorated_amount,
            "currency": "usd",
            "next_billing_date": subscription.current_period_end.isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to generate invoice preview: {e}")
        return {"error": "Failed to generate preview"}