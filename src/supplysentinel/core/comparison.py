from supplysentinel.core.models import ComparisonResult, ScanResult


def calculate_risk_reduction_percentage(
    baseline_score: int,
    target_score: int,
) -> float:
    """
    Calculate how much risk was reduced between baseline and target.

    Risk is calculated as:
    risk = 100 - security_score
    """
    baseline_risk = 100 - baseline_score
    target_risk = 100 - target_score

    if baseline_risk <= 0:
        return 0.0

    reduction = ((baseline_risk - target_risk) / baseline_risk) * 100
    return round(max(0.0, reduction), 2)


def derive_comparison_verdict(
    baseline: ScanResult,
    target: ScanResult,
    score_delta: int,
    findings_reduced: int,
) -> str:
    """
    Derive a human-readable verdict for before/after comparison.
    """
    if (
        score_delta > 0
        and target.summary.security_score >= 85
        and target.risk_profile.build_gate_status == "PASSED"
    ):
        return "SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED"

    if score_delta > 0 and findings_reduced > 0:
        return "SECURITY_POSTURE_PARTIALLY_IMPROVED"

    if score_delta == 0:
        return "NO_MEASURABLE_SECURITY_CHANGE"

    return "SECURITY_POSTURE_REGRESSED"


def build_comparison_result(
    baseline: ScanResult,
    target: ScanResult,
    baseline_label: str = "Baseline Repository",
    target_label: str = "Target Repository",
) -> ComparisonResult:
    """
    Build complete before/after comparison result.
    """
    score_delta = target.summary.security_score - baseline.summary.security_score
    findings_reduced = baseline.summary.findings_count - target.summary.findings_count

    risk_reduction_percentage = calculate_risk_reduction_percentage(
        baseline_score=baseline.summary.security_score,
        target_score=target.summary.security_score,
    )

    verdict = derive_comparison_verdict(
        baseline=baseline,
        target=target,
        score_delta=score_delta,
        findings_reduced=findings_reduced,
    )

    return ComparisonResult(
        baseline_label=baseline_label,
        target_label=target_label,
        baseline=baseline,
        target=target,
        score_delta=score_delta,
        findings_reduced=findings_reduced,
        risk_reduction_percentage=risk_reduction_percentage,
        verdict=verdict,
    )