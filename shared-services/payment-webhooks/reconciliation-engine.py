"""
Payment Reconciliation Engine
Automated reconciliation of payment data between Stripe and internal systems
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import stripe
import aiohttp
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ReconciliationResult:
    """Result of reconciliation process"""
    period_start: datetime
    period_end: datetime
    total_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    discrepancies: List[Dict[str, Any]]
    reconciliation_status: str  # 'success', 'partial', 'failed'
    processing_time: float
    report_generated_at: datetime

@dataclass
class TransactionRecord:
    """Transaction record for reconciliation"""
    transaction_id: str
    platform: str
    amount: int
    currency: str
    status: str
    created_at: datetime
    metadata: Dict[str, Any]
    source: str  # 'stripe', 'internal'

class PaymentReconciliationEngine:
    """Automated payment reconciliation system"""

    def __init__(self):
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

        # Reconciliation configuration
        self.reconciliation_window_days = int(os.getenv('RECONCILIATION_WINDOW_DAYS', 30))
        self.auto_resolve_threshold = float(os.getenv('AUTO_RESOLVE_THRESHOLD', 0.01))  # 1% tolerance
        self.max_discrepancy_amount = int(os.getenv('MAX_DISCREPANCY_AMOUNT', 100))  # $1.00

    async def reconcile_payments(
        self,
        platform: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        auto_resolve: bool = False
    ) -> ReconciliationResult:
        """Perform payment reconciliation for a platform"""
        start_time = datetime.utcnow()

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=self.reconciliation_window_days)
        if not end_date:
            end_date = datetime.utcnow()

        logger.info(f"Starting reconciliation for {platform} from {start_date} to {end_date}")

        try:
            # Fetch Stripe transactions
            stripe_transactions = await self._fetch_stripe_transactions(platform, start_date, end_date)

            # Fetch internal transactions
            internal_transactions = await self._fetch_internal_transactions(platform, start_date, end_date)

            # Perform reconciliation
            matched, unmatched_stripe, unmatched_internal, discrepancies = await self._reconcile_transactions(
                stripe_transactions, internal_transactions
            )

            # Auto-resolve minor discrepancies if enabled
            if auto_resolve:
                resolved_count = await self._auto_resolve_discrepancies(discrepancies, platform)
                logger.info(f"Auto-resolved {resolved_count} discrepancies")

            # Generate reconciliation report
            result = ReconciliationResult(
                period_start=start_date,
                period_end=end_date,
                total_transactions=len(stripe_transactions) + len(internal_transactions),
                matched_transactions=len(matched),
                unmatched_transactions=len(unmatched_stripe) + len(unmatched_internal),
                discrepancies=discrepancies,
                reconciliation_status=self._calculate_reconciliation_status(
                    len(matched), len(stripe_transactions), len(internal_transactions)
                ),
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                report_generated_at=datetime.utcnow()
            )

            # Store reconciliation result
            await self._store_reconciliation_result(platform, result)

            # Send alerts for significant discrepancies
            await self._alert_on_discrepancies(platform, result)

            logger.info(f"Reconciliation completed for {platform}: {result.reconciliation_status}")
            return result

        except Exception as e:
            logger.error(f"Reconciliation failed for {platform}: {e}")
            raise

    async def _fetch_stripe_transactions(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TransactionRecord]:
        """Fetch transactions from Stripe"""
        transactions = []

        try:
            # Get payment intents from Stripe
            payment_intents = stripe.PaymentIntent.list(
                created={
                    'gte': int(start_date.timestamp()),
                    'lte': int(end_date.timestamp())
                },
                limit=100  # Adjust as needed
            )

            for pi in payment_intents.auto_paging_iter():
                # Filter by platform metadata
                if pi.metadata.get('platform') == platform or platform == 'all':
                    transaction = TransactionRecord(
                        transaction_id=pi.id,
                        platform=pi.metadata.get('platform', 'unknown'),
                        amount=pi.amount,
                        currency=pi.currency,
                        status=pi.status,
                        created_at=datetime.fromtimestamp(pi.created),
                        metadata=dict(pi.metadata),
                        source='stripe'
                    )
                    transactions.append(transaction)

        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch Stripe transactions: {e}")
            raise

        logger.info(f"Fetched {len(transactions)} Stripe transactions for {platform}")
        return transactions

    async def _fetch_internal_transactions(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TransactionRecord]:
        """Fetch transactions from internal systems"""
        transactions = []

        try:
            # This would integrate with platform-specific APIs
            # For now, simulate by checking Redis analytics data

            import redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )

            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y%m%d')

                # Get analytics data (this would be replaced with actual internal API calls)
                analytics_key = f"analytics:{platform}:payments:{date_str}"
                analytics_data = redis_client.hgetall(analytics_key)

                if analytics_data:
                    # Create transaction records from analytics data
                    # This is simplified - in production, you'd fetch actual transaction records
                    total_payments = int(analytics_data.get('total_payments', 0))

                    # Note: This is a placeholder. In production, you'd have actual transaction IDs
                    for i in range(min(total_payments, 10)):  # Limit for demo
                        transaction = TransactionRecord(
                            transaction_id=f"internal_{platform}_{date_str}_{i}",
                            platform=platform,
                            amount=1000,  # Placeholder amount
                            currency='usd',
                            status='succeeded',
                            created_at=current_date,
                            metadata={'source': 'internal_analytics'},
                            source='internal'
                        )
                        transactions.append(transaction)

                current_date += timedelta(days=1)

        except Exception as e:
            logger.error(f"Failed to fetch internal transactions: {e}")
            raise

        logger.info(f"Fetched {len(transactions)} internal transactions for {platform}")
        return transactions

    async def _reconcile_transactions(
        self,
        stripe_transactions: List[TransactionRecord],
        internal_transactions: List[TransactionRecord]
    ) -> Tuple[List[Dict[str, Any]], List[TransactionRecord], List[TransactionRecord], List[Dict[str, Any]]]:
        """Reconcile Stripe and internal transactions"""
        matched = []
        unmatched_stripe = []
        unmatched_internal = []
        discrepancies = []

        # Create lookup dictionaries
        stripe_lookup = {tx.transaction_id: tx for tx in stripe_transactions}
        internal_lookup = {tx.transaction_id: tx for tx in internal_transactions}

        # Find matches and discrepancies
        for stripe_tx in stripe_transactions:
            internal_tx = internal_lookup.get(stripe_tx.transaction_id)

            if internal_tx:
                # Check for discrepancies
                discrepancy = self._check_transaction_discrepancy(stripe_tx, internal_tx)
                if discrepancy:
                    discrepancies.append(discrepancy)
                else:
                    matched.append({
                        'transaction_id': stripe_tx.transaction_id,
                        'amount': stripe_tx.amount,
                        'currency': stripe_tx.currency,
                        'status': stripe_tx.status
                    })
            else:
                unmatched_stripe.append(stripe_tx)

        # Find unmatched internal transactions
        for internal_tx in internal_transactions:
            if internal_tx.transaction_id not in stripe_lookup:
                unmatched_internal.append(internal_tx)

        return matched, unmatched_stripe, unmatched_internal, discrepancies

    def _check_transaction_discrepancy(
        self,
        stripe_tx: TransactionRecord,
        internal_tx: TransactionRecord
    ) -> Optional[Dict[str, Any]]:
        """Check for discrepancies between Stripe and internal transaction"""
        discrepancies = []

        # Check amount
        if stripe_tx.amount != internal_tx.amount:
            amount_diff = abs(stripe_tx.amount - internal_tx.amount)
            if amount_diff > self.max_discrepancy_amount:
                discrepancies.append({
                    'field': 'amount',
                    'stripe_value': stripe_tx.amount,
                    'internal_value': internal_tx.amount,
                    'difference': amount_diff
                })

        # Check currency
        if stripe_tx.currency != internal_tx.currency:
            discrepancies.append({
                'field': 'currency',
                'stripe_value': stripe_tx.currency,
                'internal_value': internal_tx.currency
            })

        # Check status
        if stripe_tx.status != internal_tx.status:
            discrepancies.append({
                'field': 'status',
                'stripe_value': stripe_tx.status,
                'internal_value': internal_tx.status
            })

        if discrepancies:
            return {
                'transaction_id': stripe_tx.transaction_id,
                'discrepancies': discrepancies,
                'severity': 'high' if any(d['field'] == 'amount' and d['difference'] > 100 for d in discrepancies) else 'medium'
            }

        return None

    async def _auto_resolve_discrepancies(
        self,
        discrepancies: List[Dict[str, Any]],
        platform: str
    ) -> int:
        """Auto-resolve minor discrepancies"""
        resolved_count = 0

        for discrepancy in discrepancies:
            # Only auto-resolve small amount differences
            amount_discrepancies = [
                d for d in discrepancy['discrepancies']
                if d['field'] == 'amount' and d['difference'] <= self.max_discrepancy_amount
            ]

            if amount_discrepancies and len(discrepancy['discrepancies']) == 1:
                # Mark as resolved
                discrepancy['status'] = 'auto_resolved'
                discrepancy['resolved_at'] = datetime.utcnow().isoformat()
                resolved_count += 1

                logger.info(f"Auto-resolved discrepancy for transaction {discrepancy['transaction_id']}")

        return resolved_count

    def _calculate_reconciliation_status(
        self,
        matched_count: int,
        stripe_count: int,
        internal_count: int
    ) -> str:
        """Calculate overall reconciliation status"""
        total_transactions = stripe_count + internal_count

        if total_transactions == 0:
            return 'no_data'

        match_rate = (matched_count * 2) / total_transactions  # *2 because each match represents 2 records

        if match_rate >= 0.95:  # 95% match rate
            return 'success'
        elif match_rate >= 0.80:  # 80% match rate
            return 'partial'
        else:
            return 'failed'

    async def _store_reconciliation_result(self, platform: str, result: ReconciliationResult):
        """Store reconciliation result for auditing"""
        try:
            import redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )

            result_key = f"reconciliation:{platform}:{result.period_end.strftime('%Y%m%d')}"

            result_data = {
                'period_start': result.period_start.isoformat(),
                'period_end': result.period_end.isoformat(),
                'total_transactions': result.total_transactions,
                'matched_transactions': result.matched_transactions,
                'unmatched_transactions': result.unmatched_transactions,
                'reconciliation_status': result.reconciliation_status,
                'processing_time': result.processing_time,
                'report_generated_at': result.report_generated_at.isoformat(),
                'discrepancies': json.dumps(result.discrepancies)
            }

            redis_client.hmset(result_key, result_data)
            redis_client.expire(result_key, 2592000)  # 30 days

        except Exception as e:
            logger.error(f"Failed to store reconciliation result: {e}")

    async def _alert_on_discrepancies(self, platform: str, result: ReconciliationResult):
        """Send alerts for significant reconciliation discrepancies"""
        try:
            significant_discrepancies = [
                d for d in result.discrepancies
                if d.get('severity') == 'high' and d.get('status') != 'auto_resolved'
            ]

            if significant_discrepancies:
                alert_data = {
                    'platform': platform,
                    'period': {
                        'start': result.period_start.isoformat(),
                        'end': result.period_end.isoformat()
                    },
                    'discrepancy_count': len(significant_discrepancies),
                    'reconciliation_status': result.reconciliation_status,
                    'discrepancies': significant_discrepancies[:5]  # Top 5
                }

                # In production, this would send alerts via email/Slack/webhook
                logger.warning(f"Significant reconciliation discrepancies detected for {platform}: {len(significant_discrepancies)} issues")

        except Exception as e:
            logger.error(f"Failed to send discrepancy alerts: {e}")

    async def get_reconciliation_history(
        self,
        platform: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get reconciliation history for monitoring"""
        try:
            import redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )

            history = []
            current_date = datetime.utcnow()

            for i in range(days):
                check_date = current_date - timedelta(days=i)
                result_key = f"reconciliation:{platform}:{check_date.strftime('%Y%m%d')}"

                result_data = redis_client.hgetall(result_key)
                if result_data:
                    history.append({
                        'date': check_date.strftime('%Y-%m-%d'),
                        'status': result_data.get('reconciliation_status'),
                        'total_transactions': int(result_data.get('total_transactions', 0)),
                        'matched_transactions': int(result_data.get('matched_transactions', 0)),
                        'unmatched_transactions': int(result_data.get('unmatched_transactions', 0)),
                        'processing_time': float(result_data.get('processing_time', 0))
                    })

            return history

        except Exception as e:
            logger.error(f"Failed to get reconciliation history: {e}")
            return []

    async def generate_reconciliation_report(
        self,
        platform: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate detailed reconciliation report"""
        try:
            result = await self.reconcile_payments(platform, start_date, end_date)

            report = {
                'report_metadata': {
                    'platform': platform,
                    'generated_at': datetime.utcnow().isoformat(),
                    'period': {
                        'start': result.period_start.isoformat(),
                        'end': result.period_end.isoformat()
                    }
                },
                'summary': {
                    'reconciliation_status': result.reconciliation_status,
                    'total_transactions': result.total_transactions,
                    'matched_transactions': result.matched_transactions,
                    'unmatched_transactions': result.unmatched_transactions,
                    'match_rate': (result.matched_transactions / max(result.total_transactions, 1)) * 100,
                    'processing_time_seconds': result.processing_time
                },
                'discrepancies': result.discrepancies,
                'recommendations': self._generate_reconciliation_recommendations(result)
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate reconciliation report: {e}")
            return {'error': str(e)}

    def _generate_reconciliation_recommendations(self, result: ReconciliationResult) -> List[str]:
        """Generate recommendations based on reconciliation results"""
        recommendations = []

        match_rate = (result.matched_transactions / max(result.total_transactions, 1)) * 100

        if result.reconciliation_status == 'failed':
            recommendations.append("Critical: Reconciliation failed. Manual investigation required.")
            recommendations.append("Check webhook delivery and processing.")
            recommendations.append("Verify Stripe API connectivity.")

        elif result.reconciliation_status == 'partial':
            recommendations.append("Partial reconciliation detected. Review unmatched transactions.")
            if result.unmatched_transactions > 10:
                recommendations.append("High number of unmatched transactions. Check data synchronization.")

        if result.discrepancies:
            high_severity = [d for d in result.discrepancies if d.get('severity') == 'high']
            if high_severity:
                recommendations.append(f"Address {len(high_severity)} high-severity discrepancies immediately.")

        if match_rate < 95:
            recommendations.append("Implement additional data validation and error handling.")

        if not recommendations:
            recommendations.append("Reconciliation successful. Continue monitoring.")

        return recommendations

# Global reconciliation engine instance
reconciliation_engine = PaymentReconciliationEngine()