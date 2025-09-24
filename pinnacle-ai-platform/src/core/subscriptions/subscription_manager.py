"""
Subscription Management System for Pinnacle AI Platform
Handles recurring payments, plan management, and billing cycles
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import stripe
from fastapi import HTTPException
import redis

logger = logging.getLogger(__name__)

@dataclass
class SubscriptionPlan:
    """Subscription plan configuration"""
    plan_id: str
    name: str
    description: str
    price_monthly: int  # Price in cents
    price_yearly: int   # Price in cents
    features: List[str]
    limits: Dict[str, Any]  # API limits, storage, etc.
    stripe_price_monthly: str
    stripe_price_yearly: str
    is_active: bool = True

@dataclass
class UserSubscription:
    """User subscription data"""
    user_id: str
    subscription_id: str
    plan_id: str
    status: str  # 'active', 'canceled', 'past_due', 'incomplete'
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    stripe_customer_id: str
    stripe_subscription_id: str
    metadata: Dict[str, Any]

class SubscriptionManager:
    """Manages AI platform subscriptions and billing"""

    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Define subscription plans
        self.plans = {
            'free': SubscriptionPlan(
                plan_id='free',
                name='Free Tier',
                description='Basic AI features for getting started',
                price_monthly=0,
                price_yearly=0,
                features=[
                    '100 AI requests per month',
                    'Basic AI models',
                    'Community support',
                    '1GB storage'
                ],
                limits={
                    'monthly_requests': 100,
                    'storage_gb': 1,
                    'models': ['basic'],
                    'support': 'community'
                },
                stripe_price_monthly='',
                stripe_price_yearly='',
                is_active=True
            ),
            'basic': SubscriptionPlan(
                plan_id='basic',
                name='Basic Plan',
                description='Essential AI capabilities for individuals',
                price_monthly=999,   # $9.99
                price_yearly=9999,   # $99.99
                features=[
                    '1,000 AI requests per month',
                    'All AI models',
                    'Email support',
                    '10GB storage',
                    'API access'
                ],
                limits={
                    'monthly_requests': 1000,
                    'storage_gb': 10,
                    'models': ['all'],
                    'support': 'email',
                    'api_access': True
                },
                stripe_price_monthly=os.getenv('STRIPE_PRICE_BASIC_MONTHLY', 'price_basic_monthly'),
                stripe_price_yearly=os.getenv('STRIPE_PRICE_BASIC_YEARLY', 'price_basic_yearly'),
                is_active=True
            ),
            'pro': SubscriptionPlan(
                plan_id='pro',
                name='Professional Plan',
                description='Advanced AI tools for professionals',
                price_monthly=2999,  # $29.99
                price_yearly=29999,  # $299.99
                features=[
                    '10,000 AI requests per month',
                    'Priority processing',
                    'Phone & email support',
                    '100GB storage',
                    'Advanced analytics',
                    'Custom integrations'
                ],
                limits={
                    'monthly_requests': 10000,
                    'storage_gb': 100,
                    'models': ['all'],
                    'support': 'phone_email',
                    'api_access': True,
                    'priority_processing': True,
                    'analytics': True,
                    'custom_integrations': True
                },
                stripe_price_monthly=os.getenv('STRIPE_PRICE_PRO_MONTHLY', 'price_pro_monthly'),
                stripe_price_yearly=os.getenv('STRIPE_PRICE_PRO_YEARLY', 'price_pro_yearly'),
                is_active=True
            ),
            'enterprise': SubscriptionPlan(
                plan_id='enterprise',
                name='Enterprise Plan',
                description='Unlimited AI power for organizations',
                price_monthly=9999,  # $99.99
                price_yearly=99999,  # $999.99
                features=[
                    'Unlimited AI requests',
                    'Dedicated support',
                    'Unlimited storage',
                    'White-label options',
                    'SLA guarantee',
                    'Custom AI models',
                    'On-premise deployment'
                ],
                limits={
                    'monthly_requests': -1,  # Unlimited
                    'storage_gb': -1,        # Unlimited
                    'models': ['all'],
                    'support': 'dedicated',
                    'api_access': True,
                    'priority_processing': True,
                    'analytics': True,
                    'custom_integrations': True,
                    'white_label': True,
                    'sla': True,
                    'custom_models': True,
                    'on_premise': True
                },
                stripe_price_monthly=os.getenv('STRIPE_PRICE_ENTERPRISE_MONTHLY', 'price_enterprise_monthly'),
                stripe_price_yearly=os.getenv('STRIPE_PRICE_ENTERPRISE_YEARLY', 'price_enterprise_yearly'),
                is_active=True
            )
        }

    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        billing_cycle: str = 'month',
        payment_method_id: Optional[str] = None,
        coupon_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new subscription for a user"""
        try:
            if plan_id not in self.plans:
                raise HTTPException(status_code=400, detail="Invalid plan ID")

            plan = self.plans[plan_id]
            if not plan.is_active:
                raise HTTPException(status_code=400, detail="Plan is not available")

            # Check if user already has an active subscription
            existing_subscription = await self.get_user_subscription(user_id)
            if existing_subscription and existing_subscription.status == 'active':
                raise HTTPException(status_code=400, detail="User already has an active subscription")

            # Get or create Stripe customer
            customer_id = await self._get_or_create_stripe_customer(user_id)

            # Get the appropriate price ID
            price_id = plan.stripe_price_monthly if billing_cycle == 'month' else plan.stripe_price_yearly

            # Prepare subscription data
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': {
                    'user_id': user_id,
                    'plan_id': plan_id,
                    'billing_cycle': billing_cycle
                }
            }

            # Add payment method if provided
            if payment_method_id:
                subscription_data['default_payment_method'] = payment_method_id

            # Add coupon if provided
            if coupon_code:
                # Validate coupon (simplified)
                if await self._validate_coupon(coupon_code):
                    subscription_data['coupon'] = coupon_code

            # Create subscription in Stripe
            subscription = stripe.Subscription.create(**subscription_data)

            # Store subscription data locally
            user_subscription = UserSubscription(
                user_id=user_id,
                subscription_id=f"sub_{user_id}_{plan_id}",
                plan_id=plan_id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end),
                cancel_at_period_end=subscription.cancel_at_period_end,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription.id,
                metadata={
                    'billing_cycle': billing_cycle,
                    'price_id': price_id,
                    'coupon_code': coupon_code
                }
            )

            await self._store_subscription(user_subscription)

            # Update user permissions based on plan
            await self._update_user_permissions(user_id, plan)

            return {
                'subscription_id': user_subscription.subscription_id,
                'stripe_subscription_id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'plan': {
                    'plan_id': plan.plan_id,
                    'name': plan.name,
                    'billing_cycle': billing_cycle,
                    'price': plan.price_monthly if billing_cycle == 'month' else plan.price_yearly
                }
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def cancel_subscription(
        self,
        user_id: str,
        cancel_at_period_end: bool = True,
        cancellation_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cancel a user's subscription"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                raise HTTPException(status_code=404, detail="No active subscription found")

            # Cancel in Stripe
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=cancel_at_period_end
            )

            # Update local subscription status
            subscription.status = 'canceled' if not cancel_at_period_end else 'active'
            subscription.cancel_at_period_end = cancel_at_period_end
            subscription.metadata['cancellation_reason'] = cancellation_reason
            subscription.metadata['cancelled_at'] = datetime.utcnow().isoformat()

            await self._store_subscription(subscription)

            # Schedule permission updates
            if cancel_at_period_end:
                # Keep permissions until period end
                pass
            else:
                # Immediately revoke permissions
                await self._update_user_permissions(user_id, self.plans['free'])

            return {
                'subscription_id': subscription.subscription_id,
                'status': subscription.status,
                'cancel_at_period_end': cancel_at_period_end,
                'current_period_end': subscription.current_period_end.isoformat()
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription cancellation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def change_subscription_plan(
        self,
        user_id: str,
        new_plan_id: str,
        new_billing_cycle: Optional[str] = None,
        prorate: bool = True
    ) -> Dict[str, Any]:
        """Change a user's subscription plan"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                raise HTTPException(status_code=404, detail="No active subscription found")

            if new_plan_id not in self.plans:
                raise HTTPException(status_code=400, detail="Invalid plan ID")

            new_plan = self.plans[new_plan_id]
            billing_cycle = new_billing_cycle or subscription.metadata.get('billing_cycle', 'month')

            # Get new price ID
            new_price_id = new_plan.stripe_price_monthly if billing_cycle == 'month' else new_plan.stripe_price_yearly

            # Update subscription in Stripe
            stripe_subscription = stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    'id': subscription.stripe_subscription_id + '_item',  # Simplified
                    'price': new_price_id
                }],
                proration_behavior='create_prorations' if prorate else 'none'
            )

            # Update local subscription
            subscription.plan_id = new_plan_id
            subscription.metadata['previous_plan'] = subscription.plan_id
            subscription.metadata['plan_changed_at'] = datetime.utcnow().isoformat()

            await self._store_subscription(subscription)

            # Update user permissions
            await self._update_user_permissions(user_id, new_plan)

            return {
                'subscription_id': subscription.subscription_id,
                'old_plan': subscription.metadata['previous_plan'],
                'new_plan': new_plan_id,
                'billing_cycle': billing_cycle,
                'prorated': prorate
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe plan change failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def get_user_subscription(self, user_id: str) -> Optional[UserSubscription]:
        """Get user's current subscription"""
        try:
            subscription_data = self.redis.hgetall(f"subscription:{user_id}")
            if not subscription_data:
                return None

            return UserSubscription(
                user_id=user_id,
                subscription_id=subscription_data['subscription_id'],
                plan_id=subscription_data['plan_id'],
                status=subscription_data['status'],
                current_period_start=datetime.fromisoformat(subscription_data['current_period_start']),
                current_period_end=datetime.fromisoformat(subscription_data['current_period_end']),
                cancel_at_period_end=subscription_data.get('cancel_at_period_end', 'False') == 'True',
                stripe_customer_id=subscription_data['stripe_customer_id'],
                stripe_subscription_id=subscription_data['stripe_subscription_id'],
                metadata=json.loads(subscription_data.get('metadata', '{}'))
            )

        except Exception as e:
            logger.error(f"Failed to get user subscription: {e}")
            return None

    async def check_usage_limits(self, user_id: str, resource: str, amount: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """Check if user has exceeded usage limits for their plan"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                # Free tier limits
                plan = self.plans['free']
            else:
                plan = self.plans.get(subscription.plan_id, self.plans['free'])

            limit = plan.limits.get(resource, 0)
            if limit == -1:  # Unlimited
                return True, {'remaining': -1, 'limit': -1}

            # Get current usage for this month
            current_month = datetime.utcnow().strftime('%Y%m')
            usage_key = f"usage:{user_id}:{resource}:{current_month}"
            current_usage = self.redis.get(usage_key) or 0
            current_usage = int(current_usage)

            remaining = max(0, limit - current_usage - amount)
            allowed = current_usage + amount <= limit

            return allowed, {
                'current_usage': current_usage,
                'limit': limit,
                'remaining': remaining,
                'requested': amount,
                'period': current_month
            }

        except Exception as e:
            logger.error(f"Failed to check usage limits: {e}")
            return False, {'error': str(e)}

    async def record_usage(self, user_id: str, resource: str, amount: int = 1):
        """Record resource usage for billing/analytics"""
        try:
            current_month = datetime.utcnow().strftime('%Y%m')
            usage_key = f"usage:{user_id}:{resource}:{current_month}"

            # Increment usage
            new_usage = self.redis.incrby(usage_key, amount)

            # Set expiry (keep for 6 months)
            self.redis.expire(usage_key, 15552000)  # 6 months in seconds

            # Check if approaching limit
            allowed, limits = await self.check_usage_limits(user_id, resource, 0)
            if limits.get('remaining', 0) < 100:  # Less than 100 remaining
                await self._send_usage_warning(user_id, resource, limits)

            return new_usage

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")

    async def get_subscription_analytics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get subscription analytics for the specified period"""
        try:
            analytics = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'subscriptions': {},
                'revenue': {},
                'churn': {},
                'plans': {}
            }

            # This would aggregate data from Redis/database
            # Simplified implementation
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y%m%d')

                # Get daily metrics (would be stored in Redis/database)
                analytics['subscriptions'][date_str] = {
                    'new': 0,      # New subscriptions
                    'cancelled': 0, # Cancelled subscriptions
                    'active': 0    # Total active
                }

                analytics['revenue'][date_str] = {
                    'total': 0,    # Total revenue
                    'recurring': 0, # Recurring revenue
                    'new': 0       # New revenue
                }

                current_date += timedelta(days=1)

            return analytics

        except Exception as e:
            logger.error(f"Failed to get subscription analytics: {e}")
            return {}

    async def _get_or_create_stripe_customer(self, user_id: str) -> str:
        """Get existing Stripe customer or create new one"""
        try:
            # Check if we have a stored customer ID
            customer_key = f"stripe_customer:{user_id}"
            customer_id = self.redis.get(customer_key)

            if customer_id:
                return customer_id

            # Create new customer (would need user email/name from database)
            # Simplified - in production, get user data from database
            customer = stripe.Customer.create(
                email=f"user_{user_id}@example.com",  # Placeholder
                name=f"User {user_id}",               # Placeholder
                metadata={'user_id': user_id}
            )

            # Store customer ID
            self.redis.set(customer_key, customer.id)

            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create/get Stripe customer: {e}")
            raise

    async def _store_subscription(self, subscription: UserSubscription):
        """Store subscription data in Redis"""
        try:
            subscription_data = {
                'subscription_id': subscription.subscription_id,
                'plan_id': subscription.plan_id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start.isoformat(),
                'current_period_end': subscription.current_period_end.isoformat(),
                'cancel_at_period_end': str(subscription.cancel_at_period_end),
                'stripe_customer_id': subscription.stripe_customer_id,
                'stripe_subscription_id': subscription.stripe_subscription_id,
                'metadata': json.dumps(subscription.metadata)
            }

            self.redis.hmset(f"subscription:{subscription.user_id}", subscription_data)

        except Exception as e:
            logger.error(f"Failed to store subscription: {e}")

    async def _update_user_permissions(self, user_id: str, plan: SubscriptionPlan):
        """Update user permissions based on subscription plan"""
        try:
            # Store user permissions in Redis
            permissions_key = f"permissions:{user_id}"
            permissions = {
                'plan_id': plan.plan_id,
                'limits': json.dumps(plan.limits),
                'features': json.dumps(plan.features),
                'updated_at': datetime.utcnow().isoformat()
            }

            self.redis.hmset(permissions_key, permissions)
            self.redis.expire(permissions_key, 2592000)  # 30 days

        except Exception as e:
            logger.error(f"Failed to update user permissions: {e}")

    async def _validate_coupon(self, coupon_code: str) -> bool:
        """Validate coupon code (simplified)"""
        # In production, check against database/API
        valid_coupons = ['WELCOME10', 'SAVE20', 'AIYEAR']
        return coupon_code in valid_coupons

    async def _send_usage_warning(self, user_id: str, resource: str, limits: Dict[str, Any]):
        """Send usage warning notification"""
        try:
            # In production, send email/SMS/webhook notification
            warning_data = {
                'user_id': user_id,
                'resource': resource,
                'current_usage': limits['current_usage'],
                'limit': limits['limit'],
                'remaining': limits['remaining'],
                'timestamp': datetime.utcnow().isoformat()
            }

            # Store warning for dashboard
            warning_key = f"usage_warning:{user_id}:{resource}"
            self.redis.setex(warning_key, 86400, json.dumps(warning_data))  # 24 hours

            logger.info(f"Usage warning sent to user {user_id} for {resource}")

        except Exception as e:
            logger.error(f"Failed to send usage warning: {e}")

# Global subscription manager instance
subscription_manager = SubscriptionManager()