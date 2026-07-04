from supplysentinel.policies.policy_engine import evaluate_policy


def test_vulnerable_repo_fails_policy(vulnerable_scan, policy_file):
    evaluation = evaluate_policy(
        result=vulnerable_scan,
        policy_path=str(policy_file),
    )

    violation_ids = {violation.policy_id for violation in evaluation.violations}

    assert evaluation.passed is False
    assert evaluation.actual_score == vulnerable_scan.summary.security_score
    assert "POLICY-MIN-SCORE" in violation_ids
    assert "POLICY-FAIL-ON-CRITICAL" in violation_ids
    assert len(evaluation.violations) > 0


def test_secure_repo_passes_policy(secure_scan, policy_file):
    evaluation = evaluate_policy(
        result=secure_scan,
        policy_path=str(policy_file),
    )

    assert evaluation.passed is True
    assert evaluation.actual_score == 100
    assert evaluation.violations == []