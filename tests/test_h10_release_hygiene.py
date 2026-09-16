from __future__ import annotations

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_h10b_freezes_release_version() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    assert pyproject["project"]["version"] == "1.0.0"


def test_h10a_removes_obsolete_legacy_frontend_package_data() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    setuptools = pyproject.get("tool", {}).get("setuptools", {})
    package_data = setuptools.get("package-data", {})

    assert "supplysentinel" not in package_data
    assert not (ROOT / "src" / "supplysentinel" / "web" / "static").exists()


def test_h10a_removes_empty_parser_scaffolding() -> None:
    assert not (ROOT / "src" / "supplysentinel" / "parsers").exists()


def test_h10a_removes_unused_core_scaffolding() -> None:
    constants = (
        ROOT / "src" / "supplysentinel" / "core" / "constants.py"
    ).read_text(encoding="utf-8")
    exceptions = (
        ROOT / "src" / "supplysentinel" / "core" / "exceptions.py"
    ).read_text(encoding="utf-8")

    assert "SECURITY_RELEVANT_FILENAMES" not in constants
    assert "InvalidTargetError" not in exceptions
    assert "ScannerExecutionError" not in exceptions
    assert "class SupplySentinelError" in exceptions


def test_h10a_line_ending_policy_covers_release_fixture_types() -> None:
    attributes = (ROOT / ".gitattributes").read_text(
        encoding="utf-8-sig"
    )

    required = {
        ".npmrc text eol=lf",
        ".pypirc text eol=lf",
        "*.conf text eol=lf",
        "*.ts text eol=lf",
        "*.tsx text eol=lf",
        "*.tgz -text",
    }

    for rule in required:
        assert rule in attributes


def test_canonical_docs_drop_stale_pre_hardening_and_pending_release_language() -> None:
    canonical = [
        ROOT / "README.md",
        ROOT / "SECURITY.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "final-blueprint.md",
        ROOT / "docs" / "final-project-summary.md",
        ROOT / "docs" / "final-report.md",
        ROOT / "docs" / "final-submission-checklist.md",
        ROOT / "docs" / "demo-script.md",
        ROOT / "docs" / "interview-explanation.md",
        ROOT / "docs" / "screenshots-checklist.md",
    ]

    forbidden = {
        "57 passed",
        "57 passing tests",
        "not yet the final tagged release",
        "replacement final checkpoint and hosted-CI pass remain required",
        "Only the final replacement checkpoint/hosted-CI",
        "project remains a release candidate until",
    }

    for path in canonical:
        content = path.read_text(encoding="utf-8-sig")
        for phrase in forbidden:
            assert phrase not in content, f"{path}: {phrase}"


def test_canonical_docs_do_not_claim_completed_security_work_is_pending() -> None:
    canonical = [
        ROOT / "README.md",
        ROOT / "SECURITY.md",
        ROOT / "docs" / "architecture.md",
        ROOT / "docs" / "final-report.md",
        ROOT / "docs" / "final-submission-checklist.md",
    ]

    forbidden = {
        "H1 has not started yet",
        "API authentication/authorization is not yet implemented",
        "Dashboard rendering still requires final XSS/browser-security hardening",
        "Request/resource controls and safe public error handling require hardening",
    }

    for path in canonical:
        content = path.read_text(encoding="utf-8-sig")
        for phrase in forbidden:
            assert phrase not in content


def test_readme_reflects_current_stack_release_and_historical_audit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8-sig")

    assert "React 19, TypeScript 7, Vite 8" in readme
    assert "295 passed, 2 skipped" in readme
    assert "Current released version: `v1.0.0`" in readme
    assert "dec7eea405cd474fdea73bacd8f9847782887816" in readme

    audit = (ROOT / "docs" / "h10-final-audit.md").read_text(encoding="utf-8")
    assert "268 passed, 2 skipped" in audit
    assert "51 TP / 49 TN / 0 FP / 0 FN" in audit
    assert "not a real-world detection-accuracy claim" in audit


def test_h10a_preserves_h9_claim_boundary() -> None:
    audit = (ROOT / "docs" / "h10-final-audit.md").read_text(
        encoding="utf-8"
    )
    metrics = (
        ROOT / "evaluation" / "h9d-final-metrics-v1.json"
    ).read_text(encoding="utf-8")

    assert "51 TP / 49 TN / 0 FP / 0 FN" in audit
    assert "not a real-world detection-accuracy claim" in audit
    assert (
        "not estimates of real-world detection accuracy"
        in metrics
    )
