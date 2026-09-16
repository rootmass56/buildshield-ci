from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from supplysentinel.core.scanner import (
    discover_security_relevant_files,
    scan_repository,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = PROJECT_ROOT / "evaluation" / "corpus-design-v1.json"
INDEX_PATH = PROJECT_ROOT / "evaluation" / "corpus-index-v1.json"
OSV_CASES_PATH = PROJECT_ROOT / "evaluation" / "osv-cases-v1.json"

EXPECTED_RULES = {
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
    "DG-DOCKER-001",
    "DG-DOCKER-002",
    "DG-DOCKER-003",
    "DG-DOCKER-004",
    "DG-DOCKER-005",
    "DG-DOCKER-006",
    "DG-DOCKER-007",
    "DG-DOCKER-008",
}

EXPECTED_PRIMARY_FILE_TYPES = {
    "npm": "package_json",
    "python": "python_requirements",
    "github_actions": "github_actions_workflow",
    "dockerfile": "dockerfile",
}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _design() -> dict:
    return _json(DESIGN_PATH)


def _index() -> dict:
    return _json(INDEX_PATH)


def _stable_prediction(fixture: Path) -> list[tuple]:
    result = scan_repository(str(fixture))

    return sorted(
        (
            finding.rule_id,
            finding.evidence.file_path,
            finding.evidence.line_number,
            finding.evidence.snippet,
        )
        for finding in result.findings
    )


def test_h9b_materializes_exactly_100_fixture_directories() -> None:
    design = _design()
    fixture_dirs = []

    for case in design["cases"]:
        fixture = PROJECT_ROOT / case["fixture_path"]
        assert fixture.is_dir(), case["case_id"]
        fixture_dirs.append(fixture)

    assert len(fixture_dirs) == 100
    assert len({path.resolve() for path in fixture_dirs}) == 100


def test_h9b_corpus_index_matches_design_and_all_file_hashes() -> None:
    design = _design()
    index = _index()

    assert index["schema_version"] == 1
    assert index["checkpoint_basis"] == design["checkpoint_basis"]
    assert index["case_count"] == 100
    assert len(index["cases"]) == 100

    design_cases = {
        case["case_id"]: case
        for case in design["cases"]
    }
    indexed_cases = {
        case["case_id"]: case
        for case in index["cases"]
    }

    assert set(indexed_cases) == set(design_cases)

    actual_file_count = 0

    for case_id, entry in indexed_cases.items():
        design_case = design_cases[case_id]

        assert entry["rule_id"] == design_case["rule_id"]
        assert entry["fixture_path"] == design_case["fixture_path"]
        assert entry["files"]

        fixture = PROJECT_ROOT / entry["fixture_path"]

        actual_relative_files = sorted(
            path.relative_to(fixture).as_posix()
            for path in fixture.rglob("*")
            if path.is_file()
        )
        indexed_relative_files = sorted(
            item["path"]
            for item in entry["files"]
        )

        assert actual_relative_files == indexed_relative_files

        for item in entry["files"]:
            path = fixture / item["path"]
            content = path.read_bytes()

            assert len(content) == item["size"]
            assert hashlib.sha256(content).hexdigest() == item["sha256"]
            actual_file_count += 1

    assert actual_file_count == index["file_count"]


def test_h9b_every_fixture_exposes_the_expected_analyzer_input_type() -> None:
    design = _design()

    for case in design["cases"]:
        fixture = PROJECT_ROOT / case["fixture_path"]
        discovered = discover_security_relevant_files(fixture)
        file_types = {
            item.file_type
            for item in discovered
        }

        expected_type = EXPECTED_PRIMARY_FILE_TYPES[case["analyzer"]]
        assert expected_type in file_types, case["case_id"]


def test_h9b_fixtures_are_offline_regular_files_without_symlinks() -> None:
    design = _design()

    for case in design["cases"]:
        assert case["network_required"] is False

        fixture = PROJECT_ROOT / case["fixture_path"]

        for path in fixture.rglob("*"):
            assert not path.is_symlink(), path

            if path.is_file():
                assert path.stat().st_size < 64 * 1024, path


def test_h9b_each_rule_retains_five_cases_with_positive_and_negative_labels() -> None:
    design = _design()
    counts = Counter(case["rule_id"] for case in design["cases"])
    labels: dict[str, set[bool]] = defaultdict(set)

    for case in design["cases"]:
        labels[case["rule_id"]].add(case["expected_detected"])

    assert set(counts) == EXPECTED_RULES
    assert set(counts.values()) == {5}
    assert all(value == {True, False} for value in labels.values())


def test_h9b_all_100_fixtures_scan_deterministically_twice() -> None:
    design = _design()

    for case in design["cases"]:
        fixture = PROJECT_ROOT / case["fixture_path"]

        first = _stable_prediction(fixture)
        second = _stable_prediction(fixture)

        assert first == second, case["case_id"]


def test_h9b_osv_manifest_contains_six_offline_deterministic_cases() -> None:
    osv = _json(OSV_CASES_PATH)

    assert osv["schema_version"] == 1
    assert osv["network_required"] is False
    assert osv["included_in_static_rule_metrics"] is False
    assert len(osv["cases"]) == 6
    assert {
        case["case_id"]
        for case in osv["cases"]
    } == {
        "OSV-01",
        "OSV-02",
        "OSV-03",
        "OSV-04",
        "OSV-05",
        "OSV-06",
    }


def test_h9b_prior_uncovered_docker_rules_now_have_full_fixture_families() -> None:
    design = _design()

    for rule_id in ("DG-DOCKER-003", "DG-DOCKER-008"):
        cases = [
            case
            for case in design["cases"]
            if case["rule_id"] == rule_id
        ]

        assert len(cases) == 5
        assert {case["expected_detected"] for case in cases} == {
            True,
            False,
        }

        for case in cases:
            fixture = PROJECT_ROOT / case["fixture_path"]
            assert (fixture / "Dockerfile").is_file()
