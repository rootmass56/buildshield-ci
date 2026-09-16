from __future__ import annotations

import json
from pathlib import Path

import pytest

from supplysentinel.evaluation.corpus_evaluator import (
    classify_outcome,
    evaluate_static_corpus,
    render_markdown_report,
    safe_divide,
    write_json_report,
    write_markdown_report,
)
from supplysentinel.intelligence import osv_client
from supplysentinel.inventory.dependency_inventory import (
    build_dependency_inventory,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "h9c-baseline-metrics-v1.json"
)
FINAL_METRICS_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "h9d-final-metrics-v1.json"
)
OSV_CASES_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "osv-cases-v1.json"
)

PRE_HARDENING_MISMATCH_IDS = [
    "DG-DOCKER-002-03",
    "DG-DOCKER-002-05",
    "DG-DOCKER-003-05",
    "DG-DOCKER-004-05",
    "DG-DOCKER-005-05",
    "DG-DOCKER-006-05",
    "DG-DOCKER-007-03",
    "DG-DOCKER-007-05",
    "DG-GHA-002-05",
    "DG-GHA-003-05",
    "DG-GHA-004-05",
    "DG-GHA-005-05",
    "DG-NPM-004-05",
    "DG-PY-003-05",
]


@pytest.fixture(scope="module")
def report() -> dict:
    return evaluate_static_corpus(PROJECT_ROOT)


def test_h9c_metric_helpers_and_outcome_labels() -> None:
    assert safe_divide(1, 0) == 0.0
    assert safe_divide(3, 4) == 0.75

    assert classify_outcome(True, True) == "TP"
    assert classify_outcome(False, False) == "TN"
    assert classify_outcome(False, True) == "FP"
    assert classify_outcome(True, False) == "FN"


def test_h9c_evaluator_covers_exactly_100_cases_and_20_rules(
    report: dict,
) -> None:
    assert report["schema_version"] == 1
    assert report["corpus"] == {
        "static_rules": 20,
        "static_cases": 100,
        "cases_per_rule": 5,
        "network_required": False,
    }
    assert len(report["cases"]) == 100
    assert len(report["per_rule"]) == 20


def test_h9c_pre_hardening_baseline_is_preserved() -> None:
    baseline = json.loads(
        BASELINE_PATH.read_text(encoding="utf-8")
    )

    assert baseline["confusion_matrix"] == {
        "tp": 41,
        "tn": 45,
        "fp": 4,
        "fn": 10,
    }
    assert baseline["micro_metrics"] == {
        "precision": 0.911111,
        "recall": 0.803922,
        "f1": 0.854167,
        "accuracy": 0.86,
    }
    assert baseline["macro_metrics"] == {
        "precision": 0.933333,
        "recall": 0.833333,
        "f1": 0.85,
    }
    assert (
        baseline["quality"]["classification_mismatch_case_ids"]
        == PRE_HARDENING_MISMATCH_IDS
    )


def test_h9d_live_confusion_matrix_and_aggregate_metrics(
    report: dict,
) -> None:
    assert report["confusion_matrix"] == {
        "tp": 51,
        "tn": 49,
        "fp": 0,
        "fn": 0,
    }
    assert report["micro_metrics"] == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
        "accuracy": 1.0,
    }
    assert report["macro_metrics"] == {
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }


def test_h9d_per_rule_metrics_are_perfect_on_curated_corpus(
    report: dict,
) -> None:
    assert len(report["per_rule"]) == 20

    for rule in report["per_rule"]:
        assert rule["fp"] == 0
        assert rule["fn"] == 0
        assert rule["precision"] == 1.0
        assert rule["recall"] == 1.0
        assert rule["f1"] == 1.0


def test_h9d_has_zero_mismatches_without_rewriting_ground_truth(
    report: dict,
) -> None:
    quality = report["quality"]

    assert quality["classification_mismatch_count"] == 0
    assert quality["classification_mismatch_case_ids"] == []
    assert quality["target_count_mismatch_count"] == 0
    assert quality["target_count_mismatch_case_ids"] == []

    baseline = json.loads(
        BASELINE_PATH.read_text(encoding="utf-8")
    )
    assert (
        baseline["quality"]["classification_mismatch_case_ids"]
        == PRE_HARDENING_MISMATCH_IDS
    )


def test_h9d_has_no_cross_rule_leakage_or_duplicate_targets(
    report: dict,
) -> None:
    quality = report["quality"]

    assert quality["duplicate_target_finding_count"] == 0
    assert quality["cross_rule_leakage_case_count"] == 0
    assert quality["cross_rule_leakage_case_ids"] == []
    assert quality["perfect_rule_count"] == 20


