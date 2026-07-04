def test_vulnerable_repo_detects_expected_supply_chain_findings(vulnerable_scan):
    rule_ids = {finding.rule_id for finding in vulnerable_scan.findings}

    expected_rule_ids = {
        "DG-NPM-001",
        "DG-NPM-002",
        "DG-NPM-003",
        "DG-NPM-004",
        "DG-PY-001",
        "DG-PY-002",
        "DG-PY-003",
        "DG-GHA-001",
        "DG-GHA-002",
        "DG-GHA-003",
        "DG-GHA-004",
        "DG-GHA-005",
    }

    assert expected_rule_ids.issubset(rule_ids)
    assert vulnerable_scan.summary.findings_count > 0
    assert vulnerable_scan.summary.security_score < 80
    assert vulnerable_scan.risk_profile.build_gate_status == "FAILED"


def test_secure_repo_has_no_findings(secure_scan):
    assert secure_scan.summary.findings_count == 0
    assert secure_scan.summary.security_score == 100
    assert secure_scan.summary.risk_level.value == "LOW"
    assert secure_scan.risk_profile.build_gate_status == "PASSED"
    assert secure_scan.findings == []