# Stripe Payment Integration Plan for Unified Projects

## Overview

This document outlines the comprehensive Stripe payment integration strategy for the unified projects monorepo, covering both the **Free E-commerce Store** (WordPress/WooCommerce) and **Pinnacle AI Platform** (Python/FastAPI).

## Current Status

### Free E-commerce Store (WordPress/WooCommerce)
- **Current State**: Uses free infrastructure (InfinityFree hosting)
- **Payment Gap**: No payment processing capability
- **Requirements**: Basic e-commerce payment processing
- **Integration Method**: WooCommerce Stripe Payment Gateway plugin

### Pinnacle AI Platform (Python/FastAPI)
- **Current State**: Has Stripe configuration in environment variables
- **Payment Gap**: No implementation of payment processing
- **Requirements**: Advanced payment features, subscriptions, AI service payments
- **Integration Method**: Direct Stripe API integration with FastAPI

## Integration Architecture

### 1. Unified Payment Service Layer

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│  API Gateway     │────│ Payment Service │
│   (React/Vue)   │    │  (FastAPI/NGINX) │    │   (Stripe API)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │  Webhook Handler    │
                    │  (Event Processing) │
                    └─────────────────────┘
```

### 2. Payment Features Matrix

| Feature | Free E-commerce Store | Pinnacle AI Platform | Priority |
|---------|----------------------|---------------------|----------|
| One-time Payments | ✅ | ✅ | High |
| Subscription Management | ❌ | ✅ | High |
| Payment Intents | ✅ | ✅ | High |
| Webhooks | ✅ | ✅ | High |
| Refunds | ✅ | ✅ | Medium |
| Multi-currency | ❌ | ✅ | Medium |
| Payment Analytics | ❌ | ✅ | Medium |
| Fraud Prevention | ✅ | ✅ | High |
| PCI Compliance | ✅ | ✅ | High |

## Implementation Phases

### Phase 1: Core Payment Processing (Week 1-2)

#### 1.1 Free E-commerce Store Integration
```php
// wp-content/plugins/stripe-integration/stripe-integration.php
<?php
/*
Plugin Name: Stripe Payment Integration
Description: Custom Stripe payment processing for dropshipping store
Version: 1.0.0
*/

// Stripe PHP SDK integration
require_once plugin_dir_path(__FILE__) . 'vendor/autoload.php';

class StripeIntegration {
    private $stripe_secret_key;
    private $webhook_secret;

    public function __construct() {
        $this->stripe_secret_key = get_option('stripe_secret_key');
        $this->webhook_secret = get_option('stripe_webhook_secret');

        \Stripe\Stripe::setApiKey($this->stripe_secret_key);

        add_action('woocommerce_checkout_process', array($this, 'process_stripe_payment'));
        add_action('woocommerce_api_stripe_webhook', array($this, 'handle_webhook'));
    }

    public function process_stripe_payment() {
        // Payment processing logic
        try {
            $payment_intent = \Stripe\PaymentIntent::create([
                'amount' => WC()->cart->get_total() * 100,
                'currency' => get_woocommerce_currency(),
                'metadata' => [
                    'order_id' => $order_id,
                    'customer_email' => $customer_email
                ]
            ]);

            // Store payment intent ID in session
            WC()->session->set('stripe_payment_intent', $payment_intent->id);

        } catch (\Stripe\Exception\ApiErrorException $e) {
            wc_add_notice('Payment failed: ' . $e->getMessage(), 'error');
        }
    }

