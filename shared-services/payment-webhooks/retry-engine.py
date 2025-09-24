"""
Payment Retry Engine
Intelligent retry logic for failed payment processing with exponential backoff
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import redis
import aiohttp
import stripe
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetryAttempt:
    """Retry attempt data structure"""
    payment_intent_id: str
    attempt_number: int
    max_attempts: int
    last_attempt_at: datetime
    next_attempt_at: datetime
    failure_reason: str
    retry_strategy: str
    platform: str
    metadata: Dict[str, Any]

@dataclass
class RetryResult:
    """Result of a retry attempt"""
    success: bool
    payment_intent_id: str
    attempt_number: int
    response: Optional[Dict[str, Any]]
    error: Optional[str]
    should_retry: bool
    next_retry_at: Optional[datetime]

class PaymentRetryEngine:
    """Intelligent payment retry engine with multiple strategies"""

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

        # Retry configuration
        self.retry_strategies = {
            'exponential_backoff': self._exponential_backoff,
            'fixed_interval': self._fixed_interval,
            'immediate_retry': self._immediate_retry,
            'smart_retry': self._smart_retry
        }

        # Default retry limits
        self.max_attempts = {
            'card_declined': 3,
            'insufficient_funds': 2,
            'network_error': 5,
            'processing_error': 3,
            'authentication_required': 2,
            'generic_decline': 1
        }

        # Failure reason mapping
        self.failure_mapping = {
            'card_declined': 'card_declined',
            'insufficient_funds': 'insufficient_funds',
            'generic_decline': 'generic_decline',
            'processing_error': 'processing_error',
            'issuer_not_available': 'network_error',
            'network_timeout': 'network_error',
            'authentication_required': 'authentication_required'
        }

    async def schedule_retry(
        self,
        payment_intent_id: str,
        failure_reason: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Schedule a payment for retry based on failure reason"""
        try:
            # Map failure reason to retry category
            retry_category = self.failure_mapping.get(failure_reason, 'generic_decline')
            max_attempts = self.max_attempts.get(retry_category, 1)

            # Check if payment is already scheduled for retry
            existing_retry = await self._get_retry_attempt(payment_intent_id)
            if existing_retry:
                if existing_retry.attempt_number >= max_attempts:
                    logger.info(f"Payment {payment_intent_id} has reached max retry attempts")
                    return False
            else:
                # Create new retry attempt
                existing_retry = RetryAttempt(
                    payment_intent_id=payment_intent_id,
                    attempt_number=0,
                    max_attempts=max_attempts,
                    last_attempt_at=datetime.utcnow(),
                    next_attempt_at=datetime.utcnow(),  # Immediate first retry
                    failure_reason=failure_reason,
                    retry_strategy=self._select_retry_strategy(retry_category),
                    platform=platform,
                    metadata=metadata or {}
                )

            # Calculate next retry time
            next_attempt_at = await self._calculate_next_retry_time(
                existing_retry.retry_strategy,
                existing_retry.attempt_number
            )

            existing_retry.next_attempt_at = next_attempt_at
            existing_retry.attempt_number += 1

            # Store retry attempt
            await self._store_retry_attempt(existing_retry)

            # Schedule the retry
            await self._schedule_retry_task(existing_retry)

            logger.info(f"Scheduled retry {existing_retry.attempt_number}/{max_attempts} for payment {payment_intent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule retry for {payment_intent_id}: {e}")
            return False

    async def process_retry_queue(self):
        """Process queued payment retries"""
        while True:
            try:
                # Get payments ready for retry
                retry_keys = self.redis.zrangebyscore(
                    'retry_queue',
                    0,
                    datetime.utcnow().timestamp(),
                    start=0,
                    num=10  # Process up to 10 at a time
                )

                for retry_key in retry_keys:
                    try:
                        # Get retry attempt data
                        retry_data = self.redis.hgetall(f"retry:{retry_key}")
                        if not retry_data:
                            continue

                        retry_attempt = RetryAttempt(
                            payment_intent_id=retry_data['payment_intent_id'],
                            attempt_number=int(retry_data['attempt_number']),
                            max_attempts=int(retry_data['max_attempts']),
                            last_attempt_at=datetime.fromisoformat(retry_data['last_attempt_at']),
                            next_attempt_at=datetime.fromisoformat(retry_data['next_attempt_at']),
                            failure_reason=retry_data['failure_reason'],
                            retry_strategy=retry_data['retry_strategy'],
                            platform=retry_data['platform'],
                            metadata=json.loads(retry_data.get('metadata', '{}'))
                        )

                        # Attempt the retry
                        result = await self._attempt_payment_retry(retry_attempt)

                        if result.success:
                            # Payment succeeded - remove from retry queue
                            await self._remove_retry_attempt(retry_attempt.payment_intent_id)
                            logger.info(f"Payment {retry_attempt.payment_intent_id} succeeded on retry {retry_attempt.attempt_number}")
                        elif result.should_retry and retry_attempt.attempt_number < retry_attempt.max_attempts:
                            # Schedule next retry
                            next_attempt_at = await self._calculate_next_retry_time(
                                retry_attempt.retry_strategy,
                                retry_attempt.attempt_number
                            )

                            retry_attempt.next_attempt_at = next_attempt_at
                            retry_attempt.attempt_number += 1
                            retry_attempt.last_attempt_at = datetime.utcnow()

                            await self._store_retry_attempt(retry_attempt)
                            await self._schedule_retry_task(retry_attempt)
                        else:
                            # Max attempts reached or no retry needed
                            await self._remove_retry_attempt(retry_attempt.payment_intent_id)
                            await self._log_final_failure(retry_attempt, result)

                    except Exception as e:
                        logger.error(f"Error processing retry for {retry_key}: {e}")

                # Remove processed items from queue
                if retry_keys:
                    self.redis.zrem('retry_queue', *retry_keys)

            except Exception as e:
                logger.error(f"Error in retry queue processing: {e}")

            await asyncio.sleep(30)  # Process every 30 seconds

    async def _attempt_payment_retry(self, retry_attempt: RetryAttempt) -> RetryResult:
        """Attempt to retry a failed payment"""
        try:
            # Get payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(retry_attempt.payment_intent_id)

            # Check if payment is already succeeded
            if payment_intent.status == 'succeeded':
                return RetryResult(
                    success=True,
                    payment_intent_id=retry_attempt.payment_intent_id,
                    attempt_number=retry_attempt.attempt_number,
                    response={'status': 'already_succeeded'},
                    error=None,
                    should_retry=False,
                    next_retry_at=None
                )

            # Attempt to confirm the payment again
            # Note: In production, you might need different logic based on the failure reason
            try:
                confirmed_payment = stripe.PaymentIntent.confirm(
                    retry_attempt.payment_intent_id,
                    # Include any updated payment method if available
                )

                if confirmed_payment.status == 'succeeded':
                    return RetryResult(
                        success=True,
                        payment_intent_id=retry_attempt.payment_intent_id,
                        attempt_number=retry_attempt.attempt_number,
                        response={
                            'status': confirmed_payment.status,
                            'amount': confirmed_payment.amount,
                            'currency': confirmed_payment.currency
                        },
                        error=None,
                        should_retry=False,
                        next_retry_at=None
                    )
                else:
                    # Payment still failed
                    return RetryResult(
                        success=False,
                        payment_intent_id=retry_attempt.payment_intent_id,
                        attempt_number=retry_attempt.attempt_number,
                        response={'status': confirmed_payment.status},
                        error=confirmed_payment.last_payment_error.get('message') if confirmed_payment.last_payment_error else 'Unknown error',
                        should_retry=self._should_retry_failure(confirmed_payment.last_payment_error),
                        next_retry_at=None
                    )

            except stripe.error.StripeError as e:
                return RetryResult(
                    success=False,
                    payment_intent_id=retry_attempt.payment_intent_id,
                    attempt_number=retry_attempt.attempt_number,
                    response=None,
                    error=str(e),
                    should_retry=self._should_retry_stripe_error(e),
                    next_retry_at=None
                )

        except Exception as e:
            logger.error(f"Error attempting payment retry: {e}")
            return RetryResult(
                success=False,
                payment_intent_id=retry_attempt.payment_intent_id,
                attempt_number=retry_attempt.attempt_number,
                response=None,
                error=str(e),
                should_retry=False,
                next_retry_at=None
            )

    def _select_retry_strategy(self, retry_category: str) -> str:
        """Select appropriate retry strategy based on failure category"""
        strategy_mapping = {
            'card_declined': 'smart_retry',
            'insufficient_funds': 'exponential_backoff',
            'network_error': 'immediate_retry',
            'processing_error': 'fixed_interval',
            'authentication_required': 'smart_retry',
            'generic_decline': 'exponential_backoff'
        }

        return strategy_mapping.get(retry_category, 'exponential_backoff')

    async def _calculate_next_retry_time(self, strategy: str, attempt_number: int) -> datetime:
        """Calculate next retry time based on strategy"""
        strategy_func = self.retry_strategies.get(strategy, self._exponential_backoff)
        return await strategy_func(attempt_number)

    async def _exponential_backoff(self, attempt_number: int) -> datetime:
        """Exponential backoff: 1min, 4min, 16min, 64min, etc."""
        delay_minutes = 1 ** (attempt_number + 1)  # 1, 4, 16, 64, etc.
        delay_minutes = min(delay_minutes, 1440)  # Max 24 hours
        return datetime.utcnow() + timedelta(minutes=delay_minutes)

    async def _fixed_interval(self, attempt_number: int) -> datetime:
        """Fixed interval: 5 minutes between retries"""
        return datetime.utcnow() + timedelta(minutes=5)

    async def _immediate_retry(self, attempt_number: int) -> datetime:
        """Immediate retry for network errors"""
        return datetime.utcnow() + timedelta(seconds=30)

    async def _smart_retry(self, attempt_number: int) -> datetime:
        """Smart retry based on attempt number"""
        if attempt_number == 1:
            return datetime.utcnow() + timedelta(minutes=1)
        elif attempt_number == 2:
            return datetime.utcnow() + timedelta(hours=1)
        else:
            return datetime.utcnow() + timedelta(hours=6)

    def _should_retry_failure(self, payment_error: Optional[Dict[str, Any]]) -> bool:
        """Determine if a payment failure should be retried"""
        if not payment_error:
            return False

        decline_code = payment_error.get('decline_code', '')
        non_retryable_codes = [
            'card_not_supported', 'currency_not_supported', 'duplicate_transaction',
            'expired_card', 'incorrect_cvc', 'incorrect_number', 'invalid_card_type',
            'invalid_cvc', 'invalid_expiry_month', 'invalid_expiry_year',
            'invalid_number', 'issuer_not_available', 'lost_card', 'stolen_card'
        ]

        return decline_code not in non_retryable_codes

    def _should_retry_stripe_error(self, error: stripe.error.StripeError) -> bool:
        """Determine if a Stripe error should be retried"""
        # Retry on network errors, rate limits, and some card errors
        retryable_errors = (
            stripe.error.APIConnectionError,
            stripe.error.APIError,
            stripe.error.RateLimitError,
            stripe.error.TimeoutError
        )

        return isinstance(error, retryable_errors)

    async def _get_retry_attempt(self, payment_intent_id: str) -> Optional[RetryAttempt]:
        """Get existing retry attempt for a payment"""
        try:
            retry_data = self.redis.hgetall(f"retry:{payment_intent_id}")
            if not retry_data:
                return None

            return RetryAttempt(
                payment_intent_id=payment_intent_id,
                attempt_number=int(retry_data['attempt_number']),
                max_attempts=int(retry_data['max_attempts']),
                last_attempt_at=datetime.fromisoformat(retry_data['last_attempt_at']),
                next_attempt_at=datetime.fromisoformat(retry_data['next_attempt_at']),
                failure_reason=retry_data['failure_reason'],
                retry_strategy=retry_data['retry_strategy'],
                platform=retry_data['platform'],
                metadata=json.loads(retry_data.get('metadata', '{}'))
            )

        except Exception as e:
            logger.error(f"Error getting retry attempt: {e}")
            return None

    async def _store_retry_attempt(self, retry_attempt: RetryAttempt):
        """Store retry attempt data"""
        try:
            retry_data = {
                'payment_intent_id': retry_attempt.payment_intent_id,
                'attempt_number': retry_attempt.attempt_number,
                'max_attempts': retry_attempt.max_attempts,
                'last_attempt_at': retry_attempt.last_attempt_at.isoformat(),
                'next_attempt_at': retry_attempt.next_attempt_at.isoformat(),
                'failure_reason': retry_attempt.failure_reason,
                'retry_strategy': retry_attempt.retry_strategy,
                'platform': retry_attempt.platform,
                'metadata': json.dumps(retry_attempt.metadata)
            }

            self.redis.hmset(f"retry:{retry_attempt.payment_intent_id}", retry_data)

        except Exception as e:
            logger.error(f"Error storing retry attempt: {e}")

    async def _schedule_retry_task(self, retry_attempt: RetryAttempt):
        """Schedule retry task in Redis sorted set"""
        try:
            self.redis.zadd(
                'retry_queue',
                {retry_attempt.payment_intent_id: retry_attempt.next_attempt_at.timestamp()}
            )

        except Exception as e:
            logger.error(f"Error scheduling retry task: {e}")

    async def _remove_retry_attempt(self, payment_intent_id: str):
        """Remove retry attempt from queue and storage"""
        try:
            self.redis.delete(f"retry:{payment_intent_id}")
            self.redis.zrem('retry_queue', payment_intent_id)

        except Exception as e:
            logger.error(f"Error removing retry attempt: {e}")

    async def _log_final_failure(self, retry_attempt: RetryAttempt, result: RetryResult):
        """Log final failure after all retry attempts exhausted"""
        try:
            failure_data = {
                'payment_intent_id': retry_attempt.payment_intent_id,
                'platform': retry_attempt.platform,
                'total_attempts': retry_attempt.attempt_number,
                'final_error': result.error,
                'failure_reason': retry_attempt.failure_reason,
                'last_attempt_at': retry_attempt.last_attempt_at.isoformat(),
                'metadata': json.dumps(retry_attempt.metadata)
            }

            # Store final failure for analysis
            self.redis.hmset(f"final_failure:{retry_attempt.payment_intent_id}", failure_data)
            self.redis.expire(f"final_failure:{retry_attempt.payment_intent_id}", 2592000)  # 30 days

            logger.warning(f"Payment {retry_attempt.payment_intent_id} failed after {retry_attempt.attempt_number} attempts")

        except Exception as e:
            logger.error(f"Error logging final failure: {e}")

    async def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics for monitoring"""
        try:
            # Count items in retry queue
            queue_size = self.redis.zcard('retry_queue')

            # Get recent retry attempts
            recent_retries = self.redis.keys('retry:*')
            active_retries = len(recent_retries)

            # Get final failures in last 24 hours
            final_failures = self.redis.keys('final_failure:*')

            return {
                'queue_size': queue_size,
                'active_retries': active_retries,
                'final_failures_24h': len(final_failures),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting retry stats: {e}")
            return {'error': str(e)}

# Global retry engine instance
retry_engine = PaymentRetryEngine()