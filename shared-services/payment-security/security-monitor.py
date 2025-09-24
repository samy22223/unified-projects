"""
Payment Security Monitoring and Alerting System
Real-time security monitoring with automated alerting
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import redis
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    affected_resources: List[str]
    recommended_actions: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False

class SecurityMonitor:
    """Real-time security monitoring system"""

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Alert thresholds
        self.thresholds = {
            'failed_payments_per_hour': 50,
            'suspicious_ips_per_hour': 10,
            'high_risk_transactions_per_hour': 20,
            'chargeback_rate_threshold': 0.02,  # 2%
        }

        # Alert channels
        self.alert_channels = {
            'email': self._send_email_alert,
            'webhook': self._send_webhook_alert,
            'slack': self._send_slack_alert,
        }

    async def monitor_security_metrics(self):
        """Continuously monitor security metrics"""
        while True:
            try:
                await self._check_security_thresholds()
                await self._analyze_security_patterns()
                await self._cleanup_old_alerts()
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")

            await asyncio.sleep(300)  # Check every 5 minutes

    async def _check_security_thresholds(self):
        """Check if security metrics exceed thresholds"""
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')

        # Check failed payments
        failed_key = f"failed_payments:{current_hour}"
        failed_count = self.redis.scard(failed_key)

        if failed_count > self.thresholds['failed_payments_per_hour']:
            await self._create_security_alert(
                alert_type='high_failure_rate',
                severity='high',
                title='High Payment Failure Rate Detected',
                description=f"{failed_count} payment failures in the last hour",
                recommended_actions=[
                    'Review payment processing system',
                    'Check for API issues',
                    'Monitor Stripe dashboard for outages'
                ]
            )

        # Check suspicious IPs
        suspicious_key = f"suspicious_ips:{current_hour}"
        suspicious_count = self.redis.scard(suspicious_key)

        if suspicious_count > self.thresholds['suspicious_ips_per_hour']:
            await self._create_security_alert(
                alert_type='suspicious_activity',
                severity='medium',
                title='High Volume of Suspicious IP Activity',
                description=f"{suspicious_count} suspicious IPs detected in the last hour",
                recommended_actions=[
                    'Review fraud detection rules',
                    'Check IP geolocation patterns',
                    'Consider temporary rate limiting'
                ]
            )

        # Check high-risk transactions
        high_risk_key = f"high_risk_transactions:{current_hour}"
        high_risk_count = self.redis.scard(high_risk_key)

        if high_risk_count > self.thresholds['high_risk_transactions_per_hour']:
            await self._create_security_alert(
                alert_type='high_risk_volume',
                severity='high',
                title='High Volume of High-Risk Transactions',
                description=f"{high_risk_count} high-risk transactions in the last hour",
                recommended_actions=[
                    'Enable manual review for high-risk payments',
                    'Strengthen fraud detection rules',
                    'Consider additional verification steps'
                ]
            )

    async def _analyze_security_patterns(self):
        """Analyze security patterns for anomalies"""
        # Check for unusual geographic patterns
        await self._check_geographic_anomalies()

        # Check for payment amount anomalies
        await self._check_amount_anomalies()

        # Check for velocity attacks
        await self._check_velocity_patterns()

        # Check chargeback rates
        await self._check_chargeback_rates()

    async def _check_geographic_anomalies(self):
        """Check for unusual geographic payment patterns"""
        # Get payments by country in last 24 hours
        countries = {}
        current_time = datetime.utcnow()

        for hours_ago in range(24):
            check_time = current_time - timedelta(hours=hours_ago)
            hour_key = check_time.strftime('%Y%m%d%H')

            country_data = self.redis.hgetall(f"geo_payments:{hour_key}")
            for country, count in country_data.items():
                countries[country] = countries.get(country, 0) + int(count)

        # Check for sudden spikes in unusual countries
        total_payments = sum(countries.values())
        for country, count in countries.items():
            percentage = count / total_payments if total_payments > 0 else 0

            # Flag if any country has >50% of payments (unusual concentration)
            if percentage > 0.5 and total_payments > 10:
                await self._create_security_alert(
                    alert_type='geographic_anomaly',
                    severity='medium',
                    title='Unusual Geographic Payment Concentration',
                    description=f"{country}: {percentage:.1%} of payments ({count}/{total_payments})",
                    recommended_actions=[
                        'Review payment sources from this country',
                        'Check for coordinated payment activities',
                        'Consider additional verification for this region'
                    ]
                )

    async def _check_amount_anomalies(self):
        """Check for unusual payment amount patterns"""
        # Get payment amounts from last hour
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')
        amount_key = f"payment_amounts:{current_hour}"

        amounts = self.redis.lrange(amount_key, 0, -1)
        if not amounts:
            return

        amounts = [float(amount) for amount in amounts]

        # Check for round number patterns (common in fraud)
        round_amounts = [amt for amt in amounts if amt % 100 == 0 and amt >= 1000]
        if len(round_amounts) > len(amounts) * 0.3:  # >30% round amounts
            await self._create_security_alert(
                alert_type='amount_pattern_anomaly',
                severity='low',
                title='Unusual Round Amount Pattern Detected',
                description=f"{len(round_amounts)}/{len(amounts)} payments are round amounts ≥$10",
                recommended_actions=[
                    'Monitor for card testing patterns',
                    'Review payment sources',
                    'Consider amount-based fraud rules'
                ]
            )

    async def _check_velocity_patterns(self):
        """Check for velocity-based attack patterns"""
        # Check for rapid payment attempts from same IP
        current_hour = datetime.utcnow().strftime('%Y%m%d%H')
        velocity_key = f"ip_velocity:{current_hour}"

        ip_counts = self.redis.hgetall(velocity_key)
        for ip, count in ip_counts.items():
            if int(count) > 20:  # More than 20 payments per hour from one IP
                await self._create_security_alert(
                    alert_type='velocity_attack',
                    severity='high',
                    title='Potential Velocity Attack Detected',
                    description=f"IP {ip}: {count} payments in last hour",
                    recommended_actions=[
                        'Block or rate-limit this IP address',
                        'Review payment patterns',
                        'Enable additional fraud detection'
                    ]
                )

    async def _check_chargeback_rates(self):
        """Check chargeback rates against thresholds"""
        # Calculate chargeback rate for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        total_chargebacks = 0
        total_payments = 0

        for days_ago in range(30):
            check_date = (thirty_days_ago + timedelta(days=days_ago)).strftime('%Y%m%d')

            chargebacks = self.redis.get(f"chargebacks:{check_date}") or 0
            payments = self.redis.get(f"total_payments:{check_date}") or 0

            total_chargebacks += int(chargebacks)
            total_payments += int(payments)

        if total_payments > 100:  # Only check if we have meaningful data
            chargeback_rate = total_chargebacks / total_payments

            if chargeback_rate > self.thresholds['chargeback_rate_threshold']:
                await self._create_security_alert(
                    alert_type='high_chargeback_rate',
                    severity='critical',
                    title='High Chargeback Rate Alert',
                    description=".2%",
                    recommended_actions=[
                        'Review chargeback reasons',
                        'Implement additional verification',
                        'Contact payment processor',
                        'Consider payment method restrictions'
                    ]
                )

    async def _create_security_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        affected_resources: List[str] = None,
        recommended_actions: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> SecurityAlert:
        """Create and distribute a security alert"""
        alert = SecurityAlert(
            alert_id=f"sec_alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            affected_resources=affected_resources or [],
            recommended_actions=recommended_actions or [],
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )

        # Store alert
        alert_key = f"security_alert:{alert.alert_id}"
        alert_data = {
            'alert_id': alert.alert_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'description': alert.description,
            'affected_resources': json.dumps(alert.affected_resources),
            'recommended_actions': json.dumps(alert.recommended_actions),
            'metadata': json.dumps(alert.metadata),
            'timestamp': alert.timestamp.isoformat(),
            'resolved': str(alert.resolved)
        }

        self.redis.hmset(alert_key, alert_data)
        self.redis.expire(alert_key, 2592000)  # 30 days

        # Add to alerts list
        self.redis.lpush(f"security_alerts:{severity}", alert.alert_id)
        self.redis.ltrim(f"security_alerts:{severity}", 0, 499)  # Keep last 500 alerts

        logger.warning(f"Security alert created: {alert.alert_id} ({severity}) - {title}")

        # Send alerts via configured channels
        await self._distribute_alert(alert)

        return alert

    async def _distribute_alert(self, alert: SecurityAlert):
        """Distribute alert via configured channels"""
        channels = os.getenv('ALERT_CHANNELS', 'email').split(',')

        for channel in channels:
            if channel in self.alert_channels:
                try:
                    await self.alert_channels[channel](alert)
                except Exception as e:
                    logger.error(f"Failed to send {channel} alert: {e}")

    async def _send_email_alert(self, alert: SecurityAlert):
        """Send security alert via email"""
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        alert_emails = os.getenv('ALERT_EMAILS', '').split(',')

        if not all([smtp_server, smtp_user, smtp_password, alert_emails]):
            logger.warning("Email alert configuration incomplete")
            return

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = ', '.join(alert_emails)
        msg['Subject'] = f"🔴 SECURITY ALERT: {alert.title}"

        body = f"""
