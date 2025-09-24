#!/usr/bin/env python3
"""
Compliance Service
FastAPI service providing PCI DSS and GDPR compliance monitoring and reporting
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from compliance_engine import compliance_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Compliance Service",
    description="PCI DSS and GDPR compliance monitoring and reporting",
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
    """Initialize compliance service"""
    logger.info("Starting compliance service...")

@app.get("/dashboard", response_model=Dict[str, Any])
async def get_compliance_dashboard(api_key: str = Depends(get_api_key)):
    """
    Get compliance dashboard overview

    Returns overall compliance status, scores, and recent audit events
    for all platforms.
    """
    try:
        dashboard = await compliance_engine.get_compliance_dashboard()
        return dashboard

    except Exception as e:
        logger.error(f"Failed to get compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance dashboard")

@app.get("/platforms/{platform}/checks", response_model=Dict[str, Any])
async def run_compliance_checks(
    platform: str,
    api_key: str = Depends(get_api_key)
):
    """
    Run comprehensive compliance checks for a platform

    Executes all PCI DSS, GDPR, and security compliance checks
    and returns detailed results.
    """
    try:
        report = await compliance_engine.run_compliance_checks(platform)
        return report

    except Exception as e:
        logger.error(f"Failed to run compliance checks for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run compliance checks")

@app.get("/platforms/{platform}/status", response_model=Dict[str, Any])
async def get_compliance_status(
    platform: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get current compliance status for a platform

    Returns the latest compliance check results without running new checks.
    """
    try:
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        latest_key = f"compliance_latest:{platform}"
        report_data = redis_client.get(latest_key)

        if not report_data:
            return {
                'platform': platform,
                'status': 'no_data',
                'message': 'No compliance checks have been run yet'
            }

        report = redis_client.json().loads(report_data)
        return report

    except Exception as e:
        logger.error(f"Failed to get compliance status for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance status")

@app.post("/data-processing-records", response_model=Dict[str, str])
async def create_data_processing_record(
    data_subject: str = Query(..., description="Data subject identifier"),
    data_categories: List[str] = Query(..., description="Categories of personal data"),
    processing_purpose: str = Query(..., description="Purpose of processing"),
    legal_basis: str = Query(..., description="Legal basis for processing"),
    retention_period: str = Query(..., description="Data retention period"),
    api_key: str = Depends(get_api_key)
):
    """
    Create a GDPR data processing record

    Documents a data processing activity for GDPR compliance.
    """
    try:
        record_id = await compliance_engine.create_data_processing_record(
            data_subject=data_subject,
            data_categories=data_categories,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            retention_period=retention_period
        )

        return {
            'record_id': record_id,
            'status': 'created',
            'message': 'Data processing record created successfully'
        }

    except Exception as e:
        logger.error(f"Failed to create data processing record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create data processing record")

@app.post("/audit/log", response_model=Dict[str, str])
async def log_audit_event(
    user_id: Optional[str] = Query(None, description="User ID performing action"),
    action: str = Query(..., description="Action performed"),
    resource: str = Query(..., description="Resource affected"),
    ip_address: str = Query(..., description="Client IP address"),
    user_agent: str = Query(..., description="User agent string"),
    success: bool = Query(True, description="Whether action was successful"),
    details: Optional[Dict[str, Any]] = None,
    api_key: str = Depends(get_api_key)
):
    """
    Log an audit event for compliance tracking

    Records security-relevant events for compliance auditing.
    """
    try:
        entry_id = await compliance_engine.log_audit_event(
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details
        )

        return {
            'entry_id': entry_id,
            'status': 'logged',
            'message': 'Audit event logged successfully'
        }

    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log audit event")