    public function handle_webhook() {
        $payload = @file_get_contents('php://input');
        $sig_header = $_SERVER['HTTP_STRIPE_SIGNATURE'];

        try {
            $event = \Stripe\Webhook::constructEvent(
                $payload, $sig_header, $this->webhook_secret
            );

            switch ($event->type) {
                case 'payment_intent.succeeded':
                    $this->handle_payment_success($event->data->object);
                    break;
                case 'payment_intent.payment_failed':
                    $this->handle_payment_failure($event->data->object);
                    break;
            }

            http_response_code(200);

        } catch (\UnexpectedValueException $e) {
            http_response_code(400);
            exit();
        }
    }
}
```

#### 1.2 Pinnacle AI Platform Integration

**File Structure:**
```
pinnacle-ai-platform/src/core/payments/
├── __init__.py
├── stripe_integration.py
├── models.py
├── webhooks.py
└── subscriptions.py
```

**Core Integration:**
```python
# src/core/payments/stripe_integration.py
import stripe
from fastapi import HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class StripePaymentService:
    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe PaymentIntent"""
        try:
            intent_data = {
                'amount': amount,
                'currency': currency,
                'automatic_payment_methods': {'enabled': True},
                'metadata': metadata or {}
            }

            if customer_id:
                intent_data['customer'] = customer_id

            payment_intent = stripe.PaymentIntent.create(**intent_data)

            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'status': payment_intent.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe payment intent creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a subscription for recurring payments"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                metadata=metadata or {},
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )

            return {
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe subscription creation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Stripe webhooks"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            # Handle different event types
            event_handlers = {
                'payment_intent.succeeded': self._handle_payment_success,
                'payment_intent.payment_failed': self._handle_payment_failure,
                'customer.subscription.created': self._handle_subscription_created,
                'customer.subscription.updated': self._handle_subscription_updated,
                'customer.subscription.deleted': self._handle_subscription_cancelled,
            }

            handler = event_handlers.get(event.type)
            if handler:
                await handler(event.data.object)

            return {'status': 'processed', 'event_type': event.type}

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=400, detail="Webhook processing failed")

    async def _handle_payment_success(self, payment_intent):
        """Handle successful payment"""
        logger.info(f"Payment succeeded: {payment_intent.id}")
        # Update order status, send confirmation emails, etc.

    async def _handle_payment_failure(self, payment_intent):
        """Handle failed payment"""
        logger.warning(f"Payment failed: {payment_intent.id}")
        # Handle payment failure logic

    async def _handle_subscription_created(self, subscription):
        """Handle new subscription"""
        logger.info(f"Subscription created: {subscription.id}")
        # Activate user subscription, update database

    async def _handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        logger.info(f"Subscription updated: {subscription.id}")
        # Update subscription status, handle plan changes

    async def _handle_subscription_cancelled(self, subscription):
        """Handle subscription cancellation"""
        logger.info(f"Subscription cancelled: {subscription.id}")
        # Deactivate subscription, update user access
```

### Phase 2: Advanced Features (Week 3-4)

#### 2.1 Subscription Management
```python
# src/core/payments/subscriptions.py
class SubscriptionManager:
    def __init__(self, stripe_service: StripePaymentService):
        self.stripe = stripe_service

    async def create_ai_service_subscription(
        self,
        user_id: str,
        plan_type: str,  # 'basic', 'pro', 'enterprise'
        billing_cycle: str = 'month'  # 'month' or 'year'
    ):
        """Create subscription for AI services"""

        price_ids = {
            'basic': {
                'month': os.getenv('STRIPE_PRICE_BASIC_MONTHLY'),
                'year': os.getenv('STRIPE_PRICE_BASIC_YEARLY')
            },
            'pro': {
                'month': os.getenv('STRIPE_PRICE_PRO_MONTHLY'),
                'year': os.getenv('STRIPE_PRICE_PRO_YEARLY')
            },
            'enterprise': {
                'month': os.getenv('STRIPE_PRICE_ENTERPRISE_MONTHLY'),
                'year': os.getenv('STRIPE_PRICE_ENTERPRISE_YEARLY')
            }
        }

        price_id = price_ids.get(plan_type, {}).get(billing_cycle)
        if not price_id:
            raise HTTPException(status_code=400, detail="Invalid plan or billing cycle")

        # Create or get Stripe customer
        customer = await self._get_or_create_customer(user_id)

        return await self.stripe.create_subscription(
            customer_id=customer.id,
            price_id=price_id,
            metadata={'user_id': user_id, 'plan_type': plan_type}
        )
```

#### 2.2 Fraud Prevention & Security
```python
# src/core/payments/security.py
class PaymentSecurity:
    def __init__(self):
        self.radar_enabled = os.getenv('STRIPE_RADAR_ENABLED', 'true').lower() == 'true'

    async def assess_payment_risk(self, payment_intent_id: str) -> Dict[str, Any]:
        """Assess payment risk using Stripe Radar"""
        if not self.radar_enabled:
            return {'risk_score': 0, 'risk_level': 'low'}

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            charges = payment_intent.charges.data

            if charges:
                charge = charges[0]
                return {
                    'risk_score': charge.outcome.risk_score,
                    'risk_level': charge.outcome.risk_level,
                    'rule': getattr(charge.outcome, 'rule', None)
                }

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")

        return {'risk_score': 0, 'risk_level': 'unknown'}

    async def flag_suspicious_activity(self, user_id: str, activity: str):
        """Flag suspicious payment activity"""
        logger.warning(f"Suspicious activity flagged for user {user_id}: {activity}")
        # Implement additional security measures
        # - Send alerts to administrators
        # - Temporarily block payments
        # - Request additional verification
```

### Phase 3: Analytics & Compliance (Week 5-6)

#### 3.1 Payment Analytics Dashboard
```python
# src/core/payments/analytics.py
class PaymentAnalytics:
    def __init__(self, db_session):
        self.db = db_session

    async def get_payment_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        group_by: str = 'day'
    ) -> Dict[str, Any]:
        """Generate payment analytics"""

        # Revenue metrics
        revenue_query = """
        SELECT
            DATE_TRUNC(%s, created_at) as period,
            COUNT(*) as transaction_count,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_transaction_value
        FROM payments
        WHERE created_at BETWEEN %s AND %s
            AND status = 'succeeded'
        GROUP BY period
        ORDER BY period
        """

        # Subscription metrics
        subscription_query = """
        SELECT
            status,
            COUNT(*) as count
        FROM subscriptions
        WHERE created_at BETWEEN %s AND %s
        GROUP BY status
        """

        # Churn analysis
        churn_query = """
        SELECT
            COUNT(*) as cancelled_subscriptions
        FROM subscription_events
        WHERE event_type = 'cancelled'
            AND created_at BETWEEN %s AND %s
        """

        return {
            'revenue': await self.db.execute(revenue_query, (group_by, start_date, end_date)),
            'subscriptions': await self.db.execute(subscription_query, (start_date, end_date)),
            'churn': await self.db.execute(churn_query, (start_date, end_date))
        }
```

#### 3.2 Compliance & Data Protection
```python
# src/core/payments/compliance.py
class PaymentCompliance:
    def __init__(self):
        self.gdpr_enabled = True
        self.pci_compliant = True

    async def handle_data_deletion_request(self, user_id: str):
        """Handle GDPR right to erasure for payment data"""
        try:
            # Anonymize payment data instead of deleting
            await self.db.execute("""
                UPDATE payments
                SET customer_email = CONCAT('deleted_', id, '@anonymized.com'),
                    metadata = jsonb_set(metadata, '{gdpr_deleted}', 'true')
                WHERE user_id = %s
            """, (user_id,))

            # Cancel any active subscriptions
            await self.cancel_user_subscriptions(user_id)

            logger.info(f"GDPR data deletion completed for user {user_id}")

        except Exception as e:
            logger.error(f"GDPR deletion failed for user {user_id}: {e}")
            raise

    async def generate_pci_compliance_report(self) -> Dict[str, Any]:
        """Generate PCI DSS compliance report"""
        return {
            'pci_version': '3.2.1',
            'compliance_status': 'compliant',
            'last_assessment': datetime.utcnow(),
            'encryption_enabled': True,
            'tokenization_enabled': True,
            'audit_trail_enabled': True
        }

    async def export_payment_data_for_audit(self, start_date: datetime, end_date: datetime):
        """Export payment data for regulatory audits"""
        # Implement secure data export for compliance
        pass
```

## Configuration Requirements

### Environment Variables

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Subscription Pricing
STRIPE_PRICE_BASIC_MONTHLY=price_...
STRIPE_PRICE_BASIC_YEARLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_PRO_YEARLY=price_...
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...
STRIPE_PRICE_ENTERPRISE_YEARLY=price_...

# Security & Compliance
STRIPE_RADAR_ENABLED=true
PAYMENT_RETENTION_DAYS=2555  # 7 years for PCI compliance
GDPR_COMPLIANCE_ENABLED=true

# Webhook Configuration
WEBHOOK_RETRY_ATTEMPTS=3
WEBHOOK_TIMEOUT_SECONDS=30
```

## Testing Strategy

### Unit Tests
```python
# tests/test_payments.py
import pytest
from unittest.mock import patch, MagicMock
from src.core.payments.stripe_integration import StripePaymentService

class TestStripeIntegration:
    @patch('stripe.PaymentIntent.create')
    async def test_create_payment_intent_success(self, mock_create):
        # Test successful payment intent creation
        pass

    @patch('stripe.PaymentIntent.create')
    async def test_create_payment_intent_failure(self, mock_create):
        # Test payment intent creation failure
        pass

    async def test_webhook_signature_verification(self):
        # Test webhook signature validation
        pass
```

### Integration Tests
```python
# tests/integration/test_payment_flow.py
async def test_complete_payment_flow(client, db_session):
    """Test complete payment flow from creation to completion"""
    # 1. Create payment intent
    # 2. Simulate webhook
    # 3. Verify database updates
    # 4. Check user notifications
    pass
```

## Deployment Considerations

### 1. Webhook Security
- Use Stripe CLI for local webhook testing: `stripe listen --forward-to localhost:8000/webhooks`
- Implement webhook signature verification
- Handle webhook idempotency

### 2. Database Migrations
```sql
-- Create payments table
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    user_id INTEGER REFERENCES users(id),
    amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create subscriptions table
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Monitoring & Alerting
- Set up Stripe webhooks for payment failures
- Monitor payment success rates
- Alert on unusual payment patterns
- Track subscription churn rates

## Success Metrics

### Business Metrics
- **Conversion Rate**: Payment completion rate
- **Churn Rate**: Subscription cancellation rate
- **Revenue per User**: Average revenue metrics
- **Payment Failure Rate**: Technical reliability

### Technical Metrics
- **Webhook Processing Time**: < 5 seconds
- **Payment Success Rate**: > 95%
- **System Uptime**: > 99.9%
- **False Positive Rate**: < 1% (fraud detection)

## Risk Mitigation

### 1. Payment Security
- Implement 3D Secure for high-risk transactions
- Use Stripe Radar for fraud prevention
- Regular security audits and penetration testing

### 2. Business Continuity
- Implement payment retry logic
- Set up payment failure notifications
- Maintain payment processing during outages

### 3. Compliance
- Regular PCI DSS assessments
- GDPR compliance for EU customers
- Data encryption at rest and in transit

## Next Steps

1. **Immediate Actions**:
   - Complete Stripe account setup and API key configuration
   - Implement basic payment processing for both platforms
   - Set up webhook endpoints and handlers

2. **Week 1-2**: Core payment processing
3. **Week 3-4**: Subscription management and advanced features
4. **Week 5-6**: Analytics, compliance, and optimization

This integration will transform both e-commerce platforms into fully functional, payment-enabled systems capable of processing transactions, managing subscriptions, and providing enterprise-grade payment analytics.