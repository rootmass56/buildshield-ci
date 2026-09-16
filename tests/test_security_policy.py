from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_security_policy_exists_and_defines_reporting_scope() -> None:
    policy = project_root() / "SECURITY.md"

    assert policy.exists()

    content = policy.read_text(encoding="utf-8-sig")

    assert "# Security Policy" in content
    assert "## Reporting a Vulnerability" in content
    assert "## Safe Research Expectations" in content
    assert "## Security Model and Limitations" in content


def test_security_policy_marks_vulnerable_fixture_as_intentional() -> None:
    content = (project_root() / "SECURITY.md").read_text(
        encoding="utf-8-sig"
    )

    assert "samples/vulnerable-repo" in content
    assert "intentionally insecure" in content
    assert "expected demonstration findings" in content


def test_security_policy_does_not_claim_enterprise_hardening() -> None:
    content = (project_root() / "SECURITY.md").read_text(
        encoding="utf-8-sig"
    )

    assert "Enterprise or organization-wide deployment would require additional controls" in content
    assert "does not claim to provide complete vulnerability coverage" in content


def test_readme_marks_controlled_vulnerable_sample_as_intentional() -> None:
    readme = (project_root() / "README.md").read_text(
        encoding="utf-8-sig"
    )

    assert "samples/vulnerable-repo" in readme
    assert "Controlled vulnerable-to-hardened benchmark" in readme
    assert "checked-in controlled fixtures" in readme
    assert "not a universal security guarantee" in readme
