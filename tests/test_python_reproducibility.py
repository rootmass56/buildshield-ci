from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = PROJECT_ROOT / "requirements"
SBOM = PROJECT_ROOT / "sbom" / "cyclonedx-python.json"


def _read_lock(name: str) -> str:
    return (REQUIREMENTS / name).read_text(encoding="utf-8")


def test_h8b_runtime_locks_are_hash_pinned_and_not_editable():
    for name in (
        "runtime-py313-windows.lock.txt",
        "runtime-py313-linux.lock.txt",
    ):
        content = _read_lock(name)

        assert "--hash=sha256:" in content
        assert "-e " not in content
        assert "--editable" not in content
        assert "file://" not in content.lower()

        normalized = content.lower()

        for dependency in (
            "fastapi==",
            "pydantic==",
            "pyyaml==",
            "rich==",
            "typer==",
        ):
            assert dependency in normalized

        assert (
            "uvicorn==" in normalized
            or "uvicorn[standard]==" in normalized
        )


def test_h8b_linux_dev_lock_contains_quality_toolchain():
    content = _read_lock("dev-py313-linux.lock.txt").lower()

    assert "--hash=sha256:" in content

    for dependency in (
        "build==",
        "cyclonedx-bom==7.4.0",
        "mypy==",
        "pip-tools==7.6.1",
        "pytest-cov==",
        "ruff==",
    ):
        assert dependency in content


def test_h8d2_cyclonedx_sbom_metadata_runtime_components_and_graph():
    payload = json.loads(SBOM.read_text(encoding="utf-8"))

    assert payload["bomFormat"] == "CycloneDX"
    assert payload["specVersion"] == "1.6"

    root = payload["metadata"]["component"]
    assert root["name"] == "buildshield-ci"
    assert root["version"] == "0.12.7"
    assert root["bom-ref"] == "root-component"

    components = payload.get("components", [])
    component_by_ref = {
        item["bom-ref"]: item
        for item in components
        if isinstance(item, dict) and item.get("bom-ref")
    }
    component_names = {
        item["name"].lower()
        for item in components
        if isinstance(item, dict) and "name" in item
    }

    expected_runtime = {
        "fastapi",
        "pydantic",
        "pyyaml",
        "rich",
        "typer",
        "uvicorn",
    }
    assert expected_runtime.issubset(component_names)

    dependency_entries = payload.get("dependencies", [])
    root_entry = next(
        item
        for item in dependency_entries
        if item.get("ref") == root["bom-ref"]
    )
    root_direct_names = {
        component_by_ref[ref]["name"].lower()
        for ref in root_entry.get("dependsOn", [])
    }
    assert root_direct_names == expected_runtime

    known_refs = set(component_by_ref) | {root["bom-ref"]}
    unknown_refs = {
        ref
        for item in dependency_entries
        for ref in [item.get("ref"), *item.get("dependsOn", [])]
        if ref and ref not in known_refs
    }
    assert not unknown_refs
    assert sum(
        len(item.get("dependsOn", []))
        for item in dependency_entries
    ) > len(root_entry["dependsOn"])


def test_h8b_reproducibility_documentation_exists():
    content = (REQUIREMENTS / "README.md").read_text(
        encoding="utf-8"
    )

    assert "pip-tools: 7.6.1" in content
    assert "CycloneDX Python: 7.4.0" in content
    assert "pip --require-hashes" in content
    assert "fresh Linux container" in content
    assert "cyclonedx-py environment" in content
    assert "root dependency graph" in content
