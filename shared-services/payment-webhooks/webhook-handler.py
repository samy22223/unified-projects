#!/usr/bin/env python3
"""
Unified Payment Webhook Handler for Unified Projects
Handles webhooks from Stripe for both Pinnacle AI Platform and Free E-commerce Store
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import stripe
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import redis
import aiohttp
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from retry_engine import retry_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FastApiIntegration()],
        environment=os.getenv('ENVIRONMENT', 'development')
    )

# Initialize Redis for webhook deduplication
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    decode_responses=True
)

# Initialize FastAPI
app = FastAPI(
    title="Unified Payment Webhooks",
    description="Centralized webhook handler for Stripe payments across unified projects",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class WebhookProcessor:
    """Centralized webhook processing for all platforms"""

    def __init__(self):
        self.platform_endpoints = {
            'pinnacle_ai': os.getenv('PINNACLE_AI_WEBHOOK_URL'),
            'free_ecommerce': os.getenv('FREE_ECOMMERCE_WEBHOOK_URL'),
        }
        self.webhook_secrets = {
            'pinnacle_ai': os.getenv('PINNACLE_AI_WEBHOOK_SECRET'),
            'free_ecommerce': os.getenv('FREE_ECOMMERCE_WEBHOOK_SECRET'),
        }

    async def process_webhook(self, platform: str, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process webhook for specific platform"""
        try:
            # Parse webhook data
            event = json.loads(payload)
            event_type = event.get('type')
            event_data = event.get('data', {}).get('object', {})

            # Handle payment failures with retry logic
            if event_type == 'payment_intent.payment_failed':
                payment_intent = event_data
                failure_reason = self._extract_failure_reason(payment_intent)

                # Schedule retry for recoverable failures
                if self._is_retryable_failure(failure_reason):
                    await retry_engine.schedule_retry(
                        payment_intent_id=payment_intent.get('id'),
                        failure_reason=failure_reason,
                        platform=platform,
                        metadata={
                            'amount': payment_intent.get('amount'),
                            'currency': payment_intent.get('currency'),
                            'customer_id': payment_intent.get('customer')
                        }
                    )
                    logger.info(f"Scheduled retry for failed payment {payment_intent.get('id')}")

            # Continue with normal processing
            # Verify webhook signature
            secret = self.webhook_secrets.get(platform)
            if not secret:
                raise HTTPException(status_code=400, detail=f"Webhook secret not configured for {platform}")

            event = stripe.Webhook.construct_event(payload, signature, secret)

            # Check for duplicate events
            event_key = f"webhook:{platform}:{event.id}"
            if redis_client.exists(event_key):
                logger.info(f"Duplicate webhook event: {event.id}")
                return {"status": "duplicate", "event_id": event.id}

            # Mark event as processed
            redis_client.setex(event_key, 86400, "processed")  # 24 hours

            # Process event based on type
            result = await self._process_event(platform, event)

            logger.info(f"Successfully processed webhook: {event.id} for {platform}")
            return {
                "status": "processed",
                "event_id": event.id,
                "event_type": event.type,
                "platform": platform,
                "result": result
            }

        except stripe.error.SignatureVerificationError:
            logger.error(f"Webhook signature verification failed for {platform}")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook processing failed for {platform}: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    async def _process_event(self, platform: str, event) -> Dict[str, Any]:
        """Process individual webhook events"""
        event_handlers = {
            # Payment events
            'payment_intent.succeeded': self._handle_payment_success,
            'payment_intent.payment_failed': self._handle_payment_failure,
            'payment_intent.canceled': self._handle_payment_cancelled,

            # Subscription events
            'customer.subscription.created': self._handle_subscription_created,
            'customer.subscription.updated': self._handle_subscription_updated,
            'customer.subscription.deleted': self._handle_subscription_cancelled,

            # Invoice events
            'invoice.payment_succeeded': self._handle_invoice_payment_succeeded,
            'invoice.payment_failed': self._handle_invoice_payment_failed,

            # Dispute events
            'charge.dispute.created': self._handle_dispute_created,
            'charge.dispute.closed': self._handle_dispute_closed,
        }

        handler = event_handlers.get(event.type)
        if handler:
            return await handler(platform, event.data.object)
        else:
            logger.warning(f"Unhandled webhook event type: {event.type}")
            return {"action": "ignored", "reason": "unhandled_event_type"}

    async def _handle_payment_success(self, platform: str, payment_intent) -> Dict[str, Any]:
        """Handle successful payment"""
        logger.info(f"Payment succeeded: {payment_intent.id} on {platform}")

        # Forward to platform-specific handler
        await self._forward_to_platform(platform, {
            "event": "payment_success",
            "payment_intent_id": payment_intent.id,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "customer_id": payment_intent.customer,
            "metadata": payment_intent.metadata
        })

        # Update payment analytics
        await self._update_payment_analytics(platform, payment_intent)

        return {
            "action": "payment_completed",
            "payment_intent_id": payment_intent.id,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency
        }

    async def _handle_payment_failure(self, platform: str, payment_intent) -> Dict[str, Any]:
        """Handle failed payment"""
        logger.warning(f"Payment failed: {payment_intent.id} on {platform}")

        # Forward to platform-specific handler
        await self._forward_to_platform(platform, {
            "event": "payment_failure",
            "payment_intent_id": payment_intent.id,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "last_payment_error": payment_intent.last_payment_error,
            "metadata": payment_intent.metadata
        })

        # Log failure for analysis
        await self._log_payment_failure(platform, payment_intent)

        return {
            "action": "payment_failed",
            "payment_intent_id": payment_intent.id,
            "failure_reason": payment_intent.last_payment_error
        }

    async def _handle_subscription_created(self, platform: str, subscription) -> Dict[str, Any]:
        """Handle new subscription"""
        logger.info(f"Subscription created: {subscription.id} on {platform}")

        await self._forward_to_platform(platform, {
            "event": "subscription_created",
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "metadata": subscription.metadata
        })

        return {
            "action": "subscription_activated",
            "subscription_id": subscription.id,
            "customer_id": subscription.customer
        }

    async def _handle_subscription_updated(self, platform: str, subscription) -> Dict[str, Any]:
        """Handle subscription updates"""
        logger.info(f"Subscription updated: {subscription.id} on {platform}")

        await self._forward_to_platform(platform, {
            "event": "subscription_updated",
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "metadata": subscription.metadata
        })

        return {
            "action": "subscription_updated",
            "subscription_id": subscription.id
        }

    async def _handle_subscription_cancelled(self, platform: str, subscription) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        logger.info(f"Subscription cancelled: {subscription.id} on {platform}")

        await self._forward_to_platform(platform, {
            "event": "subscription_cancelled",
            "subscription_id": subscription.id,
            "customer_id": subscription.customer,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "metadata": subscription.metadata
        })

        return {
            "action": "subscription_cancelled",
            "subscription_id": subscription.id
        }

    async def _handle_invoice_payment_succeeded(self, platform: str, invoice) -> Dict[str, Any]:
        """Handle successful subscription payment"""
        logger.info(f"Invoice payment succeeded: {invoice.id} on {platform}")

        await self._forward_to_platform(platform, {
            "event": "invoice_payment_succeeded",
            "invoice_id": invoice.id,
            "subscription_id": invoice.subscription,
            "customer_id": invoice.customer,
            "amount_paid": invoice.amount_paid,
            "currency": invoice.currency
        })

        return {
            "action": "invoice_paid",
            "invoice_id": invoice.id,
            "amount": invoice.amount_paid
        }

    async def _handle_dispute_created(self, platform: str, dispute) -> Dict[str, Any]:
        """Handle charge dispute"""
        logger.warning(f"Dispute created: {dispute.id} on {platform}")

        # Alert administrators
        await self._alert_administrators("dispute_created", {
            "dispute_id": dispute.id,
            "charge_id": dispute.charge,
            "amount": dispute.amount,
            "currency": dispute.currency,
            "reason": dispute.reason,
            "platform": platform
        })

        return {
            "action": "dispute_alert_sent",
            "dispute_id": dispute.id
        }

    async def _forward_to_platform(self, platform: str, event_data: Dict[str, Any]):
        """Forward webhook event to platform-specific handler"""
        endpoint = self.platform_endpoints.get(platform)
        if not endpoint:
            logger.warning(f"No endpoint configured for platform: {platform}")
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=event_data,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Source": "unified-webhook-handler"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully forwarded webhook to {platform}")
                    else:
                        logger.error(f"Failed to forward webhook to {platform}: {response.status}")

        except Exception as e:
            logger.error(f"Error forwarding webhook to {platform}: {e}")

    async def _update_payment_analytics(self, platform: str, payment_intent):
        """Update payment analytics in Redis"""
        try:
            # Store payment data for analytics
            analytics_key = f"analytics:{platform}:payments:{datetime.utcnow().strftime('%Y-%m-%d')}"
            redis_client.hincrby(analytics_key, "total_payments", 1)
            redis_client.hincrby(analytics_key, f"amount_{payment_intent.currency}", payment_intent.amount)

            # Set expiry (90 days)
            redis_client.expire(analytics_key, 7776000)

        except Exception as e:
            logger.error(f"Failed to update payment analytics: {e}")

    async def _log_payment_failure(self, platform: str, payment_intent):
        """Log payment failure for analysis"""
        try:
            failure_key = f"failures:{platform}:{datetime.utcnow().strftime('%Y-%m-%d')}"
            failure_data = {
                "payment_intent_id": payment_intent.id,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "error": payment_intent.last_payment_error,
                "timestamp": datetime.utcnow().isoformat()
            }

            redis_client.lpush(failure_key, json.dumps(failure_data))
            redis_client.ltrim(failure_key, 0, 999)  # Keep last 1000 failures
            redis_client.expire(failure_key, 2592000)  # 30 days

        except Exception as e:
            logger.error(f"Failed to log payment failure: {e}")

    async def _alert_administrators(self, alert_type: str, data: Dict[str, Any]):
        """Send alerts to administrators"""
        try:
            # In a real implementation, this would send emails/SMS/webhooks
            alert_key = f"alerts:{alert_type}:{datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')}"
            redis_client.setex(alert_key, 86400, json.dumps(data))  # 24 hours

            logger.warning(f"Administrator alert created: {alert_type}")

        except Exception as e:
            logger.error(f"Failed to create administrator alert: {e}")

