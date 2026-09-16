from __future__ import annotations

import json
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "1.0.0"
HISTORICAL_H9_VERSION = "0.12.7"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_h10b_python_release_identity_is_frozen() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    init_text = (
        ROOT / "src" / "supplysentinel" / "__init__.py"
    ).read_text(encoding="utf-8")

    assert pyproject["project"]["version"] == RELEASE_VERSION
    assert "Development Status :: 5 - Production/Stable" in (
        pyproject["project"]["classifiers"]
    )
    assert '__version__ = "1.0.0"' in init_text


def test_h10b_frontend_package_and_lock_share_release_identity() -> None:
    package = _json(ROOT / "frontend" / "package.json")
    lock = _json(ROOT / "frontend" / "package-lock.json")

    assert package["version"] == RELEASE_VERSION
    assert lock["version"] == RELEASE_VERSION
    assert lock["packages"][""]["version"] == RELEASE_VERSION
    assert package["packageManager"] == "npm@12.0.2"


def test_h10b_sbom_root_component_is_release_candidate() -> None:
    sbom = _json(ROOT / "sbom" / "cyclonedx-python.json")
    root = sbom["metadata"]["component"]

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert root["name"] == "buildshield-ci"
    assert root["version"] == RELEASE_VERSION
    assert root["bom-ref"] == "root-component"

    components = sbom["components"]
    dependencies = sbom["dependencies"]
    root_entry = next(
        item for item in dependencies
        if item["ref"] == "root-component"
    )

    assert len(components) == 26
    assert len(dependencies) == 27
    assert len(root_entry["dependsOn"]) == 6
    assert sum(
        len(item.get("dependsOn", []))
        for item in dependencies
    ) == 42


def test_h10b_hosted_ci_expects_release_candidate_sbom_version() -> None:
    workflow = (
        ROOT / ".github" / "workflows" / "buildshield-ci.yml"
    ).read_text(encoding="utf-8")

    assert 'root["version"] != "1.0.0"' in workflow
    assert 'root["version"] != "0.12.7"' not in workflow
    assert workflow.count("cyclonedx-py environment") == 2


def test_h10b_current_release_docs_expose_candidate_not_final_tag() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    deployment = (
        ROOT / "docs" / "deployment.md"
    ).read_text(encoding="utf-8")
    blueprint = (
        ROOT / "docs" / "final-blueprint.md"
    ).read_text(encoding="utf-8")
    release_doc = (
        ROOT / "docs" / "h10-release-candidate.md"
    ).read_text(encoding="utf-8")

    assert "Current H10 release candidate" in readme
    assert "BuildShield-CI version: 1.0.0" in readme
    assert '"version": "1.0.0"' in deployment
    assert "## H10B — v1.0.0 Release-Candidate Freeze" in blueprint
    assert "Status: COMPLETE LOCALLY." in blueprint
    assert "## H10C — Final Portfolio / Demo / Documentation Closure" in blueprint
    assert "## H10D — Final Release Acceptance" in blueprint
    assert "Historical evidence boundary" in release_doc
    assert "No H10 checkpoint commit is created in H10B" in release_doc
    assert "No final tag or release has been created" in release_doc


def test_h10b_preserves_h9_historical_product_versions() -> None:
    h9c = _json(ROOT / "evaluation" / "h9c-baseline-metrics-v1.json")
    h9d = _json(ROOT / "evaluation" / "h9d-final-metrics-v1.json")
    design = _json(ROOT / "evaluation" / "corpus-design-v1.json")

    assert h9c["product_version"] == HISTORICAL_H9_VERSION
    assert h9d["product_version"] == HISTORICAL_H9_VERSION
    assert design["product_version_during_h9"] == HISTORICAL_H9_VERSION


def test_h10b_dependency_locks_remain_unchanged_release_inputs() -> None:
    requirements = (
        ROOT / "requirements" / "README.md"
    ).read_text(encoding="utf-8")

    assert "release-candidate project version at `1.0.0`" in requirements
    assert "dependency versions in these H8-generated lock files are unchanged" in requirements

    for name in (
        "runtime-py313-windows.lock.txt",
        "runtime-py313-linux.lock.txt",
        "dev-py313-linux.lock.txt",
    ):
        text = (ROOT / "requirements" / name).read_text(
            encoding="utf-8"
        )
        assert "--hash=sha256:" in text


def test_h10b_does_not_reintroduce_h10a_removed_residue() -> None:
    assert not (
        ROOT / "src" / "supplysentinel" / "parsers"
    ).exists()
    assert not (
        ROOT / "src" / "supplysentinel" / "web" / "static"
    ).exists()

    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)

    package_data = (
        pyproject.get("tool", {})
        .get("setuptools", {})
        .get("package-data", {})
    )
    assert "supplysentinel" not in package_data
