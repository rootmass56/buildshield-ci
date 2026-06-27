from collections import defaultdict

from supplysentinel.core.constants import FindingCategory, RiskLevel, Severity
from supplysentinel.core.models import (
    CategoryRisk,
    Finding,
    RiskProfile,
    TopRiskDriver,
)


SEVERITY_BASE_WEIGHTS = {
    Severity.CRITICAL: 30.0,
    Severity.HIGH: 18.0,
    Severity.MEDIUM: 8.0,
    Severity.LOW: 3.0,
    Severity.INFO: 0.0,
}


CONFIDENCE_MULTIPLIERS = {
    "HIGH": 1.0,
    "MEDIUM": 0.8,
    "LOW": 0.5,
}


CATEGORY_PENALTY_CAPS = {
    FindingCategory.DEPENDENCY: 35.0,
    FindingCategory.REGISTRY: 35.0,
    FindingCategory.CICD: 30.0,
    FindingCategory.SECRETS: 35.0,
    FindingCategory.BUILD_SCRIPT: 25.0,
    FindingCategory.CONTAINER: 20.0,
    FindingCategory.POLICY: 20.0,
}


def get_confidence_multiplier(confidence: str) -> float:
    """
    Convert confidence text into a scoring multiplier.
    """
    return CONFIDENCE_MULTIPLIERS.get(confidence.upper(), 0.8)


def calculate_finding_contribution(finding: Finding) -> float:
    """
    Calculate how much one finding contributes to risk.
    """
    severity_weight = SEVERITY_BASE_WEIGHTS.get(finding.severity, 0.0)
    confidence_multiplier = get_confidence_multiplier(finding.confidence)

    return round(severity_weight * confidence_multiplier, 2)


def derive_security_risk_level(score: int) -> RiskLevel:
    """
    Convert overall security score into risk level.
    Higher score means safer repository.
    """
    if score >= 85:
        return RiskLevel.LOW

    if score >= 70:
        return RiskLevel.MEDIUM

    if score >= 50:
        return RiskLevel.HIGH

    return RiskLevel.CRITICAL


def derive_category_risk_level(risk_score: int) -> RiskLevel:
    """
    Convert category risk score into risk level.
    Higher score means more dangerous category.
    """
    if risk_score >= 80:
        return RiskLevel.CRITICAL

    if risk_score >= 60:
        return RiskLevel.HIGH

    if risk_score >= 30:
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def calculate_security_score(findings: list[Finding]) -> int:
    """
    Backward-compatible overall score calculation.
    """
    risk_profile = calculate_risk_profile(findings)
    return risk_profile.overall_security_score


def derive_risk_level(score: int) -> RiskLevel:
    """
    Backward-compatible risk level derivation.
    """
    return derive_security_risk_level(score)


def calculate_category_risks(findings: list[Finding]) -> list[CategoryRisk]:
    """
    Calculate risk score per finding category.
    """
    category_penalties: dict[FindingCategory, float] = defaultdict(float)
    category_counts: dict[FindingCategory, int] = defaultdict(int)

    for finding in findings:
        category_counts[finding.category] += 1
        category_penalties[finding.category] += calculate_finding_contribution(finding)

    category_risks: list[CategoryRisk] = []

    for category, raw_penalty in category_penalties.items():
        cap = CATEGORY_PENALTY_CAPS.get(category, 20.0)
        capped_penalty = min(raw_penalty, cap)
        risk_score = int(round((capped_penalty / cap) * 100))

        category_risks.append(
            CategoryRisk(
                category=category,
                finding_count=category_counts[category],
                penalty_points=round(capped_penalty, 2),
                risk_score=risk_score,
                risk_level=derive_category_risk_level(risk_score),
            )
        )

    return sorted(
        category_risks,
        key=lambda item: item.risk_score,
        reverse=True,
    )


def calculate_top_risk_drivers(
    findings: list[Finding],
    limit: int = 5,
) -> list[TopRiskDriver]:
    """
    Identify the most important findings driving risk.
    """
    ranked_findings = sorted(
        findings,
        key=calculate_finding_contribution,
        reverse=True,
    )

    top_drivers: list[TopRiskDriver] = []

    for finding in ranked_findings[:limit]:
        top_drivers.append(
            TopRiskDriver(
                rule_id=finding.rule_id,
                title=finding.title,
                severity=finding.severity,
                category=finding.category,
                file_path=finding.evidence.file_path,
                line_number=finding.evidence.line_number,
                contribution_points=calculate_finding_contribution(finding),
            )
        )

    return top_drivers


def evaluate_build_gate(
    findings: list[Finding],
    security_score: int,
) -> tuple[str, str]:
    """
    Decide whether a build should pass, warn, or fail.
    """
    has_critical = any(finding.severity == Severity.CRITICAL for finding in findings)
    high_count = sum(1 for finding in findings if finding.severity == Severity.HIGH)

    if has_critical:
        return (
            "FAILED",
            "Critical security finding detected. Build should not proceed without review.",
        )

    if security_score < 70:
        return (
            "FAILED",
            "Security score is below the minimum safe threshold of 70.",
        )

    if high_count >= 3:
        return (
            "FAILED",
            "Multiple high-severity findings detected.",
        )

    if security_score < 85:
        return (
            "WARNING",
            "Security score is acceptable but improvements are recommended.",
        )

    return (
        "PASSED",
        "No blocking supply-chain risk detected.",
    )


def calculate_risk_profile(findings: list[Finding]) -> RiskProfile:
    """
    Calculate complete advanced risk profile for a repository.
    """
    category_risks = calculate_category_risks(findings)

    total_capped_penalty = sum(
        category_risk.penalty_points for category_risk in category_risks
    )

    # Cap overall penalty at 95 so a vulnerable repo still shows measurable score.
    # This is useful for before/after comparison instead of always showing 0.
    overall_penalty = min(total_capped_penalty, 95.0)
    overall_security_score = int(max(0, 100 - overall_penalty))

    overall_risk_level = derive_security_risk_level(overall_security_score)

    build_gate_status, build_gate_reason = evaluate_build_gate(
        findings=findings,
        security_score=overall_security_score,
    )

    return RiskProfile(
        overall_security_score=overall_security_score,
        overall_risk_level=overall_risk_level,
        build_gate_status=build_gate_status,
        build_gate_reason=build_gate_reason,
        category_risks=category_risks,
        top_risk_drivers=calculate_top_risk_drivers(findings),
    )