SECURITY ALERT - {alert.severity.upper()}

Title: {alert.title}
Type: {alert.alert_type}
Time: {alert.timestamp.isoformat()}

Description:
{alert.description}

Recommended Actions:
{chr(10).join(f"- {action}" for action in alert.recommended_actions)}

Alert ID: {alert.alert_id}

This is an automated security alert from the Payment Security Monitor.
Please review immediately.
        """

        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, alert_emails, msg.as_string())
            server.quit()

            logger.info(f"Security alert email sent to {len(alert_emails)} recipients")

        except Exception as e:
            logger.error(f"Failed to send security alert email: {e}")

    async def _send_webhook_alert(self, alert: SecurityAlert):
        """Send security alert via webhook"""
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if not webhook_url:
            return

        payload = {
            'alert_id': alert.alert_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'title': alert.title,
            'description': alert.description,
            'recommended_actions': alert.recommended_actions,
            'timestamp': alert.timestamp.isoformat(),
            'metadata': alert.metadata
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Security alert webhook sent successfully")
                    else:
                        logger.error(f"Security alert webhook failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send security alert webhook: {e}")

    async def _send_slack_alert(self, alert: SecurityAlert):
        """Send security alert to Slack"""
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if not slack_webhook:
            return

        # Color coding for severity
        colors = {
            'low': 'good',
            'medium': 'warning',
            'high': 'danger',
            'critical': '#ff0000'
        }

        payload = {
            'attachments': [{
                'color': colors.get(alert.severity, 'danger'),
                'title': f"🔴 {alert.title}",
                'text': alert.description,
                'fields': [
                    {
                        'title': 'Severity',
                        'value': alert.severity.upper(),
                        'short': True
                    },
                    {
                        'title': 'Type',
                        'value': alert.alert_type,
                        'short': True
                    },
                    {
                        'title': 'Alert ID',
                        'value': alert.alert_id,
                        'short': True
                    }
                ],
                'footer': 'Payment Security Monitor',
                'ts': alert.timestamp.timestamp()
            }]
        }

        if alert.recommended_actions:
            payload['attachments'][0]['fields'].append({
                'title': 'Recommended Actions',
                'value': '\n'.join(f"• {action}" for action in alert.recommended_actions),
                'short': False
            })

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    slack_webhook,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info("Security alert sent to Slack successfully")
                    else:
                        logger.error(f"Security alert Slack webhook failed: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send security alert to Slack: {e}")

    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        # Keep alerts for 90 days, resolved alerts for 30 days
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Get all alert keys
        alert_keys = self.redis.keys("security_alert:*")

        for key in alert_keys:
            alert_data = self.redis.hgetall(key)
            if not alert_data:
                continue

            alert_timestamp = datetime.fromisoformat(alert_data['timestamp'])
            resolved = alert_data.get('resolved', 'False').lower() == 'true'

            # Delete old alerts
            if resolved and alert_timestamp < thirty_days_ago:
                self.redis.delete(key)
            elif not resolved and alert_timestamp < ninety_days_ago:
                self.redis.delete(key)

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        dashboard = {
            'active_alerts': {},
            'recent_activity': [],
            'risk_metrics': {},
            'timestamp': datetime.utcnow().isoformat()
        }

        # Get active alerts by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            alert_ids = self.redis.lrange(f"security_alerts:{severity}", 0, 9)  # Last 10
            alerts = []

            for alert_id in alert_ids:
                alert_key = f"security_alert:{alert_id}"
                alert_data = self.redis.hgetall(alert_key)
                if alert_data:
                    alerts.append({
                        'alert_id': alert_data['alert_id'],
                        'title': alert_data['title'],
                        'description': alert_data['description'],
                        'timestamp': alert_data['timestamp'],
                        'resolved': alert_data.get('resolved', 'False') == 'True'
                    })

            dashboard['active_alerts'][severity] = alerts

        # Get recent security activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        activity_keys = [
            'failed_payments:*',
            'suspicious_ips:*',
            'high_risk_transactions:*'
        ]

        # This would aggregate recent activity data
        dashboard['recent_activity'] = []  # Placeholder for activity data

        # Get risk metrics
        dashboard['risk_metrics'] = {
            'total_failed_payments_24h': 0,  # Would calculate from Redis
            'total_suspicious_ips_24h': 0,
            'total_high_risk_transactions_24h': 0,
            'chargeback_rate_30d': 0.0
        }

        return dashboard

# Global security monitor instance
security_monitor = SecurityMonitor()