# Initialize webhook processor
webhook_processor = WebhookProcessor()

@app.post("/webhooks/{platform}")
async def handle_webhook(
    platform: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Unified webhook endpoint for all platforms

    Platforms: pinnacle_ai, free_ecommerce
    """
    if platform not in ['pinnacle_ai', 'free_ecommerce']:
        raise HTTPException(status_code=400, detail="Invalid platform")

    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get('stripe-signature')

    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    # Process webhook in background
    background_tasks.add_task(webhook_processor.process_webhook, platform, body, signature)

    # Return immediately to Stripe
    return {"status": "accepted"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "redis": "connected",
                "stripe": "configured" if stripe.api_key else "not_configured",
                "retry_engine": "active"
            }
        }

    def _extract_failure_reason(self, payment_intent: Dict[str, Any]) -> str:
        """Extract failure reason from payment intent"""
        last_payment_error = payment_intent.get('last_payment_error', {})
        decline_code = last_payment_error.get('decline_code', 'unknown')
        return decline_code

    def _is_retryable_failure(self, failure_reason: str) -> bool:
        """Determine if a failure reason should trigger retry"""
        non_retryable = [
            'card_not_supported', 'currency_not_supported', 'duplicate_transaction',
            'expired_card', 'incorrect_cvc', 'incorrect_number', 'invalid_card_type',
            'invalid_cvc', 'invalid_expiry_month', 'invalid_expiry_year',
            'invalid_number', 'lost_card', 'stolen_card'
        ]
        return failure_reason not in non_retryable

    async def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return await retry_engine.get_retry_stats()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/analytics/{platform}")
async def get_payment_analytics(platform: str, days: int = 30):
    """Get payment analytics for a platform"""
    try:
        analytics = {}
        current_date = datetime.utcnow()

        for i in range(days):
            date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
            key = f"analytics:{platform}:payments:{date}"

            data = redis_client.hgetall(key)
            if data:
                analytics[date] = {
                    "total_payments": int(data.get("total_payments", 0)),
                    "amount_usd": int(data.get("amount_usd", 0)) / 100,  # Convert cents to dollars
                    "amount_eur": int(data.get("amount_eur", 0)) / 100,
                }

        return {
            "platform": platform,
            "period_days": days,
            "analytics": analytics
        }

    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail="Analytics retrieval failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))