def test_h9d_report_is_deterministic_and_matches_final_metrics(
    report: dict,
    tmp_path: Path,
) -> None:
    second = evaluate_static_corpus(PROJECT_ROOT)
    final_metrics = json.loads(
        FINAL_METRICS_PATH.read_text(encoding="utf-8")
    )

    assert report == second
    assert report == final_metrics

    generated = tmp_path / "metrics.json"
    write_json_report(report, generated)

    assert generated.read_bytes() == FINAL_METRICS_PATH.read_bytes()
    assert b"\\r\\n" not in generated.read_bytes()


def test_h9d_markdown_report_keeps_claim_boundary_and_final_metrics(
    report: dict,
    tmp_path: Path,
) -> None:
    markdown = render_markdown_report(report)

    assert "curated deterministic H9 corpus" in markdown
    assert "not estimates of real-world detection accuracy" in markdown
    assert "TP=51, TN=49, FP=0, FN=0" in markdown
    assert "Classification mismatches: 0" in markdown

    generated = tmp_path / "metrics.md"
    write_markdown_report(report, generated)
    assert generated.read_text(encoding="utf-8") == markdown
    assert b"\\r\\n" not in generated.read_bytes()


def test_h9c_osv_queryability_manifest_matches_client_semantics(
    tmp_path: Path,
) -> None:
    manifest = json.loads(
        OSV_CASES_PATH.read_text(encoding="utf-8")
    )
    cases = {
        case["case_id"]: case
        for case in manifest["cases"]
    }

    for case_id in ("OSV-01", "OSV-02", "OSV-03", "OSV-04"):
        case = cases[case_id]
        fixture = tmp_path / case_id
        fixture.mkdir()

        source = case["input"]

        if source["ecosystem"] == "npm":
            (fixture / "package.json").write_text(
                json.dumps(
                    {
                        "name": "h9-osv-fixture",
                        "version": "1.0.0",
                        "dependencies": {
                            source["name"]: source["declared_version"],
                        },
                    }
                ),
                encoding="utf-8",
            )
        else:
            (fixture / "requirements.txt").write_text(
                f"{source['name']}{source['declared_version']}\n",
                encoding="utf-8",
            )

        inventory = build_dependency_inventory(str(fixture))
        queries, skipped = (
            osv_client.build_osv_queries_from_inventory(inventory)
        )

        if case["expected"]["queryable"]:
            assert len(queries) == 1
            assert skipped == []
            assert (
                queries[0].osv_ecosystem
                == case["expected"]["osv_ecosystem"]
            )
            assert queries[0].version == case["expected"]["version"]
        else:
            assert queries == []
            assert len(skipped) == 1
            assert (
                skipped[0].skipped_reason
                == case["expected"]["skipped_reason"]
            )


def test_h9c_osv_mock_response_and_failure_are_network_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads(
        OSV_CASES_PATH.read_text(encoding="utf-8")
    )
    cases = {
        case["case_id"]: case
        for case in manifest["cases"]
    }

    vulnerable_case = cases["OSV-05"]
    query = osv_client.OsvPackageQuery(
        query_id="h9:osv:05",
        ecosystem="npm",
        osv_ecosystem="npm",
        package_name="lodash",
        version="4.17.21",
        file_path="package.json",
    )

    monkeypatch.setattr(
        osv_client,
        "post_json",
        lambda url, payload, timeout_seconds: (
            vulnerable_case["mock_response"]
        ),
    )

    package_results = osv_client.query_osv_batch([query])
    summary = osv_client.build_summary(
        target_path="deterministic-h9-osv",
        total_dependencies_seen=1,
        queryable_dependencies=1,
        skipped_dependencies=0,
        package_results=package_results,
        status="COMPLETED",
    )

    assert (
        summary.vulnerable_dependencies
        == vulnerable_case["expected"]["vulnerable_dependencies"]
    )
    assert (
        summary.total_vulnerabilities
        == vulnerable_case["expected"]["total_vulnerabilities"]
    )
    assert (
        summary.online_lookup_status
        == vulnerable_case["expected"]["status"]
    )

    failure_case = cases["OSV-06"]
    fixture = tmp_path / "osv-failure"
    fixture.mkdir()
    (fixture / "package.json").write_text(
        json.dumps(
            {
                "name": "h9-osv-failure",
                "version": "1.0.0",
                "dependencies": {
                    "lodash": "4.17.21",
                },
            }
        ),
        encoding="utf-8",
    )

    def fail_post_json(
        url: str,
        payload: dict,
        timeout_seconds: int,
    ) -> dict:
        raise osv_client.OsvLookupError(
            failure_case["mock_failure"]
        )

    monkeypatch.setattr(
        osv_client,
        "post_json",
        fail_post_json,
    )

    failure_report = osv_client.build_osv_vulnerability_report(
        target=str(fixture),
        online_lookup=True,
    )

    assert (
        failure_report.summary.online_lookup_status
        == failure_case["expected"]["status"]
    )
    assert failure_case["expected"]["error_contains"] in (
        failure_report.summary.error_message or ""
    )
