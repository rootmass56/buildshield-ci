from __future__ import annotations

from collections import Counter
from pathlib import Path

from supplysentinel.analyzers import (
    dockerfile_analyzer,
    github_actions_analyzer,
    npm_analyzer,
    python_analyzer,
)
from supplysentinel.core import scanner
from supplysentinel.core.scanner import (
    discover_security_relevant_files,
    run_all_analyzers,
    scan_repository,
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def vulnerable_repo() -> Path:
    return project_root() / "samples" / "vulnerable-repo"


def secure_repo() -> Path:
    return project_root() / "samples" / "secure-repo"


def test_dedicated_npm_analyzer_detects_expected_vulnerable_fixture_rules() -> None:
    target = vulnerable_repo()
    discovered_files = discover_security_relevant_files(target)

    findings = npm_analyzer.analyze_npm(
        target_path=target,
        discovered_files=discovered_files,
    )

    distribution = Counter(finding.rule_id for finding in findings)

    assert len(findings) == 7
    assert distribution == Counter(
        {
            "DG-NPM-001": 1,
            "DG-NPM-002": 4,
            "DG-NPM-003": 1,
            "DG-NPM-004": 1,
        }
    )


def test_dedicated_github_actions_analyzer_detects_expected_fixture_rules() -> None:
    target = vulnerable_repo()
    discovered_files = discover_security_relevant_files(target)

    findings = github_actions_analyzer.analyze_github_actions(
        discovered_files=discovered_files,
    )

    distribution = Counter(finding.rule_id for finding in findings)

    assert len(findings) == 5
    assert distribution == Counter(
        {
            "DG-GHA-001": 1,
            "DG-GHA-002": 1,
            "DG-GHA-003": 1,
            "DG-GHA-004": 1,
            "DG-GHA-005": 1,
        }
    )


def test_scanner_dispatches_through_explicit_analyzer_interfaces(
    monkeypatch,
) -> None:
    calls = {
        "npm": 0,
        "python": 0,
        "github_actions": 0,
        "dockerfile": 0,
    }

    def fake_npm(*, target_path, discovered_files):
        calls["npm"] += 1
        return []

    def fake_python(*, target_path, discovered_files):
        calls["python"] += 1
        return []

    def fake_github_actions(*, discovered_files):
        calls["github_actions"] += 1
        return []

    def fake_dockerfile(*, target_path, discovered_files):
        calls["dockerfile"] += 1
        return []

    monkeypatch.setattr(npm_analyzer, "analyze_npm", fake_npm)
    monkeypatch.setattr(
        python_analyzer,
        "analyze_python_security",
        fake_python,
    )
    monkeypatch.setattr(
        github_actions_analyzer,
        "analyze_github_actions",
        fake_github_actions,
    )
    monkeypatch.setattr(
        dockerfile_analyzer,
        "analyze_dockerfile_security",
        fake_dockerfile,
    )

    run_all_analyzers(
        target_path=vulnerable_repo(),
        discovered_files=[],
    )

    assert calls == {
        "npm": 1,
        "python": 1,
        "github_actions": 1,
        "dockerfile": 1,
    }


def test_legacy_dynamic_and_fallback_analyzer_routing_is_removed() -> None:
    assert not hasattr(scanner, "call_known_analyzer")
    assert not hasattr(scanner, "fallback_npm_analyzer")
    assert not hasattr(scanner, "fallback_github_actions_analyzer")


def test_controlled_vulnerable_to_secure_benchmark_is_preserved() -> None:
    vulnerable_result = scan_repository(str(vulnerable_repo()))
    secure_result = scan_repository(str(secure_repo()))

    vulnerable_summary = vulnerable_result.summary
    secure_summary = secure_result.summary

    assert vulnerable_summary.files_discovered == 5
    assert vulnerable_summary.files_scanned == 5
    assert vulnerable_summary.findings_count == 22
    assert vulnerable_summary.critical_count == 4
    assert vulnerable_summary.high_count == 10
    assert vulnerable_summary.medium_count == 7
    assert vulnerable_summary.low_count == 1
    assert vulnerable_summary.info_count == 0
    assert vulnerable_summary.security_score == 5
    assert str(vulnerable_summary.risk_level).endswith("CRITICAL")
    assert str(vulnerable_result.risk_profile.build_gate_status).endswith("FAILED")

    assert secure_summary.files_discovered == 7
    assert secure_summary.files_scanned == 7
    assert secure_summary.findings_count == 0
    assert secure_summary.critical_count == 0
    assert secure_summary.high_count == 0
    assert secure_summary.medium_count == 0
    assert secure_summary.low_count == 0
    assert secure_summary.info_count == 0
    assert secure_summary.security_score == 100
    assert str(secure_summary.risk_level).endswith("LOW")
    assert str(secure_result.risk_profile.build_gate_status).endswith("PASSED")
