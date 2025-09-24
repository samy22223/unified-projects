"""
Payment API endpoints for Stripe integration
"""

from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException
from typing import Dict, Any
from src.core.payments.stripe_integration import (
    StripeIntegration,
    PaymentIntentRequest,
    SubscriptionRequest
)

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/create-payment-intent", response_model=Dict[str, Any])
async def create_payment_intent(request: PaymentIntentRequest):
    """
    Create a Stripe PaymentIntent for one-time payments

    This endpoint creates a secure payment intent that can be used
    with Stripe Elements on the frontend.
    """
    return await StripeIntegration.create_payment_intent(request)

@router.post("/create-subscription", response_model=Dict[str, Any])
async def create_subscription(request: SubscriptionRequest):
    """
    Create a Stripe subscription for recurring payments

    This endpoint creates a subscription with automatic billing
    for recurring services like AI platform access.
    """
    return await StripeIntegration.create_subscription(request)

@router.post("/create-customer", response_model=Dict[str, Any])
async def create_customer(
    email: str,
    name: str = None,
    metadata: Dict[str, str] = None
):
    """
    Create a Stripe customer

    Creates a customer record in Stripe for tracking payments
    and managing subscriptions.
    """
    return await StripeIntegration.create_customer(email, name, metadata)

@router.get("/payment-intent/{payment_intent_id}", response_model=Dict[str, Any])
async def get_payment_intent(payment_intent_id: str):
    """
    Retrieve payment intent details

    Get the current status and details of a payment intent.
    """
    return await StripeIntegration.retrieve_payment_intent(payment_intent_id)

@router.post("/refund", response_model=Dict[str, Any])
async def process_refund(
    payment_intent_id: str,
    amount: int = None,
    reason: str = "requested_by_customer"
):
    """
    Process a refund for a payment

    Refund a payment partially or fully with specified reason.
    """
    return await StripeIntegration.process_refund(payment_intent_id, amount, reason)

@router.post("/webhooks")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Stripe webhooks

    This endpoint receives webhook events from Stripe for payment
    status updates, subscription changes, etc.
    """
    # Get the raw body
    body = await request.body()

    # Get the Stripe signature from headers
    signature = request.headers.get('stripe-signature')
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    return await StripeIntegration.handle_webhook(body, signature, background_tasks)

# AI Platform specific payment endpoints
@router.post("/ai-service-payment", response_model=Dict[str, Any])
async def create_ai_service_payment(
    service_type: str,  # 'basic', 'pro', 'enterprise'
    billing_period: str = "month",  # 'month' or 'year'
    user_id: str = None
):
    """
    Create payment for AI platform services

    Convenience endpoint for AI service payments with predefined pricing.
    """
    # Define pricing (these would come from environment variables or database)
    pricing = {
        'basic': {
            'month': 999,  # $9.99
            'year': 9999   # $99.99
        },
        'pro': {
            'month': 2999,  # $29.99
            'year': 29999   # $299.99
        },
        'enterprise': {
            'month': 9999,  # $99.99
            'year': 99999   # $999.99
        }
    }

    if service_type not in pricing:
        raise HTTPException(status_code=400, detail="Invalid service type")

    if billing_period not in ['month', 'year']:
        raise HTTPException(status_code=400, detail="Invalid billing period")

    amount = pricing[service_type][billing_period]

    payment_request = PaymentIntentRequest(
        amount=amount,
        currency="usd",
        metadata={
            "service_type": service_type,
            "billing_period": billing_period,
            "user_id": user_id,
            "product": f"AI Platform {service_type.title()} ({billing_period})"
        },
        description=f"AI Platform {service_type.title()} - {billing_period}ly subscription"
    )

    return await StripeIntegration.create_payment_intent(payment_request)

@router.post("/ai-service-subscription", response_model=Dict[str, Any])
async def create_ai_service_subscription(
    service_type: str,  # 'basic', 'pro', 'enterprise'
    billing_period: str = "month",  # 'month' or 'year'
    customer_id: str = None,
    user_id: str = None
):
    """
    Create subscription for AI platform services

    Creates a recurring subscription for AI platform access.
    """
    # Price IDs would be configured in Stripe dashboard
    price_ids = {
        'basic': {
            'month': "price_basic_monthly",  # Replace with actual Stripe price IDs
            'year': "price_basic_yearly"
        },
        'pro': {
            'month': "price_pro_monthly",
            'year': "price_pro_yearly"
        },
        'enterprise': {
            'month': "price_enterprise_monthly",
            'year': "price_enterprise_yearly"
        }
    }

    if not customer_id:
        raise HTTPException(status_code=400, detail="Customer ID required for subscriptions")

    if service_type not in price_ids:
        raise HTTPException(status_code=400, detail="Invalid service type")

    if billing_period not in ['month', 'year']:
        raise HTTPException(status_code=400, detail="Invalid billing period")

    price_id = price_ids[service_type][billing_period]

    subscription_request = SubscriptionRequest(
        customer_id=customer_id,
        price_id=price_id,
        metadata={
            "service_type": service_type,
            "billing_period": billing_period,
            "user_id": user_id,
            "platform": "ai_platform"
        }
    )

    return await StripeIntegration.create_subscription(subscription_request)