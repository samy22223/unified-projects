"""
Payment Analytics and Reporting Dashboard
Comprehensive business intelligence for payment data across unified projects
"""

import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import redis
import aiohttp
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PaymentMetrics:
    """Payment metrics data structure"""
    total_revenue: float
    transaction_count: int
    average_transaction_value: float
    successful_payments: int
    failed_payments: int
    refund_amount: float
    chargeback_amount: float
    period: str

@dataclass
class SubscriptionMetrics:
    """Subscription analytics data structure"""
    total_subscribers: int
    active_subscribers: int
    churned_subscribers: int
    new_subscribers: int
    monthly_recurring_revenue: float
    annual_recurring_revenue: float
    churn_rate: float
    conversion_rate: float
    average_revenue_per_user: float

@dataclass
class PlatformComparison:
    """Cross-platform comparison metrics"""
    platform_revenue: Dict[str, float]
    platform_transactions: Dict[str, int]
    platform_users: Dict[str, int]
    platform_growth: Dict[str, float]
    market_share: Dict[str, float]

class PaymentAnalyticsEngine:
    """Advanced payment analytics and reporting engine"""

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Analytics retention periods
        self.retention_days = {
            'hourly': 7,      # 7 days of hourly data
            'daily': 90,      # 90 days of daily data
            'monthly': 365,   # 1 year of monthly data
            'yearly': 1825    # 5 years of yearly data
        }

    async def get_payment_dashboard(
        self,
        platform: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive payment dashboard data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        dashboard = {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'summary': await self._get_payment_summary(platform, start_date, end_date),
            'trends': await self._get_payment_trends(platform, start_date, end_date),
            'breakdown': await self._get_payment_breakdown(platform, start_date, end_date),
            'forecast': await self._get_revenue_forecast(platform, days),
            'alerts': await self._get_payment_alerts(platform),
            'generated_at': datetime.utcnow().isoformat()
        }

        return dashboard

    async def _get_payment_summary(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate payment summary metrics"""
        total_revenue = 0.0
        transaction_count = 0
        successful_payments = 0
        failed_payments = 0
        refund_amount = 0.0
        chargeback_amount = 0.0

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')

            # Aggregate data from Redis
            if platform:
                key_prefix = f"analytics:{platform}:payments:{date_str}"
            else:
                # Cross-platform aggregation (simplified)
                key_prefix = f"analytics:*:payments:{date_str}"

            # Get daily metrics (would be stored by payment processors)
            daily_revenue = float(self.redis.get(f"{key_prefix}:revenue") or 0)
            daily_transactions = int(self.redis.get(f"{key_prefix}:transactions") or 0)
            daily_successful = int(self.redis.get(f"{key_prefix}:successful") or 0)
            daily_failed = int(self.redis.get(f"{key_prefix}:failed") or 0)
            daily_refunds = float(self.redis.get(f"{key_prefix}:refunds") or 0)
            daily_chargebacks = float(self.redis.get(f"{key_prefix}:chargebacks") or 0)

            total_revenue += daily_revenue
            transaction_count += daily_transactions
            successful_payments += daily_successful
            failed_payments += daily_failed
            refund_amount += daily_refunds
            chargeback_amount += daily_chargebacks

            current_date += timedelta(days=1)

        success_rate = (successful_payments / transaction_count * 100) if transaction_count > 0 else 0
        average_transaction = total_revenue / transaction_count if transaction_count > 0 else 0

        return {
            'total_revenue': total_revenue,
            'transaction_count': transaction_count,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'success_rate': round(success_rate, 2),
            'average_transaction_value': round(average_transaction, 2),
            'refund_amount': refund_amount,
            'chargeback_amount': chargeback_amount,
            'net_revenue': total_revenue - refund_amount - chargeback_amount
        }

    async def _get_payment_trends(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze payment trends over time"""
        trends = {
            'daily_revenue': [],
            'daily_transactions': [],
            'success_rate_trend': [],
            'cumulative_revenue': [],
            'growth_rate': []
        }

        cumulative_revenue = 0.0
        previous_revenue = 0.0

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')

            if platform:
                key_prefix = f"analytics:{platform}:payments:{date_str}"
            else:
                key_prefix = f"analytics:total:payments:{date_str}"

            daily_revenue = float(self.redis.get(f"{key_prefix}:revenue") or 0)
            daily_transactions = int(self.redis.get(f"{key_prefix}:transactions") or 0)
            daily_successful = int(self.redis.get(f"{key_prefix}:successful") or 0)
            daily_total = int(self.redis.get(f"{key_prefix}:total") or 0)

            success_rate = (daily_successful / daily_total * 100) if daily_total > 0 else 0
            cumulative_revenue += daily_revenue

            # Calculate growth rate
            growth_rate = ((daily_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

            trends['daily_revenue'].append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': daily_revenue
            })

            trends['daily_transactions'].append({
                'date': current_date.strftime('%Y-%m-%d'),
                'transactions': daily_transactions
            })

            trends['success_rate_trend'].append({
                'date': current_date.strftime('%Y-%m-%d'),
                'success_rate': round(success_rate, 2)
            })

            trends['cumulative_revenue'].append({
                'date': current_date.strftime('%Y-%m-%d'),
                'cumulative': cumulative_revenue
            })

            trends['growth_rate'].append({
                'date': current_date.strftime('%Y-%m-%d'),
                'growth_rate': round(growth_rate, 2)
            })

            previous_revenue = daily_revenue
            current_date += timedelta(days=1)

        return trends

    async def _get_payment_breakdown(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get detailed payment breakdown by categories"""
        breakdown = {
            'by_payment_method': {},
            'by_country': {},
            'by_currency': {},
            'by_amount_range': {},
            'by_hour_of_day': {},
            'by_day_of_week': {}
        }

        # This would aggregate detailed payment data
        # Simplified implementation with sample data structure

        # Payment method breakdown
        breakdown['by_payment_method'] = {
            'credit_card': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'debit_card': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'digital_wallet': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'bank_transfer': {'count': 0, 'revenue': 0.0, 'percentage': 0.0}
        }

        # Geographic breakdown
        breakdown['by_country'] = {
            'US': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'UK': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'DE': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'FR': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            'Others': {'count': 0, 'revenue': 0.0, 'percentage': 0.0}
        }

        # Amount range breakdown
        breakdown['by_amount_range'] = {
            '0-10': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            '10-50': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            '50-100': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            '100-500': {'count': 0, 'revenue': 0.0, 'percentage': 0.0},
            '500+': {'count': 0, 'revenue': 0.0, 'percentage': 0.0}
        }

        return breakdown

    async def _get_revenue_forecast(
        self,
        platform: Optional[str],
        days: int
    ) -> Dict[str, Any]:
        """Generate revenue forecast using historical data"""
        # Simple linear regression forecast (simplified)
        forecast = {
            'forecast_period_days': 30,
            'predicted_revenue': 0.0,
            'confidence_interval': {'lower': 0.0, 'upper': 0.0},
            'growth_rate': 0.0,
            'seasonal_factors': {},
            'forecast_accuracy': 0.0
        }

        # Calculate average daily revenue from last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        total_revenue = 0.0
        days_with_data = 0

        current_date = start_date
        while current_date < end_date:
            date_str = current_date.strftime('%Y%m%d')
            if platform:
                key = f"analytics:{platform}:payments:{date_str}:revenue"
            else:
                key = f"analytics:total:payments:{date_str}:revenue"

            daily_revenue = float(self.redis.get(key) or 0)
            total_revenue += daily_revenue
            if daily_revenue > 0:
                days_with_data += 1

            current_date += timedelta(days=1)

        if days_with_data > 0:
            avg_daily_revenue = total_revenue / days_with_data
            forecast['predicted_revenue'] = avg_daily_revenue * 30  # 30-day forecast

            # Simple confidence interval (±20%)
            forecast['confidence_interval'] = {
                'lower': forecast['predicted_revenue'] * 0.8,
                'upper': forecast['predicted_revenue'] * 1.2
            }

        return forecast

    async def _get_payment_alerts(self, platform: Optional[str]) -> List[Dict[str, Any]]:
        """Get payment-related alerts and warnings"""
        alerts = []

        # Check for unusual patterns
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        # Revenue drop alert
        recent_revenue = await self._calculate_period_revenue(platform, start_date, end_date)
        previous_period = await self._calculate_period_revenue(
            platform,
            start_date - timedelta(days=7),
            start_date
        )

        if previous_period > 0:
            revenue_change = ((recent_revenue - previous_period) / previous_period) * 100
            if revenue_change < -20:  # 20% drop
                alerts.append({
                    'type': 'revenue_drop',
                    'severity': 'high',
                    'title': 'Significant Revenue Drop Detected',
                    'description': f"Revenue decreased by {abs(revenue_change):.1f}% compared to previous period",
                    'recommendation': 'Review payment processing, check for technical issues, analyze customer behavior'
                })

        # High failure rate alert
        failure_rate = await self._calculate_failure_rate(platform, start_date, end_date)
        if failure_rate > 5:  # >5% failure rate
            alerts.append({
                'type': 'high_failure_rate',
                'severity': 'medium',
                'title': 'High Payment Failure Rate',
                'description': f"Payment failure rate is {failure_rate:.1f}%",
                'recommendation': 'Check payment processor status, review declined payments, consider alternative payment methods'
            })

        # Chargeback alert
        chargeback_rate = await self._calculate_chargeback_rate(platform, start_date, end_date)
        if chargeback_rate > 0.02:  # >2% chargeback rate
            alerts.append({
                'type': 'high_chargeback_rate',
                'severity': 'critical',
                'title': 'High Chargeback Rate Alert',
                'description': f"Chargeback rate is {chargeback_rate:.2%}",
                'recommendation': 'Review chargeback reasons, implement fraud prevention, contact payment processor'
            })

        return alerts

    async def _calculate_period_revenue(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate total revenue for a period"""
        total = 0.0
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            if platform:
                key = f"analytics:{platform}:payments:{date_str}:revenue"
            else:
                key = f"analytics:total:payments:{date_str}:revenue"

            total += float(self.redis.get(key) or 0)
            current_date += timedelta(days=1)

        return total

    async def _calculate_failure_rate(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate payment failure rate for a period"""
        total_payments = 0
        failed_payments = 0
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            if platform:
                total_key = f"analytics:{platform}:payments:{date_str}:total"
                failed_key = f"analytics:{platform}:payments:{date_str}:failed"
            else:
                total_key = f"analytics:total:payments:{date_str}:total"
                failed_key = f"analytics:total:payments:{date_str}:failed"

            total_payments += int(self.redis.get(total_key) or 0)
            failed_payments += int(self.redis.get(failed_key) or 0)
            current_date += timedelta(days=1)

        return (failed_payments / total_payments * 100) if total_payments > 0 else 0

    async def _calculate_chargeback_rate(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate chargeback rate for a period"""
        total_payments = 0
        chargebacks = 0
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime('%Y%m%d')
            if platform:
                total_key = f"analytics:{platform}:payments:{date_str}:total"
                chargeback_key = f"analytics:{platform}:payments:{date_str}:chargebacks"
            else:
                total_key = f"analytics:total:payments:{date_str}:total"
                chargeback_key = f"analytics:total:payments:{date_str}:chargebacks"

            total_payments += int(self.redis.get(total_key) or 0)
            chargebacks += int(self.redis.get(chargeback_key) or 0)
            current_date += timedelta(days=1)

        return chargebacks / total_payments if total_payments > 0 else 0

    async def export_analytics_report(
        self,
        platform: Optional[str],
        start_date: datetime,
        end_date: datetime,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """Export comprehensive analytics report"""
        report = {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'platform': platform or 'all',
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'format': format
            },
            'executive_summary': {},
            'detailed_metrics': {},
            'trends_analysis': {},
            'recommendations': []
        }

        # Get dashboard data
        dashboard = await self.get_payment_dashboard(platform, (end_date - start_date).days)

        # Generate executive summary
        summary = dashboard['summary']
        report['executive_summary'] = {
            'total_revenue': summary['total_revenue'],
            'total_transactions': summary['transaction_count'],
            'success_rate': summary['success_rate'],
            'average_transaction': summary['average_transaction_value'],
            'key_insights': self._generate_key_insights(summary)
        }

        # Detailed metrics
        report['detailed_metrics'] = dashboard

        # Trends analysis
        report['trends_analysis'] = await self._analyze_trends(dashboard['trends'])

        # Generate recommendations
        report['recommendations'] = await self._generate_recommendations(dashboard)

        return report

    def _generate_key_insights(self, summary: Dict[str, Any]) -> List[str]:
        """Generate key insights from summary data"""
        insights = []

        if summary['success_rate'] > 95:
            insights.append("Excellent payment success rate indicates reliable payment processing")
        elif summary['success_rate'] < 90:
            insights.append("Payment success rate needs improvement - investigate failure causes")

        if summary['average_transaction_value'] > 50:
            insights.append("High average transaction value suggests premium customer base")
        elif summary['average_transaction_value'] < 10:
            insights.append("Low average transaction value indicates high-volume, low-value transactions")

        if summary['refund_amount'] > summary['total_revenue'] * 0.05:
            insights.append("High refund rate requires investigation")

        return insights

    async def _analyze_trends(self, trends: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends for patterns and insights"""
        analysis = {
            'revenue_trend': 'stable',
            'transaction_trend': 'stable',
            'seasonal_patterns': [],
            'growth_acceleration': 0.0
        }

        # Analyze revenue trend
        revenue_data = [point['revenue'] for point in trends['daily_revenue']]
        if len(revenue_data) >= 7:
            recent_avg = sum(revenue_data[-7:]) / 7
            previous_avg = sum(revenue_data[-14:-7]) / 7 if len(revenue_data) >= 14 else recent_avg

            if recent_avg > previous_avg * 1.1:
                analysis['revenue_trend'] = 'growing'
            elif recent_avg < previous_avg * 0.9:
                analysis['revenue_trend'] = 'declining'

        return analysis

    async def _generate_recommendations(self, dashboard: Dict[str, Any]) -> List[str]:
        """Generate business recommendations based on analytics"""
        recommendations = []

        summary = dashboard['summary']
        alerts = dashboard['alerts']

        if summary['success_rate'] < 95:
            recommendations.append("Improve payment success rate by optimizing checkout flow and supporting more payment methods")

        if summary['refund_amount'] / summary['total_revenue'] > 0.03:
            recommendations.append("Reduce refund rate by improving product descriptions and customer support")

        if any(alert['severity'] == 'critical' for alert in alerts):
            recommendations.append("Address critical alerts immediately to prevent revenue impact")

        if not recommendations:
            recommendations.append("Continue monitoring payment performance and customer satisfaction")

        return recommendations

# Global analytics engine instance
analytics_engine = PaymentAnalyticsEngine()