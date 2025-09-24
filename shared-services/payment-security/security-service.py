#!/usr/bin/env python3
"""
Payment Security Service
FastAPI service providing fraud detection and security monitoring
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from fraud_detection import fraud_engine, RiskAssessment
from security_monitor import security_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Payment Security Service",
    description="Advanced fraud detection and security monitoring for payment processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start background security monitoring"""
    logger.info("Starting payment security service...")
    # Start security monitoring in background
    # Note: In production, this would be handled by a separate process/worker

@app.post("/assess-risk", response_model=Dict[str, Any])
async def assess_payment_risk(
    payment_intent_id: str,
    customer_id: Optional[str] = None,
    amount: int = 0,
    currency: str = "usd",
    metadata: Optional[Dict[str, Any]] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    email: Optional[str] = None
):
    """
    Assess payment risk using advanced fraud detection

    This endpoint evaluates payment transactions for fraud risk
    using multiple detection algorithms and patterns.
    """
    try:
        assessment = await fraud_engine.assess_payment_risk(
            payment_intent_id=payment_intent_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            metadata=metadata,
            client_ip=client_ip,
            user_agent=user_agent,
            email=email
        )

        # Create fraud alert if high risk
        if assessment.risk_level in ['high', 'critical']:
            await fraud_engine.create_fraud_alert(
                alert_type='high_risk_payment',
                payment_intent_id=payment_intent_id,
                customer_id=customer_id,
                amount=amount,
                currency=currency,
                risk_score=assessment.risk_score,
                risk_factors=assessment.risk_factors,
                metadata={
                    'client_ip': client_ip,
                    'user_agent': user_agent,
                    'email': email,
                    **(metadata or {})
                }
            )

        return {
            'payment_intent_id': payment_intent_id,
            'risk_assessment': {
                'risk_level': assessment.risk_level,
                'risk_score': assessment.risk_score,
                'risk_factors': assessment.risk_factors,
                'recommendations': assessment.recommendations,
                'requires_action': assessment.requires_action
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail="Risk assessment failed")

@app.post("/report-suspicious-activity")
async def report_suspicious_activity(
    activity_type: str,
    payment_intent_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "medium"
):
    """
    Report suspicious payment activity

    This endpoint allows manual reporting of suspicious activities
    that may not be caught by automated detection.
    """
    try:
        await fraud_engine.create_fraud_alert(
            alert_type=f"manual_report_{activity_type}",
            payment_intent_id=payment_intent_id or "unknown",
            customer_id=customer_id,
            amount=0,
            currency="usd",
            risk_score=75 if severity == "high" else 50,  # Default risk scores
            risk_factors=[f"Manually reported: {activity_type}"],
            metadata={
                'reported_by': 'manual',
                'severity': severity,
                'details': details or {}
            }
        )

        return {
            'status': 'reported',
            'activity_type': activity_type,
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to report suspicious activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to report activity")

@app.get("/security-dashboard", response_model=Dict[str, Any])
async def get_security_dashboard():
    """
    Get comprehensive security dashboard data

    Returns current security status, active alerts, and risk metrics.
    """
    try:
        dashboard = await security_monitor.get_security_dashboard()

        # Add fraud detection summary
        dashboard['fraud_detection'] = {
            'engine_status': 'active',
            'patterns_monitored': len(fraud_engine.fraud_patterns),
            'last_assessment': datetime.utcnow().isoformat()
        }

        return dashboard

    except Exception as e:
        logger.error(f"Failed to get security dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard")

@app.get("/risk-metrics")
async def get_risk_metrics(hours: int = 24):
    """
    Get risk metrics for the specified time period

    Returns aggregated risk data and fraud statistics.
    """
    try:
        # This would aggregate risk metrics from Redis
        # For now, return placeholder structure
        return {
            'period_hours': hours,
            'metrics': {
                'total_assessments': 0,
                'high_risk_detected': 0,
                'fraud_alerts_created': 0,
                'blocked_transactions': 0,
                'average_risk_score': 0.0
            },
            'top_risk_factors': [],
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@app.post("/block-ip")
async def block_ip_address(
    ip_address: str,
    reason: str,
    duration_hours: int = 24,
    customer_id: Optional[str] = None
):
    """
    Block an IP address due to suspicious activity

    This endpoint adds IP addresses to a blocklist for the specified duration.
    """
    try:
        # In a production system, this would integrate with:
        # - Web Application Firewall (WAF)
        # - Load balancer rules
        # - Redis-based IP blocking
        # - Database of blocked IPs

        block_key = f"blocked_ip:{ip_address}"
        block_data = {
            'ip_address': ip_address,
            'reason': reason,
            'blocked_at': datetime.utcnow().isoformat(),
            'duration_hours': duration_hours,
            'customer_id': customer_id
        }

        # Store in Redis with expiration
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        redis_client.hmset(block_key, block_data)
        redis_client.expire(block_key, duration_hours * 3600)  # Convert to seconds

        # Create security alert
        await security_monitor._create_security_alert(
            alert_type='ip_blocked',
            severity='medium',
            title=f'IP Address Blocked: {ip_address}',
            description=f'IP {ip_address} blocked for {duration_hours} hours due to: {reason}',
            recommended_actions=[
                'Monitor for attempts to bypass block',
                'Review associated payment attempts',
                'Consider permanent blocking if pattern continues'
            ],
            metadata=block_data
        )

        return {
            'status': 'blocked',
            'ip_address': ip_address,
            'duration_hours': duration_hours,
            'reason': reason,
            'blocked_at': block_data['blocked_at']
        }

    except Exception as e:
        logger.error(f"Failed to block IP address: {e}")
        raise HTTPException(status_code=500, detail="Failed to block IP address")

@app.get("/blocked-ips")
async def get_blocked_ips():
    """
    Get list of currently blocked IP addresses
    """
    try:
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Get all blocked IP keys
        blocked_keys = redis_client.keys("blocked_ip:*")
        blocked_ips = []

        for key in blocked_keys:
            ip_data = redis_client.hgetall(key)
            if ip_data:
                blocked_ips.append(ip_data)

        return {
            'blocked_ips': blocked_ips,
            'total_count': len(blocked_ips),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get blocked IPs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve blocked IPs")

@app.post("/update-fraud-rules")
async def update_fraud_rules(rules: Dict[str, Any]):
    """
    Update fraud detection rules and thresholds

    Allows dynamic adjustment of fraud detection parameters.
    """
    try:
        # Update fraud engine thresholds
        if 'thresholds' in rules:
            fraud_engine.risk_thresholds.update(rules['thresholds'])

        # Update security monitor thresholds
        if 'security_thresholds' in rules:
            security_monitor.thresholds.update(rules['security_thresholds'])

        return {
            'status': 'updated',
            'updated_rules': rules,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to update fraud rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to update rules")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connectivity
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        redis_client.ping()

        return {
            "status": "healthy",
            "service": "payment-security",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "fraud_detection": "active",
                "security_monitoring": "active",
                "redis": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "payment-security",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(
        "security-service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )