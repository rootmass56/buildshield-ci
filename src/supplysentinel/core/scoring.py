from supplysentinel.core.constants import RiskLevel, Severity
from supplysentinel.core.models import Finding


SEVERITY_PENALTIES = {
    Severity.CRITICAL: 25,
    Severity.HIGH: 15,
    Severity.MEDIUM: 8,
    Severity.LOW: 3,
    Severity.INFO: 0,
}


def calculate_security_score(findings: list[Finding]) -> int:
    """
    Calculate a repository security score from 0 to 100.
    Higher severity findings reduce the score more.
    """
    penalty = sum(SEVERITY_PENALTIES.get(finding.severity, 0) for finding in findings)
    return max(0, 100 - penalty)


def derive_risk_level(score: int) -> RiskLevel:
    """
    Convert a numeric score into a risk level.
    """
    if score >= 85:
        return RiskLevel.LOW

    if score >= 70:
        return RiskLevel.MEDIUM

    if score >= 50:
        return RiskLevel.HIGH

    return RiskLevel.CRITICAL