"""
Stripe Payment Integration for Pinnacle AI Platform
Handles payment processing, subscriptions, and webhooks
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import stripe
from fastapi import HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class PaymentIntentRequest(BaseModel):
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd", description="Currency code")
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    description: Optional[str] = None

class SubscriptionRequest(BaseModel):
    customer_id: str
    price_id: str
    metadata: Optional[Dict[str, str]] = None

class PaymentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str

class StripeIntegration:
    """Main Stripe integration class"""

    @staticmethod
    async def create_payment_intent(request: PaymentIntentRequest) -> PaymentResponse:
        """Create a Stripe PaymentIntent for one-time payments"""
        try:
            intent_data = {
                'amount': request.amount,
                'currency': request.currency,
                'automatic_payment_methods': {'enabled': True},
                'metadata': request.metadata or {}
            }

            if request.customer_id:
                intent_data['customer'] = request.customer_id

            if request.description:
                intent_data['description'] = request.description

            payment_intent = stripe.PaymentIntent.create(**intent_data)

            return PaymentResponse(
                client_secret=payment_intent.client_secret,
                payment_intent_id=payment_intent.id,
                amount=payment_intent.amount,
                currency=payment_intent.currency,
                status=payment_intent.status
            )

        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment intent creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def create_subscription(request: SubscriptionRequest) -> Dict[str, Any]:
        """Create a subscription for recurring payments"""
        try:
            subscription = stripe.Subscription.create(
                customer=request.customer_id,
                items=[{'price': request.price_id}],
                metadata=request.metadata or {},
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )

            return {
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'metadata': subscription.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def create_customer(email: str, name: Optional[str] = None, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a Stripe customer"""
        try:
            customer_data = {
                'email': email,
                'metadata': metadata or {}
            }

            if name:
                customer_data['name'] = name

            customer = stripe.Customer.create(**customer_data)

            return {
                'customer_id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'metadata': customer.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
        """Retrieve payment intent details"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                'id': payment_intent.id,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status,
                'client_secret': payment_intent.client_secret,
                'metadata': payment_intent.metadata
            }

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve payment intent {payment_intent_id}: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def process_refund(payment_intent_id: str, amount: Optional[int] = None, reason: str = "requested_by_customer") -> Dict[str, Any]:
        """Process a refund for a payment"""
        try:
            refund_data = {
                'payment_intent': payment_intent_id,
                'reason': reason
            }

            if amount:
                refund_data['amount'] = amount

            refund = stripe.Refund.create(**refund_data)

            return {
                'refund_id': refund.id,
                'amount': refund.amount,
                'currency': refund.currency,
                'status': refund.status,
                'reason': refund.reason
            }

        except stripe.error.StripeError as e:
            logger.error(f"Refund processing failed for {payment_intent_id}: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    async def handle_webhook(payload: bytes, signature: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Process Stripe webhooks"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, stripe_webhook_secret
            )

            # Handle different event types
            event_handlers = {
                'payment_intent.succeeded': StripeIntegration._handle_payment_success,
                'payment_intent.payment_failed': StripeIntegration._handle_payment_failure,
                'customer.subscription.created': StripeIntegration._handle_subscription_created,
                'customer.subscription.updated': StripeIntegration._handle_subscription_updated,
                'customer.subscription.deleted': StripeIntegration._handle_subscription_cancelled,
                'invoice.payment_succeeded': StripeIntegration._handle_invoice_payment_succeeded,
                'invoice.payment_failed': StripeIntegration._handle_invoice_payment_failed,
            }

            handler = event_handlers.get(event.type)
            if handler:
                # Process webhook in background to avoid timeouts
                background_tasks.add_task(handler, event.data.object)
                logger.info(f"Queued webhook processing for event: {event.type}")
            else:
                logger.warning(f"Unhandled webhook event type: {event.type}")

            return {
                'status': 'processed',
                'event_type': event.type,
                'event_id': event.id
            }

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=400, detail="Webhook processing failed")

    @staticmethod
    async def _handle_payment_success(payment_intent):
        """Handle successful payment"""
        logger.info(f"Payment succeeded: {payment_intent.id}")

        # TODO: Update database with payment success
        # TODO: Send confirmation email
        # TODO: Update user credits/subscription status
        # TODO: Trigger any post-payment actions

    @staticmethod
    async def _handle_payment_failure(payment_intent):
        """Handle failed payment"""
        logger.warning(f"Payment failed: {payment_intent.id}")

        # TODO: Update database with payment failure
        # TODO: Send failure notification
        # TODO: Log failure reasons for analysis

    @staticmethod
    async def _handle_subscription_created(subscription):
        """Handle new subscription"""
        logger.info(f"Subscription created: {subscription.id}")

        # TODO: Update user subscription status
        # TODO: Grant access to paid features
        # TODO: Send welcome email

    @staticmethod
    async def _handle_subscription_updated(subscription):
        """Handle subscription updates"""
        logger.info(f"Subscription updated: {subscription.id}")

        # TODO: Update subscription details in database
        # TODO: Handle plan changes
        # TODO: Update user permissions

    @staticmethod
    async def _handle_subscription_cancelled(subscription):
        """Handle subscription cancellation"""
        logger.info(f"Subscription cancelled: {subscription.id}")

        # TODO: Update subscription status
        # TODO: Revoke premium features
        # TODO: Send cancellation confirmation

    @staticmethod
    async def _handle_invoice_payment_succeeded(invoice):
        """Handle successful subscription payment"""
        logger.info(f"Invoice payment succeeded: {invoice.id}")

        # TODO: Update payment records
        # TODO: Extend subscription period

    @staticmethod
    async def _handle_invoice_payment_failed(invoice):
        """Handle failed subscription payment"""
        logger.warning(f"Invoice payment failed: {invoice.id}")

        # TODO: Handle failed subscription payment
        # TODO: Send payment failure notification
        # TODO: Update subscription status