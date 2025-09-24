"""
Tests for Stripe payment integration
"""

import pytest
from unittest.mock import patch, MagicMock
from src.core.payments.stripe_integration import StripeIntegration, PaymentIntentRequest, SubscriptionRequest


class TestStripeIntegration:
    """Test Stripe payment integration"""

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_success(self, mock_create):
        """Test successful payment intent creation"""
        # Mock Stripe response
        mock_payment_intent = MagicMock()
        mock_payment_intent.client_secret = "pi_test_secret"
        mock_payment_intent.id = "pi_test_id"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "requires_payment_method"
        mock_create.return_value = mock_payment_intent

        # Create request
        request = PaymentIntentRequest(
            amount=1000,
            currency="usd",
            description="Test payment"
        )

        # Call function
        result = pytest.asyncio.run(StripeIntegration.create_payment_intent(request))

        # Assertions
        assert result["client_secret"] == "pi_test_secret"
        assert result["payment_intent_id"] == "pi_test_id"
        assert result["amount"] == 1000
        assert result["currency"] == "usd"
        assert result["status"] == "requires_payment_method"

        # Verify Stripe was called correctly
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert call_args["amount"] == 1000
        assert call_args["currency"] == "usd"
        assert call_args["automatic_payment_methods"]["enabled"] is True

    @patch('stripe.PaymentIntent.create')
    def test_create_payment_intent_with_customer(self, mock_create):
        """Test payment intent creation with customer"""
        mock_payment_intent = MagicMock()
        mock_payment_intent.client_secret = "pi_test_secret"
        mock_payment_intent.id = "pi_test_id"
        mock_payment_intent.amount = 2000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "requires_payment_method"
        mock_create.return_value = mock_payment_intent

        request = PaymentIntentRequest(
            amount=2000,
            currency="usd",
            customer_id="cus_test_customer"
        )

        result = pytest.asyncio.run(StripeIntegration.create_payment_intent(request))

        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert call_args["customer"] == "cus_test_customer"

    @patch('stripe.Subscription.create')
    def test_create_subscription_success(self, mock_create):
        """Test successful subscription creation"""
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test_id"
        mock_subscription.status = "incomplete"
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643673600

        mock_invoice = MagicMock()
        mock_invoice.payment_intent = MagicMock()
        mock_invoice.payment_intent.client_secret = "pi_test_secret"
        mock_subscription.latest_invoice = mock_invoice

        mock_create.return_value = mock_subscription

        request = SubscriptionRequest(
            customer_id="cus_test_customer",
            price_id="price_test_price"
        )

        result = pytest.asyncio.run(StripeIntegration.create_subscription(request))

        assert result["subscription_id"] == "sub_test_id"
        assert result["client_secret"] == "pi_test_secret"
        assert result["status"] == "incomplete"

    @patch('stripe.Customer.create')
    def test_create_customer_success(self, mock_create):
        """Test successful customer creation"""
        mock_customer = MagicMock()
        mock_customer.id = "cus_test_id"
        mock_customer.email = "test@example.com"
        mock_customer.name = "Test User"
        mock_customer.metadata = {"user_id": "123"}
        mock_create.return_value = mock_customer

        result = pytest.asyncio.run(StripeIntegration.create_customer(
            email="test@example.com",
            name="Test User",
            metadata={"user_id": "123"}
        ))

        assert result["customer_id"] == "cus_test_id"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"

    @patch('stripe.PaymentIntent.retrieve')
    def test_retrieve_payment_intent(self, mock_retrieve):
        """Test payment intent retrieval"""
        mock_payment_intent = MagicMock()
        mock_payment_intent.id = "pi_test_id"
        mock_payment_intent.amount = 1000
        mock_payment_intent.currency = "usd"
        mock_payment_intent.status = "succeeded"
        mock_payment_intent.client_secret = "pi_test_secret"
        mock_payment_intent.metadata = {"order_id": "123"}
        mock_retrieve.return_value = mock_payment_intent

        result = pytest.asyncio.run(StripeIntegration.retrieve_payment_intent("pi_test_id"))

        assert result["id"] == "pi_test_id"
        assert result["amount"] == 1000
        assert result["status"] == "succeeded"

    @patch('stripe.Refund.create')
    def test_process_refund(self, mock_create):
        """Test refund processing"""
        mock_refund = MagicMock()
        mock_refund.id = "rf_test_id"
        mock_refund.amount = 1000
        mock_refund.currency = "usd"
        mock_refund.status = "succeeded"
        mock_refund.reason = "requested_by_customer"
        mock_create.return_value = mock_refund

        result = pytest.asyncio.run(StripeIntegration.process_refund(
            payment_intent_id="pi_test_id",
            amount=1000,
            reason="requested_by_customer"
        ))

        assert result["refund_id"] == "rf_test_id"
        assert result["amount"] == 1000
        assert result["status"] == "succeeded"

    @patch('stripe.Webhook.construct_event')
    def test_webhook_processing_success(self, mock_construct):
        """Test successful webhook processing"""
        mock_event = MagicMock()
        mock_event.type = "payment_intent.succeeded"
        mock_event.data.object = MagicMock()
        mock_event.id = "evt_test_id"
        mock_construct.return_value = mock_event

        payload = b'{"type": "payment_intent.succeeded"}'
        signature = "t=123,v1=test_signature"

        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()

        result = pytest.asyncio.run(StripeIntegration.handle_webhook(
            payload, signature, background_tasks
        ))

        assert result["status"] == "processed"
        assert result["event_type"] == "payment_intent.succeeded"
        assert result["event_id"] == "evt_test_id"

    @patch('stripe.Webhook.construct_event')
    def test_webhook_signature_verification_failure(self, mock_construct):
        """Test webhook signature verification failure"""
        from stripe import SignatureVerificationError
        mock_construct.side_effect = SignatureVerificationError("Invalid signature", None)

        payload = b'{"type": "payment_intent.succeeded"}'
        signature = "invalid_signature"

        from fastapi import BackgroundTasks, HTTPException
        background_tasks = BackgroundTasks()

        with pytest.raises(HTTPException) as exc_info:
            pytest.asyncio.run(StripeIntegration.handle_webhook(
                payload, signature, background_tasks
            ))

        assert exc_info.value.status_code == 400
        assert "Invalid webhook signature" in str(exc_info.value.detail)