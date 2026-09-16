from __future__ import annotations

import json
from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load_json(relative: str) -> dict:
    return json.loads(read(relative))


def test_h10d_release_identity_is_consistently_1_0_0() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    init_text = read("src/supplysentinel/__init__.py")
    package = load_json("frontend/package.json")
    lock = load_json("frontend/package-lock.json")
    sbom = load_json("sbom/cyclonedx-python.json")

    assert pyproject["project"]["version"] == "1.0.0"
    assert '__version__ = "1.0.0"' in init_text
    assert package["version"] == "1.0.0"
    assert lock["version"] == "1.0.0"
    assert lock["packages"][""]["version"] == "1.0.0"
    assert sbom["metadata"]["component"]["version"] == "1.0.0"


def test_h10d_dockerfile_preserves_release_runtime_contract() -> None:
    dockerfile = read("Dockerfile")

    assert dockerfile.startswith("FROM node:22.23.2-bookworm-slim")
    assert "npm install --global npm@12.0.2" in dockerfile
    assert "FROM python:3.13-slim AS runtime" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "STOPSIGNAL SIGTERM" in dockerfile
    assert "http://127.0.0.1:8080/ready" in dockerfile
    assert 'CMD ["buildshield", "dashboard"' in dockerfile


def test_h10d_compose_preserves_least_privilege_contract() -> None:
    compose = read("docker-compose.yml")

    for expected in (
        'user: "10001:10001"',
        "read_only: true",
        "cap_drop:",
        "- ALL",
        "no-new-privileges:true",
        "pids_limit: 256",
        "stop_grace_period: 15s",
        '127.0.0.1:${BUILDSHIELD_HOST_PORT:-8080}:8080',
        "/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777",
        'BUILDSHIELD_ENV: "production"',
        'BUILDSHIELD_WORKSPACE_ROOT: "/app"',
        "BUILDSHIELD_ADMIN_USERNAME",
        "BUILDSHIELD_ADMIN_PASSWORD_HASH",
    ):
        assert expected in compose


def test_h10d_hosted_ci_remains_release_quality_gate() -> None:
    workflow = read(".github/workflows/buildshield-ci.yml")

    assert 'node-version: "22.23.2"' in workflow
    assert "npm install --global npm@12.0.2" in workflow
    assert 'root["version"] != "1.0.0"' in workflow
    assert "Run Ruff" in workflow
    assert "Run mypy typed-boundary gate" in workflow
    assert "Run pytest with branch coverage" in workflow
    assert "Regenerate and verify CycloneDX 1.6 runtime SBOM" in workflow
    assert "Controlled Security Gate / Reports" in workflow

    for match in re.findall(
        r"uses:\s*[^@\s]+@([0-9a-fA-F]+)",
        workflow,
    ):
        assert len(match) == 40


def test_h10d_historical_h9_evidence_remains_immutable() -> None:
    h9c = load_json("evaluation/h9c-baseline-metrics-v1.json")
    h9d = load_json("evaluation/h9d-final-metrics-v1.json")

    assert h9c["product_version"] == "0.12.7"
    assert h9d["product_version"] == "0.12.7"
    assert h9d["confusion_matrix"] == {
        "tp": 51,
        "tn": 49,
        "fp": 0,
        "fn": 0,
    }
    assert h9d["claim_boundary"].startswith(
        "Metrics describe only the curated deterministic H9 corpus"
    )


def test_h10d_release_docs_record_local_pass_without_claiming_release() -> None:
    blueprint = read("docs/final-blueprint.md")
    acceptance = read("docs/h10-final-release-acceptance.md")

    assert "H10D FINAL RELEASE ACCEPTANCE" in blueprint
    assert "LOCAL RELEASE ACCEPTANCE COMPLETE — H10 CHECKPOINT/HOSTED CI RELEASE SEQUENCE" in blueprint
    assert "LOCAL RELEASE ACCEPTANCE: PASS" in acceptance
    assert "single H10 checkpoint" in acceptance
    assert "merge, tag and GitHub release remain deferred pending hosted CI" in acceptance
    assert "Passing local H10D validation does not itself release v1.0.0" in acceptance
    assert "294 passed, 2 skipped" in acceptance


def test_h10d_h10c_validation_evidence_is_recorded() -> None:
    blueprint = read("docs/final-blueprint.md")
    acceptance = read("docs/h10-final-release-acceptance.md")

    assert "full Windows Python regression: 286 passed, 2 skipped" in blueprint
    assert "H10C Windows regression: 286 passed, 2 skipped" in acceptance
    assert "H10C — Final Portfolio / Demo / Documentation Closure" in blueprint
    assert "Status: COMPLETE LOCALLY." in blueprint


def test_h10d_removed_legacy_residue_stays_absent() -> None:
    assert not (ROOT / "src" / "supplysentinel" / "parsers").exists()
    assert not (ROOT / "src" / "supplysentinel" / "web" / "static").exists()

    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    package_data = (
        pyproject.get("tool", {})
        .get("setuptools", {})
        .get("package-data", {})
    )
    assert "supplysentinel" not in package_data
