import json

from supplysentinel.inventory.dependency_inventory import (
    build_dependency_inventory,
    generate_inventory_json,
)


def test_vulnerable_repo_dependency_inventory_detects_dependencies(vulnerable_repo):
    inventory = build_dependency_inventory(str(vulnerable_repo))

    package_names = {dependency.name for dependency in inventory.dependencies}

    assert inventory.summary.total_dependencies > 0
    assert inventory.summary.npm_dependencies > 0
    assert inventory.summary.python_dependencies > 0
    assert "express" in package_names
    assert "flask" in package_names


def test_vulnerable_repo_inventory_detects_risky_dependency_patterns(vulnerable_repo):
    inventory = build_dependency_inventory(str(vulnerable_repo))

    assert inventory.summary.unpinned_dependencies > 0
    assert inventory.summary.loose_dependencies > 0
    assert inventory.summary.internal_candidate_dependencies > 0
    assert inventory.summary.dependencies_missing_private_registry > 0


def test_secure_repo_inventory_detects_pinned_dependencies(secure_repo):
    inventory = build_dependency_inventory(str(secure_repo))

    assert inventory.summary.total_dependencies > 0
    assert inventory.summary.pinned_dependencies == inventory.summary.total_dependencies
    assert inventory.summary.dependencies_missing_private_registry == 0


def test_inventory_json_generation(vulnerable_repo):
    inventory = build_dependency_inventory(str(vulnerable_repo))
    report = generate_inventory_json(inventory)
    data = json.loads(report)

    assert data["summary"]["total_dependencies"] == inventory.summary.total_dependencies
    assert "dependencies" in data
    assert data["dependencies"]