@app.get("/audit/events", response_model=List[Dict[str, Any]])
async def get_audit_events(
    limit: int = Query(100, description="Maximum number of events to return", le=1000),
    offset: int = Query(0, description="Number of events to skip"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    api_key: str = Depends(get_api_key)
):
    """
    Retrieve audit events with filtering options

    Returns paginated audit log entries for compliance review.
    """
    try:
        import redis
        from datetime import datetime

        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Get audit log keys for the current month
        current_month = datetime.utcnow().strftime('%Y%m')
        audit_list_key = f"audit_log:{current_month}"

        # Get audit entry IDs
        audit_ids = redis_client.lrange(audit_list_key, offset, offset + limit - 1)

        events = []
        for audit_id in audit_ids:
            audit_data = redis_client.get(f"audit:{audit_id}")
            if audit_data:
                event = redis_client.json().loads(audit_data)

                # Apply filters
                if user_id and event.get('user_id') != user_id:
                    continue
                if action and event.get('action') != action:
                    continue
                if resource and event.get('resource') != resource:
                    continue

                # Date filtering would require additional indexing for efficiency
                # For now, return all events within the month

                events.append(event)

        return events

    except Exception as e:
        logger.error(f"Failed to retrieve audit events: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit events")

@app.get("/reports/{platform}/pci-dss", response_model=Dict[str, Any])
async def get_pci_dss_report(
    platform: str,
    api_key: str = Depends(get_api_key)
):
    """
    Generate PCI DSS compliance report

    Returns detailed PCI DSS compliance status and requirements.
    """
    try:
        # Get latest compliance report
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        latest_key = f"compliance_latest:{platform}"
        report_data = redis_client.get(latest_key)

        if not report_data:
            raise HTTPException(status_code=404, detail="No compliance data available")

        full_report = redis_client.json().loads(report_data)

        # Extract PCI DSS checks
        pci_checks = [
            check for check in full_report.get('checks', [])
            if check.get('category') == 'pci_dss'
        ]

        pci_summary = {
            check['requirement']: {
                'description': compliance_engine.pci_requirements.get(check['requirement'], 'Unknown'),
                'status': check['status'],
                'severity': check['severity'],
                'last_checked': check['checked_at']
            }
            for check in pci_checks
        }

        passed_requirements = len([c for c in pci_checks if c['status'] == 'pass'])
        total_requirements = len(pci_checks)

        return {
            'platform': platform,
            'report_type': 'pci_dss',
            'generated_at': datetime.utcnow().isoformat(),
            'compliance_score': round((passed_requirements / total_requirements) * 100, 1) if total_requirements > 0 else 0,
            'passed_requirements': passed_requirements,
            'total_requirements': total_requirements,
            'requirements': pci_summary,
            'recommendations': [
                "Implement quarterly vulnerability scans",
                "Maintain detailed change management procedures",
                "Conduct annual security awareness training",
                "Perform regular penetration testing"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate PCI DSS report for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PCI DSS report")

@app.get("/reports/{platform}/gdpr", response_model=Dict[str, Any])
async def get_gdpr_report(
    platform: str,
    api_key: str = Depends(get_api_key)
):
    """
    Generate GDPR compliance report

    Returns detailed GDPR compliance status and data processing activities.
    """
    try:
        # Get latest compliance report
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        latest_key = f"compliance_latest:{platform}"
        report_data = redis_client.get(latest_key)

        if not report_data:
            raise HTTPException(status_code=404, detail="No compliance data available")

        full_report = redis_client.json().loads(report_data)

        # Extract GDPR checks
        gdpr_checks = [
            check for check in full_report.get('checks', [])
            if check.get('category') == 'gdpr'
        ]

        # Get data processing records
        dpr_keys = redis_client.keys('dpr:*')
        data_processing_records = []

        for key in dpr_keys[:50]:  # Limit to last 50 records
            record_data = redis_client.get(key)
            if record_data:
                record = redis_client.json().loads(record_data)
                data_processing_records.append({
                    'record_id': record['record_id'],
                    'data_subject': record['data_subject'],
                    'processing_purpose': record['processing_purpose'],
                    'legal_basis': record['legal_basis'],
                    'retention_period': record['retention_period'],
                    'created_at': record['created_at']
                })

        passed_principles = len([c for c in gdpr_checks if c['status'] == 'pass'])
        total_principles = len(gdpr_checks)

        return {
            'platform': platform,
            'report_type': 'gdpr',
            'generated_at': datetime.utcnow().isoformat(),
            'compliance_score': round((passed_principles / total_principles) * 100, 1) if total_principles > 0 else 0,
            'passed_principles': passed_principles,
            'total_principles': total_principles,
            'data_processing_records': data_processing_records,
            'data_subject_rights_implemented': any(
                c['requirement'] == 'data_subject_rights' and c['status'] == 'pass'
                for c in gdpr_checks
            ),
            'dpo_appointed': any(
                c['requirement'] == 'dpo_appointment' and c['status'] == 'pass'
                for c in gdpr_checks
            ),
            'recommendations': [
                "Conduct Data Protection Impact Assessment (DPIA) for high-risk processing",
                "Implement data subject access request procedures",
                "Establish data breach notification procedures within 72 hours",
                "Conduct regular data protection training for staff",
                "Maintain detailed records of processing activities"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate GDPR report for {platform}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate GDPR report")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        import redis
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        redis_client.ping()

        return {
            "status": "healthy",
            "service": "compliance",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "redis": "connected",
                "compliance_engine": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "compliance",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Helper function for API key validation
async def get_api_key(api_key: str = Query(..., alias="api_key")):
    """Validate API key for compliance service access"""
    expected_key = os.getenv('COMPLIANCE_API_KEY', 'compliance_key_123')
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

if __name__ == "__main__":
    uvicorn.run(
        "compliance-service:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8003)),
        reload=True
    )