"""
Subscription Management API Endpoints
Handles subscription lifecycle, plan management, and billing
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from src.core.subscriptions.subscription_manager import subscription_manager, SubscriptionPlan

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# Pydantic models
class CreateSubscriptionRequest(BaseModel):
    plan_id: str = Field(..., description="Subscription plan ID")
    billing_cycle: str = Field(default="month", description="Billing cycle (month/year)")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    coupon_code: Optional[str] = Field(None, description="Discount coupon code")

class ChangePlanRequest(BaseModel):
    new_plan_id: str = Field(..., description="New subscription plan ID")
    new_billing_cycle: Optional[str] = Field(None, description="New billing cycle")
    prorate: bool = Field(default=True, description="Apply prorated charges")

class UsageCheckRequest(BaseModel):
    resource: str = Field(..., description="Resource to check (e.g., 'monthly_requests')")
    amount: int = Field(default=1, description="Amount to check")

class RecordUsageRequest(BaseModel):
    resource: str = Field(..., description="Resource used")
    amount: int = Field(default=1, description="Amount used")

@router.get("/plans", response_model=List[Dict[str, Any]])
async def get_subscription_plans():
    """
    Get all available subscription plans

    Returns detailed information about each subscription tier
    including features, limits, and pricing.
    """
    plans = []
    for plan_id, plan in subscription_manager.plans.items():
        if plan.is_active:
            plans.append({
                'plan_id': plan.plan_id,
                'name': plan.name,
                'description': plan.description,
                'pricing': {
                    'monthly': plan.price_monthly,
                    'yearly': plan.price_yearly
                },
                'features': plan.features,
                'limits': plan.limits
            })

    return plans

@router.get("/plans/{plan_id}", response_model=Dict[str, Any])
async def get_subscription_plan(plan_id: str):
    """
    Get detailed information about a specific subscription plan
    """
    if plan_id not in subscription_manager.plans:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan = subscription_manager.plans[plan_id]
    if not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not available")

    return {
        'plan_id': plan.plan_id,
        'name': plan.name,
        'description': plan.description,
        'pricing': {
            'monthly': plan.price_monthly,
            'yearly': plan.price_yearly
        },
        'features': plan.features,
        'limits': plan.limits
    }

@router.post("/create", response_model=Dict[str, Any])
async def create_subscription(request: CreateSubscriptionRequest, user_id: str):
    """
    Create a new subscription for the authenticated user

    This endpoint creates a Stripe subscription and sets up
    the user's plan with appropriate permissions and limits.
    """
    return await subscription_manager.create_subscription(
        user_id=user_id,
        plan_id=request.plan_id,
        billing_cycle=request.billing_cycle,
        payment_method_id=request.payment_method_id,
        coupon_code=request.coupon_code
    )

@router.get("/current", response_model=Dict[str, Any])
async def get_current_subscription(user_id: str):
    """
    Get the current user's subscription details

    Returns subscription status, plan information, and billing details.
    """
    subscription = await subscription_manager.get_user_subscription(user_id)

    if not subscription:
        return {
            'status': 'none',
            'plan': subscription_manager.plans['free'].__dict__,
            'message': 'No active subscription'
        }

    plan = subscription_manager.plans.get(subscription.plan_id, subscription_manager.plans['free'])

    return {
        'subscription_id': subscription.subscription_id,
        'stripe_subscription_id': subscription.stripe_subscription_id,
        'status': subscription.status,
        'plan': {
            'plan_id': plan.plan_id,
            'name': plan.name,
            'description': plan.description
        },
        'billing': {
            'current_period_start': subscription.current_period_start.isoformat(),
            'current_period_end': subscription.current_period_end.isoformat(),
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'billing_cycle': subscription.metadata.get('billing_cycle', 'month')
        },
        'limits': plan.limits,
        'features': plan.features
    }

@router.post("/cancel", response_model=Dict[str, Any])
async def cancel_subscription(
    cancel_at_period_end: bool = True,
    cancellation_reason: Optional[str] = None,
    user_id: str = None
):
    """
    Cancel the current user's subscription

    Can cancel immediately or at the end of the current billing period.
    """
    return await subscription_manager.cancel_subscription(
        user_id=user_id,
        cancel_at_period_end=cancel_at_period_end,
        cancellation_reason=cancellation_reason
    )

@router.post("/change-plan", response_model=Dict[str, Any])
async def change_subscription_plan(request: ChangePlanRequest, user_id: str):
    """
    Change the current user's subscription plan

    Supports plan upgrades/downgrades with optional proration.
    """
    return await subscription_manager.change_subscription_plan(
        user_id=user_id,
        new_plan_id=request.new_plan_id,
        new_billing_cycle=request.new_billing_cycle,
        prorate=request.prorate
    )

@router.post("/check-usage", response_model=Dict[str, Any])
async def check_usage_limits(request: UsageCheckRequest, user_id: str):
    """
    Check if user has exceeded usage limits for a resource

    Returns whether the requested usage is allowed and current limits.
    """
    allowed, limits = await subscription_manager.check_usage_limits(
        user_id=user_id,
        resource=request.resource,
        amount=request.amount
    )

    return {
        'allowed': allowed,
        'limits': limits
    }

@router.post("/record-usage", response_model=Dict[str, Any])
async def record_usage(request: RecordUsageRequest, user_id: str):
    """
    Record resource usage for billing and analytics

    This endpoint should be called whenever a user consumes a billable resource.
    """
    new_usage = await subscription_manager.record_usage(
        user_id=user_id,
        resource=request.resource,
        amount=request.amount
    )

    return {
        'recorded': True,
        'new_usage': new_usage,
        'resource': request.resource,
        'amount': request.amount
    }

@router.get("/usage", response_model=Dict[str, Any])
async def get_usage_stats(user_id: str):
    """
    Get current usage statistics for the user

    Returns usage data for the current billing period.
    """
    current_month = datetime.utcnow().strftime('%Y%m')

    usage_stats = {}
    for resource in ['monthly_requests', 'storage_gb', 'api_calls']:
        usage_key = f"usage:{user_id}:{resource}:{current_month}"
        current_usage = subscription_manager.redis.get(usage_key) or 0

        # Get plan limits
        subscription = await subscription_manager.get_user_subscription(user_id)
        plan = subscription_manager.plans.get(
            subscription.plan_id if subscription else 'free',
            subscription_manager.plans['free']
        )

        limit = plan.limits.get(resource, 0)

        usage_stats[resource] = {
            'current': int(current_usage),
            'limit': limit,
            'remaining': max(0, limit - int(current_usage)) if limit != -1 else -1,
            'percentage': min(100, (int(current_usage) / limit * 100)) if limit > 0 else 0
        }

    return {
        'period': current_month,
        'usage': usage_stats
    }

@router.get("/analytics")
async def get_subscription_analytics(
    days: int = 30,
    api_key: str = Depends(get_admin_api_key)  # Admin only endpoint
):
    """
    Get subscription analytics (Admin only)

    Returns aggregated subscription data for business intelligence.
    """
    from datetime import datetime, timedelta

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    analytics = await subscription_manager.get_subscription_analytics(start_date, end_date)

    return analytics

@router.post("/webhooks/stripe")
async def stripe_subscription_webhook(
    request: dict,
    background_tasks: BackgroundTasks
):
    """
    Handle Stripe subscription webhooks

    Processes subscription lifecycle events from Stripe.
    """
    # This would integrate with the unified webhook handler
    # For now, return success
    return {"status": "processed"}

# Helper function (would be in auth middleware)
async def get_admin_api_key(api_key: str):
    """Validate admin API key"""
    # Simplified - in production, validate against database
    if api_key != os.getenv('ADMIN_API_KEY', 'admin_key'):
        raise HTTPException(status_code=403, detail="Invalid admin API key")
    return api_key

# User ID dependency (would be from JWT token)
async def get_current_user_id():
    """Get current user ID from JWT token"""
    # Simplified - in production, decode JWT token
    return "user_123"  # Placeholder