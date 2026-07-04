from supplysentinel.core.comparison import build_comparison_result


def test_comparison_engine_detects_security_improvement(
    vulnerable_scan,
    secure_scan,
):
    comparison = build_comparison_result(
        baseline=vulnerable_scan,
        target=secure_scan,
        baseline_label="Vulnerable Repo",
        target_label="Secure Repo",
    )

    assert comparison.score_delta > 0
    assert comparison.findings_reduced > 0
    assert comparison.risk_reduction_percentage > 0
    assert comparison.target.summary.security_score > comparison.baseline.summary.security_score
    assert comparison.target.risk_profile.build_gate_status == "PASSED"