from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_h10c_key_documentation_exists() -> None:
    for relative in (
        "README.md",
        "SECURITY.md",
        "docs/final-project-summary.md",
        "docs/final-report.md",
        "docs/demo-script.md",
        "docs/interview-explanation.md",
        "docs/resume-points.md",
        "docs/screenshots-checklist.md",
        "docs/final-submission-checklist.md",
        "docs/h10-portfolio-closure.md",
    ):
        assert (ROOT / relative).is_file(), relative


def test_readme_has_complete_static_rule_inventory_and_current_validation() -> None:
    text = read("README.md")
    for rule in (
        "DG-NPM-001", "DG-NPM-002", "DG-NPM-003", "DG-NPM-004",
        "DG-PY-001", "DG-PY-002", "DG-PY-003",
        "DG-GHA-001", "DG-GHA-002", "DG-GHA-003", "DG-GHA-004", "DG-GHA-005",
        "DG-DOCKER-001", "DG-DOCKER-002", "DG-DOCKER-003", "DG-DOCKER-004",
        "DG-DOCKER-005", "DG-DOCKER-006", "DG-DOCKER-007", "DG-DOCKER-008",
    ):
        assert rule in text
    assert "295 passed, 2 skipped" in text
    assert "release candidate" in text.lower()


def test_project_summary_preserves_benchmark_and_h9_claim_boundary() -> None:
    text = read("docs/final-project-summary.md")
    assert "22 findings" in text
    assert "0 findings" in text
    assert "41 TP / 45 TN / 4 FP / 10 FN" in text
    assert "51 TP / 49 TN / 0 FP / 0 FN" in text
    assert "not be presented as 100% real-world detection accuracy" in text
    assert "295 passed, 2 skipped" in text


def test_demo_script_uses_production_safe_compose_flow() -> None:
    text = read("docs/demo-script.md")
    assert "hash_password" in text
    assert "BUILDSHIELD_ADMIN_PASSWORD_HASH" in text
    assert "/ready" in text
    assert "docker compose up --build -d" in text
    assert "docker run -d --name buildshield-ci-test" not in text
    assert "295 passed, 2 skipped" in text


def test_interview_and_resume_language_is_defensible() -> None:
    interview = read("docs/interview-explanation.md")
    resume = read("docs/resume-points.md")
    assert "0.854167" in interview
    assert "1.0 on that fixed corpus" in interview
    assert "295 passed, 2 skipped" in interview
    assert "React" in resume and "TypeScript" in resume
    assert "100% accurate" in resume
    assert "Do not shorten it" in resume


def test_screenshot_and_submission_checklists_match_release_stage() -> None:
    screenshots = read("docs/screenshots-checklist.md")
    submission = read("docs/final-submission-checklist.md")
    assert "295 passed, 2 skipped" in screenshots
    assert "v1.0.0` tag/release page **after H10D only**" in screenshots
    assert "H10B v1.0.0 release-candidate freeze locally validated" in submission
    assert "Final Release Actions - Remaining" in submission


def test_h10b_release_candidate_document_records_validation_closure() -> None:
    text = read("docs/h10-release-candidate.md")
    assert "COMPLETE LOCALLY" in text
    assert "276 passed, 2 skipped" in text
    assert "Node 22.23.2 / npm 12.0.2" in text
    assert "No final tag or release has been created" in text


def test_blueprint_records_h10c_complete_and_h10d_local_acceptance() -> None:
    text = read("docs/final-blueprint.md")
    assert "POST-CHECKPOINT UI/REALISTIC-DEMO/SANITATION COMPLETE" in text
    assert "## H10C — Final Portfolio / Demo / Documentation Closure" in text
    assert "## H10D — Final Release Acceptance" in text
    assert "Status: COMPLETE LOCALLY." in text
    assert "replacement final checkpoint" in text.lower()
    assert "295 passed, 2 skipped" in text


def test_security_positioning_remains_single_instance_scoped() -> None:
    security = read("SECURITY.md")
    closure = read("docs/h10-portfolio-closure.md")
    assert "validated v1.0.0 release candidate" in security
    assert "controlled single-instance" in security
    assert "not enterprise multi-tenant SaaS" in closure


def test_historical_h9_version_evidence_remains_immutable() -> None:
    metrics = json.loads(
        (ROOT / "evaluation/h9d-final-metrics-v1.json").read_text(encoding="utf-8")
    )
    design = json.loads(
        (ROOT / "evaluation/corpus-design-v1.json").read_text(encoding="utf-8")
    )
    assert metrics["product_version"] == "0.12.7"
    assert design["product_version_during_h9"] == "0.12.7"
