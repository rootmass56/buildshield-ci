from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = PROJECT_ROOT / "evaluation" / "corpus-design-v1.json"

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

EXPECTED_CASE_TYPES = {
    "canonical_positive",
    "canonical_negative",
    "positive_boundary",
    "negative_near_miss",
    "adversarial_positive",
    "adversarial_negative",
}


def _design() -> dict:
    return json.loads(DESIGN_PATH.read_text(encoding="utf-8"))


def test_h9a_design_is_bound_to_the_accepted_h8_checkpoint():
    design = _design()

    assert design["schema_version"] == 1
    assert (
        design["checkpoint_basis"]
        == "367ead5670b26c7e6076d063e08b9fb8fdcb206e"
    )
    assert design["product_version_during_h9"] == "0.12.7"


def test_h9a_design_covers_all_20_static_rules_exactly():
    design = _design()
    rule_ids = [rule["rule_id"] for rule in design["rules"]]

    assert len(rule_ids) == 20
    assert len(set(rule_ids)) == 20
    assert set(rule_ids) == EXPECTED_RULES
    assert design["scope"]["static_rule_count"] == 20


def test_h9a_design_has_five_unique_cases_per_rule_and_100_total():
    design = _design()
    cases = design["cases"]
    ids = [case["case_id"] for case in cases]
    counts = Counter(case["rule_id"] for case in cases)

    assert len(cases) == 100
    assert len(set(ids)) == 100
    assert set(counts) == EXPECTED_RULES
    assert set(counts.values()) == {5}
    assert design["scope"]["case_count"] == 100
    assert design["scope"]["cases_per_rule"] == 5


def test_h9a_each_rule_has_positive_and_negative_ground_truth():
    design = _design()
    labels: dict[str, set[bool]] = defaultdict(set)

    for case in design["cases"]:
        labels[case["rule_id"]].add(case["expected_detected"])
        assert case["expected_target_count"] in {0, 1}
        assert case["expected_target_count"] == (
            1 if case["expected_detected"] else 0
        )

    assert set(labels) == EXPECTED_RULES
    assert all(rule_labels == {True, False} for rule_labels in labels.values())


def test_h9a_cases_are_deterministic_offline_and_have_oracles():
    design = _design()

    for case in design["cases"]:
        assert case["deterministic"] is True
        assert case["network_required"] is False
        assert case["case_type"] in EXPECTED_CASE_TYPES
        assert case["scenario"].strip()
        assert case["oracle"].strip()
        assert case["fixture_path"].startswith(
            f"evaluation/corpus/{case['rule_id']}/"
        )


def test_h9a_metrics_contract_defines_required_confusion_matrix_outputs():
    contract = _design()["classification_contract"]

    for required in (
        "tp",
        "tn",
        "fp",
        "fn",
        "precision",
        "recall",
        "f1",
        "aggregate",
        "claim_boundary",
    ):
        assert contract[required]

    assert "curated deterministic corpus" in contract["claim_boundary"]


def test_h9a_preserves_existing_benchmark_and_identifies_prior_gaps():
    evidence = _design()["existing_h8_evidence"]

    assert evidence["controlled_vulnerable_findings"] == 22
    assert evidence["controlled_secure_findings"] == 0
    assert evidence["rules_without_literal_test_reference"] == [
        "DG-DOCKER-003",
        "DG-DOCKER-008",
    ]
    assert evidence["rules_not_hit_by_controlled_vulnerable_sample"] == [
        "DG-DOCKER-003",
        "DG-DOCKER-008",
    ]
    assert evidence["rules_hit_by_controlled_secure_sample"] == []


def test_h9a_osv_is_deterministic_and_separate_from_static_rule_metrics():
    osv = _design()["auxiliary_osv_evaluation"]

    assert osv["included_in_static_rule_metrics"] is False
    assert len(osv["planned_deterministic_cases"]) == 6
    assert {
        case["id"]
        for case in osv["planned_deterministic_cases"]
    } == {
        "OSV-01",
        "OSV-02",
        "OSV-03",
        "OSV-04",
        "OSV-05",
        "OSV-06",
    }
