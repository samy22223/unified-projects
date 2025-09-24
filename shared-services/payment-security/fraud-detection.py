"""
Payment Fraud Detection and Security System
Advanced fraud prevention for unified projects payment processing
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import redis
import stripe
from fastapi import HTTPException
import aiohttp
import re

logger = logging.getLogger(__name__)

@dataclass
class FraudAlert:
    """Fraud alert data structure"""
    alert_id: str
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    payment_intent_id: str
    customer_id: Optional[str]
    amount: int
    currency: str
    risk_score: int
    risk_factors: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    risk_score: int  # 0-100
    risk_factors: List[str]
    recommendations: List[str]
    requires_action: bool

class FraudDetectionEngine:
    """Advanced fraud detection engine"""

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Risk thresholds
        self.risk_thresholds = {
            'low': 30,
            'medium': 60,
            'high': 80,
            'critical': 95
        }

        # Fraud patterns to monitor
        self.fraud_patterns = {
            'velocity_check': self._check_velocity_attacks,
            'amount_anomaly': self._check_amount_anomalies,
            'geographic_anomaly': self._check_geographic_anomalies,
            'device_fingerprinting': self._check_device_fingerprinting,
            'email_domain_check': self._check_email_domain_risk,
            'ip_reputation': self._check_ip_reputation,
            'card_testing': self._check_card_testing_patterns,
            'chargeback_history': self._check_chargeback_history
        }

    async def assess_payment_risk(
        self,
        payment_intent_id: str,
        customer_id: Optional[str] = None,
        amount: int = 0,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        email: Optional[str] = None
    ) -> RiskAssessment:
        """
        Comprehensive risk assessment for payment transactions
        """
        risk_factors = []
        risk_score = 0

        # Run all fraud detection checks
        for check_name, check_func in self.fraud_patterns.items():
            try:
                factor, score = await check_func(
                    payment_intent_id=payment_intent_id,
                    customer_id=customer_id,
                    amount=amount,
                    currency=currency,
                    metadata=metadata,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    email=email
                )
                if factor:
                    risk_factors.extend(factor)
                    risk_score += score
            except Exception as e:
                logger.error(f"Fraud check {check_name} failed: {e}")

        # Cap risk score at 100
        risk_score = min(risk_score, 100)

        # Determine risk level
        risk_level = 'low'
        for level, threshold in self.risk_thresholds.items():
            if risk_score >= threshold:
                risk_level = level

        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, risk_factors)

        # Determine if action is required
        requires_action = risk_level in ['high', 'critical']

        return RiskAssessment(
            risk_level=risk_level,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            requires_action=requires_action
        )

    async def _check_velocity_attacks(
        self, payment_intent_id: str, customer_id: Optional[str] = None,
        amount: int = 0, **kwargs
    ) -> Tuple[List[str], int]:
        """Check for velocity attacks (rapid successive payments)"""
        factors = []
        risk_score = 0

        if not customer_id:
            return factors, risk_score

        # Check payments in last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        hour_key = f"payments:{customer_id}:{hour_ago.strftime('%Y%m%d%H')}"

        recent_payments = self.redis.scard(hour_key)
        if recent_payments > 10:  # More than 10 payments per hour
            factors.append(f"High velocity: {recent_payments} payments in last hour")
            risk_score += 40

        # Check payments in last 24 hours
        day_key = f"payments:{customer_id}:{hour_ago.strftime('%Y%m%d')}"
        daily_payments = self.redis.scard(day_key)
        if daily_payments > 50:  # More than 50 payments per day
            factors.append(f"Excessive daily volume: {daily_payments} payments in 24h")
            risk_score += 30

        return factors, risk_score

    async def _check_amount_anomalies(
        self, payment_intent_id: str, customer_id: Optional[str] = None,
        amount: int = 0, **kwargs
    ) -> Tuple[List[str], int]:
        """Check for unusual payment amounts"""
        factors = []
        risk_score = 0

        if not customer_id or amount <= 0:
            return factors, risk_score

        # Get customer's historical payment amounts
        history_key = f"amount_history:{customer_id}"
        historical_amounts = self.redis.lrange(history_key, 0, 9)  # Last 10 payments

        if historical_amounts:
            avg_amount = sum(float(amt) for amt in historical_amounts) / len(historical_amounts)
            deviation = abs(amount - avg_amount) / avg_amount if avg_amount > 0 else 0

            if deviation > 2.0:  # More than 200% deviation
                factors.append(".1f")
                risk_score += 25
            elif deviation > 1.0:  # More than 100% deviation
                factors.append(".1f")
                risk_score += 15

        # Check for round number amounts (common in fraud)
        if amount % 100 == 0 and amount >= 10000:  # Round thousands
            factors.append(f"Round amount pattern: ${amount/100}")
            risk_score += 10

        return factors, risk_score

    async def _check_geographic_anomalies(
        self, payment_intent_id: str, customer_id: Optional[str] = None,
        client_ip: Optional[str] = None, **kwargs
    ) -> Tuple[List[str], int]:
        """Check for geographic anomalies"""
        factors = []
        risk_score = 0

        if not customer_id or not client_ip:
            return factors, risk_score

        # Get customer's usual countries
        country_key = f"countries:{customer_id}"
        usual_countries = self.redis.smembers(country_key)

        # Get country from IP (simplified - in production use GeoIP service)
        current_country = await self._get_country_from_ip(client_ip)

        if usual_countries and current_country not in usual_countries:
            factors.append(f"Unusual country: {current_country} (usual: {', '.join(usual_countries)})")
            risk_score += 35

        return factors, risk_score

    async def _check_device_fingerprinting(
        self, payment_intent_id: str, customer_id: Optional[str] = None,
        user_agent: Optional[str] = None, **kwargs
    ) -> Tuple[List[str], int]:
        """Check device fingerprinting patterns"""
        factors = []
        risk_score = 0

        if not customer_id or not user_agent:
            return factors, risk_score

        # Store device fingerprints
        fingerprint = self._generate_device_fingerprint(user_agent)
        device_key = f"devices:{customer_id}"

        known_devices = self.redis.smembers(device_key)
        if known_devices and fingerprint not in known_devices:
            factors.append("Unrecognized device fingerprint")
            risk_score += 20

        # Check for suspicious user agents
        if self._is_suspicious_user_agent(user_agent):
            factors.append("Suspicious user agent pattern")
            risk_score += 25

        return factors, risk_score

    async def _check_email_domain_risk(
        self, payment_intent_id: str, email: Optional[str] = None, **kwargs
    ) -> Tuple[List[str], int]:
        """Check email domain for risk indicators"""
        factors = []
        risk_score = 0

        if not email:
            return factors, risk_score

        domain = email.split('@')[-1].lower()

        # High-risk domains
        high_risk_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'temp-mail.org', 'throwaway.email', 'yopmail.com'
        ]

        if domain in high_risk_domains:
            factors.append(f"High-risk email domain: {domain}")
            risk_score += 50

        # Check for suspicious patterns
        if re.match(r'.*\d{8,}.*', domain):  # Domains with long numbers
            factors.append("Suspicious email domain pattern")
            risk_score += 20

        return factors, risk_score

    async def _check_ip_reputation(
        self, payment_intent_id: str, client_ip: Optional[str] = None, **kwargs
    ) -> Tuple[List[str], int]:
        """Check IP reputation and risk"""
        factors = []
        risk_score = 0

        if not client_ip:
            return factors, risk_score

        # Check if IP is in known bad lists (simplified)
        if await self._is_ip_blacklisted(client_ip):
            factors.append(f"Blacklisted IP address: {client_ip}")
            risk_score += 60

        # Check for VPN/Tor usage (simplified detection)
        if self._is_likely_vpn_ip(client_ip):
            factors.append("Potential VPN/Tor usage detected")
            risk_score += 15

        return factors, risk_score

    async def _check_card_testing_patterns(
        self, payment_intent_id: str, customer_id: Optional[str] = None, **kwargs
    ) -> Tuple[List[str], int]:
        """Check for card testing patterns"""
        factors = []
        risk_score = 0

        if not customer_id:
            return factors, risk_score

        # Check recent failures for this customer
        failure_key = f"failures:{customer_id}"
        recent_failures = self.redis.llen(failure_key)

        if recent_failures > 5:  # More than 5 failures recently
            factors.append(f"High failure rate: {recent_failures} recent failures")
            risk_score += 45

        # Check for pattern of small amounts followed by larger ones
        amount_pattern = self._check_amount_progression_pattern(customer_id)
        if amount_pattern:
            factors.append("Suspicious amount progression pattern")
            risk_score += 20

        return factors, risk_score

    async def _check_chargeback_history(
        self, payment_intent_id: str, customer_id: Optional[str] = None, **kwargs
    ) -> Tuple[List[str], int]:
        """Check customer chargeback history"""
        factors = []
        risk_score = 0

        if not customer_id:
            return factors, risk_score

        # Check chargeback history
        chargeback_key = f"chargebacks:{customer_id}"
        chargeback_count = self.redis.get(chargeback_key) or 0

        if int(chargeback_count) > 0:
            factors.append(f"Previous chargebacks: {chargeback_count}")
            risk_score += int(chargeback_count) * 20  # 20 points per chargeback

        return factors, risk_score

    def _generate_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if risk_level in ['high', 'critical']:
            recommendations.append("Require additional verification (3D Secure, SMS code)")
            recommendations.append("Manual review recommended before processing")

        if 'velocity' in ' '.join(risk_factors).lower():
            recommendations.append("Implement velocity-based rate limiting")

        if 'geographic' in ' '.join(risk_factors).lower():
            recommendations.append("Request additional identity verification")

        if 'email' in ' '.join(risk_factors).lower():
            recommendations.append("Verify email ownership before processing")

        if not recommendations:
            recommendations.append("Monitor transaction closely")

        return recommendations

    async def create_fraud_alert(
        self,
        alert_type: str,
        payment_intent_id: str,
        customer_id: Optional[str] = None,
        amount: int = 0,
        currency: str = "usd",
        risk_score: int = 0,
        risk_factors: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FraudAlert:
        """Create and store a fraud alert"""
        alert = FraudAlert(
            alert_id=f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{payment_intent_id[:8]}",
            alert_type=alert_type,
            severity=self._calculate_severity(risk_score),
            payment_intent_id=payment_intent_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            risk_score=risk_score,
            risk_factors=risk_factors or [],
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )

        # Store alert in Redis
        alert_key = f"fraud_alert:{alert.alert_id}"
        alert_data = {
            'alert_id': alert.alert_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'payment_intent_id': alert.payment_intent_id,
            'customer_id': alert.customer_id,
            'amount': alert.amount,
            'currency': alert.currency,
            'risk_score': alert.risk_score,
            'risk_factors': json.dumps(alert.risk_factors),
            'metadata': json.dumps(alert.metadata),
            'timestamp': alert.timestamp.isoformat()
        }

        self.redis.hmset(alert_key, alert_data)
        self.redis.expire(alert_key, 2592000)  # 30 days

        # Add to alerts list for monitoring
        self.redis.lpush("fraud_alerts", alert.alert_id)
        self.redis.ltrim("fraud_alerts", 0, 999)  # Keep last 1000 alerts

        logger.warning(f"Fraud alert created: {alert.alert_id} (severity: {alert.severity})")

        return alert

    def _calculate_severity(self, risk_score: int) -> str:
        """Calculate alert severity based on risk score"""
        if risk_score >= 95:
            return 'critical'
        elif risk_score >= 80:
            return 'high'
        elif risk_score >= 60:
            return 'medium'
        else:
            return 'low'

    # Helper methods (simplified implementations)
    async def _get_country_from_ip(self, ip: str) -> str:
        """Get country from IP address (simplified)"""
        # In production, use a GeoIP service like MaxMind
        return "US"  # Placeholder

    async def _is_ip_blacklisted(self, ip: str) -> bool:
        """Check if IP is blacklisted (simplified)"""
        # In production, check against threat intelligence feeds
        return False  # Placeholder

    def _is_likely_vpn_ip(self, ip: str) -> bool:
        """Check if IP likely belongs to VPN/Tor (simplified)"""
        # In production, use VPN detection services
        return False  # Placeholder

    def _generate_device_fingerprint(self, user_agent: str) -> str:
        """Generate device fingerprint from user agent"""
        # Simplified fingerprinting
        return hash(user_agent) % 1000000

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agent patterns"""
        suspicious_patterns = [
            'curl', 'wget', 'python', 'bot', 'spider', 'crawler'
        ]
        return any(pattern.lower() in user_agent.lower() for pattern in suspicious_patterns)

    def _check_amount_progression_pattern(self, customer_id: str) -> bool:
        """Check for suspicious amount progression (simplified)"""
        # In production, analyze payment amount patterns
        return False  # Placeholder

# Global fraud detection instance
fraud_engine = FraudDetectionEngine()