"""
Payment Compliance Engine
PCI DSS and GDPR compliance framework for payment processing
"""

import os
import json
import logging
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import redis
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ComplianceCheck:
    """Compliance check result"""
    check_id: str
    category: str  # 'pci_dss', 'gdpr', 'security'
    requirement: str
    status: str  # 'pass', 'fail', 'warning', 'not_applicable'
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    evidence: Dict[str, Any]
    remediation: Optional[str]
    checked_at: datetime
    expires_at: Optional[datetime]

@dataclass
class DataProcessingRecord:
    """GDPR data processing record"""
    record_id: str
    data_subject: str
    data_categories: List[str]
    processing_purpose: str
    legal_basis: str
    retention_period: str
    data_controllers: List[str]
    data_processors: List[str]
    created_at: datetime
    consent_obtained: bool
    consent_withdrawn_at: Optional[datetime]

@dataclass
class AuditLogEntry:
    """Compliance audit log entry"""
    entry_id: str
    timestamp: datetime
    user_id: Optional[str]
    action: str
    resource: str
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any]
    compliance_flags: List[str]

class ComplianceEngine:
    """Comprehensive compliance engine for PCI DSS and GDPR"""

    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )

        # Compliance check intervals
        self.check_intervals = {
            'daily': timedelta(days=1),
            'weekly': timedelta(days=7),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90)
        }

        # PCI DSS requirements mapping
        self.pci_requirements = {
            '1': 'Install and maintain network security controls',
            '2': 'Apply secure configurations to all system components',
            '3': 'Protect stored account data',
            '4': 'Protect cardholder data with strong cryptography during transmission',
            '5': 'Protect all systems and networks from malicious software',
            '6': 'Develop and maintain secure systems and software',
            '7': 'Restrict access to system components and cardholder data',
            '8': 'Identify users and authenticate access to system components',
            '9': 'Restrict physical access to cardholder data',
            '10': 'Log and monitor all access to system resources and cardholder data',
            '11': 'Test security of systems and networks regularly',
            '12': 'Support information security with organizational policies and programs'
        }

    async def run_compliance_checks(self, platform: str) -> Dict[str, Any]:
        """Run comprehensive compliance checks for a platform"""
        logger.info(f"Running compliance checks for {platform}")

        checks = []

        # PCI DSS checks
        pci_checks = await self._run_pci_dss_checks(platform)
        checks.extend(pci_checks)

        # GDPR checks
        gdpr_checks = await self._run_gdpr_checks(platform)
        checks.extend(gdpr_checks)

        # Security checks
        security_checks = await self._run_security_checks(platform)
        checks.extend(security_checks)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(checks)

        # Generate compliance report
        report = {
            'platform': platform,
            'generated_at': datetime.utcnow().isoformat(),
            'compliance_score': compliance_score,
            'overall_status': self._get_overall_status(checks),
            'checks': [asdict(check) for check in checks],
            'summary': self._generate_compliance_summary(checks),
            'recommendations': self._generate_recommendations(checks)
        }

        # Store compliance results
        await self._store_compliance_results(platform, report)

        return report

    async def _run_pci_dss_checks(self, platform: str) -> List[ComplianceCheck]:
        """Run PCI DSS compliance checks"""
        checks = []

        # Requirement 1: Network security controls
        checks.append(await self._check_network_security(platform))

        # Requirement 2: Secure configurations
        checks.append(await self._check_secure_configurations(platform))

        # Requirement 3: Stored data protection
        checks.append(await self._check_stored_data_protection(platform))

        # Requirement 4: Data transmission protection
        checks.append(await self._check_transmission_protection(platform))

        # Requirement 5: Malware protection
        checks.append(await self._check_malware_protection(platform))

        # Requirement 6: Secure software development
        checks.append(await self._check_secure_development(platform))

        # Requirement 7: Access control
        checks.append(await self._check_access_control(platform))

        # Requirement 8: User authentication
        checks.append(await self._check_user_authentication(platform))

        # Requirement 9: Physical access control
        checks.append(await self._check_physical_access(platform))

        # Requirement 10: Logging and monitoring
        checks.append(await self._check_logging_monitoring(platform))

        # Requirement 11: Regular testing
        checks.append(await self._check_regular_testing(platform))

        # Requirement 12: Security policies
        checks.append(await self._check_security_policies(platform))

        return checks

    async def _run_gdpr_checks(self, platform: str) -> List[ComplianceCheck]:
        """Run GDPR compliance checks"""
        checks = []

        # Data protection principles
        checks.append(await self._check_lawful_processing(platform))
        checks.append(await self._check_data_minimization(platform))
        checks.append(await self._check_purpose_limitation(platform))
        checks.append(await self._check_accuracy(platform))
        checks.append(await self._check_storage_limitation(platform))
        checks.append(await self._check_integrity_confidentiality(platform))
        checks.append(await self._check_accountability(platform))

        # Data subject rights
        checks.append(await self._check_data_subject_rights(platform))

        # Data breach notification
        checks.append(await self._check_breach_notification(platform))

        # Data protection officer
        checks.append(await self._check_dpo_appointment(platform))

        # DPIA requirements
        checks.append(await self._check_dpia_requirements(platform))

        return checks

    async def _run_security_checks(self, platform: str) -> List[ComplianceCheck]:
        """Run general security compliance checks"""
        checks = []

        # Encryption checks
        checks.append(await self._check_encryption_standards(platform))

        # Access control checks
        checks.append(await self._check_access_controls(platform))

        # Audit logging
        checks.append(await self._check_audit_logging(platform))

        # Incident response
        checks.append(await self._check_incident_response(platform))

        # Vulnerability management
        checks.append(await self._check_vulnerability_management(platform))

        return checks

    # PCI DSS Check Implementations
    async def _check_network_security(self, platform: str) -> ComplianceCheck:
        """Check PCI DSS Requirement 1: Network security controls"""
        # Check for firewall configuration, network segmentation
        firewall_configured = await self._check_firewall_configuration(platform)
        network_segmented = await self._check_network_segmentation(platform)

        status = 'pass' if firewall_configured and network_segmented else 'fail'
        severity = 'critical' if status == 'fail' else 'low'

        return ComplianceCheck(
            check_id=f'{platform}_pci_1',
            category='pci_dss',
            requirement='1',
            status=status,
            severity=severity,
            description='Install and maintain network security controls',
            evidence={
                'firewall_configured': firewall_configured,
                'network_segmented': network_segmented
            },
            remediation='Configure firewall rules and implement network segmentation' if status == 'fail' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['monthly']
        )

    async def _check_stored_data_protection(self, platform: str) -> ComplianceCheck:
        """Check PCI DSS Requirement 3: Stored data protection"""
        # Check encryption of stored cardholder data
        data_encrypted = await self._check_data_encryption(platform)
        pan_masked = await self._check_pan_masking(platform)
        sensitive_authentication_data_not_stored = await self._check_auth_data_not_stored(platform)

        status = 'pass' if data_encrypted and pan_masked and sensitive_authentication_data_not_stored else 'fail'
        severity = 'critical' if not data_encrypted else 'high' if not pan_masked else 'medium'

        return ComplianceCheck(
            check_id=f'{platform}_pci_3',
            category='pci_dss',
            requirement='3',
            status=status,
            severity=severity,
            description='Protect stored account data',
            evidence={
                'data_encrypted': data_encrypted,
                'pan_masked': pan_masked,
                'sensitive_auth_data_not_stored': sensitive_authentication_data_not_stored
            },
            remediation='Implement encryption for stored card data and ensure sensitive authentication data is not retained' if status == 'fail' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['monthly']
        )

    async def _check_transmission_protection(self, platform: str) -> ComplianceCheck:
        """Check PCI DSS Requirement 4: Data transmission protection"""
        # Check TLS 1.2+ usage and secure transmission
        tls_enabled = await self._check_tls_configuration(platform)
        secure_transmission = await self._check_secure_transmission(platform)

        status = 'pass' if tls_enabled and secure_transmission else 'fail'
        severity = 'critical' if status == 'fail' else 'low'

        return ComplianceCheck(
            check_id=f'{platform}_pci_4',
            category='pci_dss',
            requirement='4',
            status=status,
            severity=severity,
            description='Protect cardholder data with strong cryptography during transmission',
            evidence={
                'tls_enabled': tls_enabled,
                'secure_transmission': secure_transmission
            },
            remediation='Enable TLS 1.2+ and ensure all cardholder data is encrypted in transit' if status == 'fail' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['monthly']
        )

    async def _check_logging_monitoring(self, platform: str) -> ComplianceCheck:
        """Check PCI DSS Requirement 10: Logging and monitoring"""
        # Check audit logging implementation
        logs_enabled = await self._check_audit_logging_enabled(platform)
        log_review = await self._check_log_review_process(platform)
        time_sync = await self._check_time_synchronization(platform)

        status = 'pass' if logs_enabled and log_review and time_sync else 'fail'
        severity = 'high' if status == 'fail' else 'low'

        return ComplianceCheck(
            check_id=f'{platform}_pci_10',
            category='pci_dss',
            requirement='10',
            status=status,
            severity=severity,
            description='Log and monitor all access to system resources and cardholder data',
            evidence={
                'logs_enabled': logs_enabled,
                'log_review_process': log_review,
                'time_synchronization': time_sync
            },
            remediation='Implement comprehensive audit logging and regular log review processes' if status == 'fail' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['daily']
        )

    # GDPR Check Implementations
    async def _check_lawful_processing(self, platform: str) -> ComplianceCheck:
        """Check GDPR lawful processing principle"""
        lawful_basis_documented = await self._check_lawful_basis_documentation(platform)
        consent_obtained = await self._check_consent_obtained(platform)

        status = 'pass' if lawful_basis_documented and consent_obtained else 'fail'
        severity = 'critical' if status == 'fail' else 'medium'

        return ComplianceCheck(
            check_id=f'{platform}_gdpr_lawful',
            category='gdpr',
            requirement='lawful_processing',
            status=status,
            severity=severity,
            description='Process personal data lawfully, fairly and transparently',
            evidence={
                'lawful_basis_documented': lawful_basis_documented,
                'consent_obtained': consent_obtained
            },
            remediation='Document lawful basis for processing and ensure valid consent is obtained' if status == 'fail' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['quarterly']
        )

    async def _check_data_minimization(self, platform: str) -> ComplianceCheck:
        """Check GDPR data minimization principle"""
        data_minimized = await self._check_data_minimization_practice(platform)
        retention_policy = await self._check_retention_policy(platform)

        status = 'pass' if data_minimized and retention_policy else 'warning'
        severity = 'high' if status == 'warning' else 'low'

        return ComplianceCheck(
            check_id=f'{platform}_gdpr_minimization',
            category='gdpr',
            requirement='data_minimization',
            status=status,
            severity=severity,
            description='Limit personal data collection to what is necessary',
            evidence={
                'data_minimized': data_minimized,
                'retention_policy_exists': retention_policy
            },
            remediation='Review data collection practices and implement data minimization principles' if status == 'warning' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['quarterly']
        )

    async def _check_data_subject_rights(self, platform: str) -> ComplianceCheck:
        """Check GDPR data subject rights implementation"""
        access_right = await self._check_subject_access_right(platform)
        rectification_right = await self._check_rectification_right(platform)
        erasure_right = await self._check_erasure_right(platform)
        portability_right = await self._check_portability_right(platform)

        rights_implemented = all([access_right, rectification_right, erasure_right, portability_right])
        status = 'pass' if rights_implemented else 'fail'
        severity = 'critical' if status == 'fail' else 'medium'

        return ComplianceCheck(
            check_id=f'{platform}_gdpr_rights',
            category='gdpr',
            requirement='data_subject_rights',
            status=status,
            severity=severity,
            description='Respect data subject rights (access, rectification, erasure, portability)',
            evidence={
                'access_right': access_right,
                'rectification_right': rectification_right,
                'erasure_right': erasure_right,
                'portability_right': portability_right
            },
            remediation='Implement all data subject rights in compliance with GDPR Article 15-20' if status == 'fail' else None,
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.check_intervals['quarterly']
        )

    # Helper methods for checks
    async def _check_firewall_configuration(self, platform: str) -> bool:
        """Check if firewall is properly configured"""
        # In production, this would check actual firewall configuration
        # For demo, check if firewall rules are documented
        firewall_key = f"compliance:{platform}:firewall_configured"
        return self.redis.get(firewall_key) == 'true'

    async def _check_data_encryption(self, platform: str) -> bool:
        """Check if cardholder data is encrypted"""
        # Check encryption configuration
        encryption_key = f"compliance:{platform}:data_encryption_enabled"
        return self.redis.get(encryption_key) == 'true'

    async def _check_tls_configuration(self, platform: str) -> bool:
        """Check TLS configuration"""
        # Check if TLS 1.2+ is enforced
        tls_key = f"compliance:{platform}:tls_12_plus_enabled"
        return self.redis.get(tls_key) == 'true'

    async def _check_audit_logging_enabled(self, platform: str) -> bool:
        """Check if audit logging is enabled"""
        logging_key = f"compliance:{platform}:audit_logging_enabled"
        return self.redis.get(logging_key) == 'true'

    async def _check_lawful_basis_documentation(self, platform: str) -> bool:
        """Check if lawful basis is documented"""
        basis_key = f"compliance:{platform}:lawful_basis_documented"
        return self.redis.get(basis_key) == 'true'

    async def _check_subject_access_right(self, platform: str) -> bool:
        """Check if subject access right is implemented"""
        access_key = f"compliance:{platform}:subject_access_implemented"
        return self.redis.get(access_key) == 'true'

    # Additional helper methods would be implemented for all checks

    def _calculate_compliance_score(self, checks: List[ComplianceCheck]) -> float:
        """Calculate overall compliance score"""
        if not checks:
            return 0.0

        total_weight = 0
        weighted_score = 0

        severity_weights = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }

        status_scores = {
            'pass': 1.0,
            'warning': 0.5,
            'fail': 0.0,
            'not_applicable': 1.0
        }

        for check in checks:
            weight = severity_weights.get(check.severity, 1)
            score = status_scores.get(check.status, 0.0)

            total_weight += weight
            weighted_score += (score * weight)

        return round((weighted_score / total_weight) * 100, 1) if total_weight > 0 else 0.0

    def _get_overall_status(self, checks: List[ComplianceCheck]) -> str:
        """Get overall compliance status"""
        critical_failures = [c for c in checks if c.severity == 'critical' and c.status == 'fail']
        high_failures = [c for c in checks if c.severity == 'high' and c.status == 'fail']

        if critical_failures:
            return 'non_compliant'
        elif high_failures:
            return 'at_risk'
        elif any(c.status == 'fail' for c in checks):
            return 'needs_attention'
        else:
            return 'compliant'

    def _generate_compliance_summary(self, checks: List[ComplianceCheck]) -> Dict[str, Any]:
        """Generate compliance summary statistics"""
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.status == 'pass'])
        failed_checks = len([c for c in checks if c.status == 'fail'])
        warning_checks = len([c for c in checks if c.status == 'warning'])

        critical_issues = len([c for c in checks if c.severity == 'critical' and c.status in ['fail', 'warning']])
        high_issues = len([c for c in checks if c.severity == 'high' and c.status in ['fail', 'warning']])

        return {
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'warning_checks': warning_checks,
            'pass_rate': round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0,
            'critical_issues': critical_issues,
            'high_issues': high_issues,
            'by_category': self._group_checks_by_category(checks),
            'by_severity': self._group_checks_by_severity(checks)
        }

    def _group_checks_by_category(self, checks: List[ComplianceCheck]) -> Dict[str, int]:
        """Group checks by category"""
        categories = {}
        for check in checks:
            categories[check.category] = categories.get(check.category, 0) + 1
        return categories

    def _group_checks_by_severity(self, checks: List[ComplianceCheck]) -> Dict[str, int]:
        """Group checks by severity"""
        severities = {}
        for check in checks:
            severities[check.severity] = severities.get(check.severity, 0) + 1
        return severities

    def _generate_recommendations(self, checks: List[ComplianceCheck]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        failed_checks = [c for c in checks if c.status == 'fail']
        warning_checks = [c for c in checks if c.status == 'warning']

        # Prioritize critical issues
        critical_failures = [c for c in failed_checks if c.severity == 'critical']
        if critical_failures:
            recommendations.append("URGENT: Address critical compliance failures immediately to avoid legal and financial penalties")

        # Group recommendations by category
        pci_failures = [c for c in failed_checks if c.category == 'pci_dss']
        if pci_failures:
            recommendations.append(f"PCI DSS: {len(pci_failures)} requirements need immediate attention")

        gdpr_failures = [c for c in failed_checks if c.category == 'gdpr']
        if gdpr_failures:
            recommendations.append(f"GDPR: {len(gdpr_failures)} requirements need to be addressed")

        # General recommendations
        if any(c.remediation for c in failed_checks):
            recommendations.append("Review detailed remediation steps for each failed check")

        if not recommendations:
            recommendations.append("Compliance status is good. Continue regular monitoring and updates.")

        return recommendations

    async def _store_compliance_results(self, platform: str, report: Dict[str, Any]):
        """Store compliance check results"""
        try:
            report_key = f"compliance_report:{platform}:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.redis.setex(report_key, 2592000, json.dumps(report))  # 30 days

            # Store latest report
            latest_key = f"compliance_latest:{platform}"
            self.redis.setex(latest_key, 2592000, json.dumps(report))

        except Exception as e:
            logger.error(f"Failed to store compliance results: {e}")

    async def create_data_processing_record(
        self,
        data_subject: str,
        data_categories: List[str],
        processing_purpose: str,
        legal_basis: str,
        retention_period: str
    ) -> str:
        """Create a GDPR data processing record"""
        record_id = f"dpr_{hashlib.md5(f'{data_subject}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:8]}"

        record = DataProcessingRecord(
            record_id=record_id,
            data_subject=data_subject,
            data_categories=data_categories,
            processing_purpose=processing_purpose,
            legal_basis=legal_basis,
            retention_period=retention_period,
            data_controllers=["Unified Projects"],
            data_processors=["Stripe", "Internal Systems"],
            created_at=datetime.utcnow(),
            consent_obtained=True,
            consent_withdrawn_at=None
        )

        # Store record
        record_key = f"dpr:{record_id}"
        self.redis.setex(record_key, 31536000, json.dumps(asdict(record)))  # 1 year

        return record_id

    async def log_audit_event(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an audit event for compliance"""
        entry_id = f"audit_{hashlib.md5(f'{user_id}_{action}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}"

        entry = AuditLogEntry(
            entry_id=entry_id,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details or {},
            compliance_flags=self._analyze_compliance_flags(action, resource, details)
        )

        # Store audit entry
        audit_key = f"audit:{entry_id}"
        self.redis.setex(audit_key, 31536000, json.dumps(asdict(entry)))  # 1 year

        # Add to audit log list
        audit_list_key = f"audit_log:{datetime.utcnow().strftime('%Y%m')}"
        self.redis.lpush(audit_list_key, entry_id)
        self.redis.ltrim(audit_list_key, 0, 9999)  # Keep last 10k entries
        self.redis.expire(audit_list_key, 7776000)  # 90 days

        return entry_id

    def _analyze_compliance_flags(self, action: str, resource: str, details: Dict[str, Any]) -> List[str]:
        """Analyze audit event for compliance flags"""
        flags = []

        # PCI DSS flags
        if 'payment' in resource.lower() or 'card' in resource.lower():
            flags.append('pci_dss_payment_data')

        if action in ['delete', 'export'] and 'user' in resource.lower():
            flags.append('gdpr_data_subject_right')

        if 'admin' in action.lower() or 'sudo' in action.lower():
            flags.append('privileged_access')

        return flags

    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get compliance dashboard data"""
        platforms = ['pinnacle_ai', 'free_ecommerce']

        dashboard = {
            'generated_at': datetime.utcnow().isoformat(),
            'platforms': {},
            'overall_score': 0,
            'critical_issues': 0,
            'recent_audit_events': []
        }

        total_score = 0
        platform_count = 0

        for platform in platforms:
            latest_report_key = f"compliance_latest:{platform}"
            report_data = self.redis.get(latest_report_key)

            if report_data:
                report = json.loads(report_data)
                dashboard['platforms'][platform] = {
                    'compliance_score': report['compliance_score'],
                    'overall_status': report['overall_status'],
                    'last_checked': report['generated_at'],
                    'critical_issues': report['summary']['critical_issues']
                }

                total_score += report['compliance_score']
                platform_count += 1
                dashboard['critical_issues'] += report['summary']['critical_issues']

        dashboard['overall_score'] = round(total_score / platform_count, 1) if platform_count > 0 else 0

        # Get recent audit events
        audit_list_key = f"audit_log:{datetime.utcnow().strftime('%Y%m')}"
        recent_audit_ids = self.redis.lrange(audit_list_key, 0, 9)  # Last 10 events

        for audit_id in recent_audit_ids:
            audit_data = self.redis.get(f"audit:{audit_id}")
            if audit_data:
                audit_entry = json.loads(audit_data)
                dashboard['recent_audit_events'].append({
                    'timestamp': audit_entry['timestamp'],
                    'action': audit_entry['action'],
                    'resource': audit_entry['resource'],
                    'user_id': audit_entry['user_id'],
                    'success': audit_entry['success']
                })

        return dashboard

# Global compliance engine instance
compliance_engine = ComplianceEngine()