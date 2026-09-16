from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


Scanner = Callable[[str], Any]


def safe_divide(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0

    return float(numerator) / float(denominator)


def rounded_metric(value: float) -> float:
    return round(float(value), 6)


def classify_outcome(expected_detected: bool, predicted_detected: bool) -> str:
    if expected_detected and predicted_detected:
        return "TP"
    if not expected_detected and not predicted_detected:
        return "TN"
    if not expected_detected and predicted_detected:
        return "FP"
    return "FN"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def default_design_path(project_root: Path) -> Path:
    return project_root / "evaluation" / "corpus-design-v1.json"


def evaluate_case(
    project_root: Path,
    case: dict[str, Any],
    scanner: Scanner,
) -> dict[str, Any]:
    fixture_path = project_root / str(case["fixture_path"])
    result = scanner(str(fixture_path))

    target_rule_id = str(case["rule_id"])
    target_findings = [
        finding
        for finding in result.findings
        if finding.rule_id == target_rule_id
    ]
    predicted_detected = bool(target_findings)
    expected_detected = bool(case["expected_detected"])
    expected_target_count = int(case["expected_target_count"])
    target_count = len(target_findings)

    all_rule_ids = sorted(
        finding.rule_id
        for finding in result.findings
    )
    non_target_rule_ids = sorted(
        {
            rule_id
            for rule_id in all_rule_ids
            if rule_id != target_rule_id
        }
    )

    return {
        "case_id": str(case["case_id"]),
        "rule_id": target_rule_id,
        "analyzer": str(case["analyzer"]),
        "case_type": str(case["case_type"]),
        "fixture_path": str(case["fixture_path"]),
        "expected_detected": expected_detected,
        "predicted_detected": predicted_detected,
        "expected_target_count": expected_target_count,
        "target_count": target_count,
        "outcome": classify_outcome(
            expected_detected=expected_detected,
            predicted_detected=predicted_detected,
        ),
        "target_count_matches_oracle": (
            target_count == expected_target_count
        ),
        "non_target_rule_ids": non_target_rule_ids,
    }


def build_report_from_case_results(
    design: dict[str, Any],
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered_cases = sorted(
        case_results,
        key=lambda item: str(item["case_id"]),
    )

    expected_case_ids = {
        str(case["case_id"])
        for case in design["cases"]
    }
    actual_case_ids = {
        str(case["case_id"])
        for case in ordered_cases
    }

    if len(ordered_cases) != 100:
        raise ValueError(
            f"H9 corpus must contain exactly 100 case results; "
            f"got {len(ordered_cases)}."
        )

    if expected_case_ids != actual_case_ids:
        missing = sorted(expected_case_ids - actual_case_ids)
        extra = sorted(actual_case_ids - expected_case_ids)
        raise ValueError(
            f"Case-result set does not match the corpus oracle. "
            f"missing={missing}, extra={extra}"
        )

    cases_by_rule: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for case in ordered_cases:
        cases_by_rule[str(case["rule_id"])].append(case)

    per_rule: list[dict[str, Any]] = []

    for rule in sorted(
        design["rules"],
        key=lambda item: str(item["rule_id"]),
    ):
        rule_id = str(rule["rule_id"])
        cases = cases_by_rule.get(rule_id, [])

        if len(cases) != 5:
            raise ValueError(
                f"Rule {rule_id} must have exactly five cases; "
                f"got {len(cases)}."
            )

        outcomes = Counter(
            str(case["outcome"])
            for case in cases
        )
        tp = outcomes["TP"]
        tn = outcomes["TN"]
        fp = outcomes["FP"]
        fn = outcomes["FN"]

        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(
            2 * precision * recall,
            precision + recall,
        )

        per_rule.append(
            {
                "rule_id": rule_id,
                "analyzer": str(rule["analyzer"]),
                "title": str(rule["title"]),
                "cases": len(cases),
                "positive_support": sum(
                    bool(case["expected_detected"])
                    for case in cases
                ),
                "negative_support": sum(
                    not bool(case["expected_detected"])
                    for case in cases
                ),
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "precision": rounded_metric(precision),
                "recall": rounded_metric(recall),
                "f1": rounded_metric(f1),
                "classification_mismatch_case_ids": [
                    str(case["case_id"])
                    for case in cases
                    if case["outcome"] in {"FP", "FN"}
                ],
                "target_count_mismatch_case_ids": [
                    str(case["case_id"])
                    for case in cases
                    if not bool(case["target_count_matches_oracle"])
                ],
            }
        )

    totals = Counter()

    for rule in per_rule:
        for key in ("tp", "tn", "fp", "fn"):
            totals[key] += int(rule[key])

    total_cases = sum(totals.values())

    if total_cases != 100:
        raise ValueError(
            f"Confusion matrix must cover exactly 100 cases; "
            f"got {total_cases}."
        )

    micro_precision = safe_divide(
        totals["tp"],
        totals["tp"] + totals["fp"],
    )
    micro_recall = safe_divide(
        totals["tp"],
        totals["tp"] + totals["fn"],
    )
    micro_f1 = safe_divide(
        2 * micro_precision * micro_recall,
        micro_precision + micro_recall,
    )
    micro_accuracy = safe_divide(
        totals["tp"] + totals["tn"],
        total_cases,
    )

    classification_mismatch_case_ids = [
        str(case["case_id"])
        for case in ordered_cases
        if case["outcome"] in {"FP", "FN"}
    ]
    target_count_mismatch_case_ids = [
        str(case["case_id"])
        for case in ordered_cases
        if not bool(case["target_count_matches_oracle"])
    ]
    cross_rule_leakage_case_ids = [
        str(case["case_id"])
        for case in ordered_cases
        if case["non_target_rule_ids"]
    ]
    duplicate_target_finding_count = sum(
        max(0, int(case["target_count"]) - 1)
        for case in ordered_cases
    )
    perfect_rule_ids = [
        str(rule["rule_id"])
        for rule in per_rule
        if int(rule["fp"]) == 0
        and int(rule["fn"]) == 0
    ]

    return {
        "schema_version": 1,
        "checkpoint_basis": str(design["checkpoint_basis"]),
        "product_version": "0.12.7",
        "report_kind": (
            "curated_deterministic_static_corpus_evaluation"
        ),
        "claim_boundary": (
            "Metrics describe only the curated deterministic H9 corpus "
            "and are not estimates of real-world detection accuracy."
        ),
        "corpus": {
            "static_rules": len(per_rule),
            "static_cases": len(ordered_cases),
            "cases_per_rule": 5,
            "network_required": False,
        },
        "confusion_matrix": {
            "tp": totals["tp"],
            "tn": totals["tn"],
            "fp": totals["fp"],
            "fn": totals["fn"],
        },
        "micro_metrics": {
            "precision": rounded_metric(micro_precision),
            "recall": rounded_metric(micro_recall),
            "f1": rounded_metric(micro_f1),
            "accuracy": rounded_metric(micro_accuracy),
        },
        "macro_metrics": {
            "precision": rounded_metric(
                mean(
                    float(rule["precision"])
                    for rule in per_rule
                )
            ),
            "recall": rounded_metric(
                mean(
                    float(rule["recall"])
                    for rule in per_rule
                )
            ),
            "f1": rounded_metric(
                mean(
                    float(rule["f1"])
                    for rule in per_rule
                )
            ),
        },
        "quality": {
            "classification_mismatch_count": len(
                classification_mismatch_case_ids
            ),
            "classification_mismatch_case_ids": (
                classification_mismatch_case_ids
            ),
            "target_count_mismatch_count": len(
                target_count_mismatch_case_ids
            ),
            "target_count_mismatch_case_ids": (
                target_count_mismatch_case_ids
            ),
            "duplicate_target_finding_count": (
                duplicate_target_finding_count
            ),
            "cross_rule_leakage_case_count": len(
                cross_rule_leakage_case_ids
            ),
            "cross_rule_leakage_case_ids": (
                cross_rule_leakage_case_ids
            ),
            "perfect_rule_count": len(perfect_rule_ids),
            "perfect_rule_ids": perfect_rule_ids,
        },
        "per_rule": per_rule,
        "cases": ordered_cases,
    }


def evaluate_static_corpus(
    project_root: Path | str,
    design_path: Path | str | None = None,
    scanner: Scanner | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    oracle_path = (
        Path(design_path).resolve()
        if design_path is not None
        else default_design_path(root)
    )
    design = load_json(oracle_path)

    if scanner is None:
        from supplysentinel.core.scanner import scan_repository

        scanner = scan_repository

    case_results = [
        evaluate_case(
            project_root=root,
            case=case,
            scanner=scanner,
        )
        for case in design["cases"]
    ]

    return build_report_from_case_results(
        design=design,
        case_results=case_results,
    )


def render_markdown_report(report: dict[str, Any]) -> str:
    confusion = report["confusion_matrix"]
    micro = report["micro_metrics"]
    macro = report["macro_metrics"]
    quality = report["quality"]

    lines = [
        "# BuildShield-CI H9 Deterministic Evaluation",
        "",
        f"Checkpoint basis: `{report['checkpoint_basis']}`",
        f"Package version: `{report['product_version']}`",
        "",
        "## Scope boundary",
        "",
        str(report["claim_boundary"]),
        "",
        "## Aggregate results",
        "",
        f"- Cases: {report['corpus']['static_cases']}",
        f"- Rules: {report['corpus']['static_rules']}",
        (
            "- Confusion matrix: "
            f"TP={confusion['tp']}, TN={confusion['tn']}, "
            f"FP={confusion['fp']}, FN={confusion['fn']}"
        ),
        (
            "- Micro: "
            f"precision={micro['precision']:.6f}, "
            f"recall={micro['recall']:.6f}, "
            f"F1={micro['f1']:.6f}, "
            f"accuracy={micro['accuracy']:.6f}"
        ),
        (
            "- Macro: "
            f"precision={macro['precision']:.6f}, "
            f"recall={macro['recall']:.6f}, "
            f"F1={macro['f1']:.6f}"
        ),
        (
            "- Classification mismatches: "
            f"{quality['classification_mismatch_count']}"
        ),
        (
            "- Cross-rule leakage cases: "
            f"{quality['cross_rule_leakage_case_count']}"
        ),
        (
            "- Duplicate target findings: "
            f"{quality['duplicate_target_finding_count']}"
        ),
        "",
        "## Per-rule metrics",
        "",
        "| Rule | TP | TN | FP | FN | Precision | Recall | F1 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for rule in report["per_rule"]:
        lines.append(
            f"| {rule['rule_id']} | {rule['tp']} | {rule['tn']} | "
            f"{rule['fp']} | {rule['fn']} | "
            f"{rule['precision']:.6f} | {rule['recall']:.6f} | "
            f"{rule['f1']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Mismatch cases",
            "",
        ]
    )

    mismatch_ids = quality["classification_mismatch_case_ids"]

    if mismatch_ids:
        lines.extend(
            f"- `{case_id}`"
            for case_id in mismatch_ids
        )
    else:
        lines.append("- None.")

    return "\n".join(lines) + "\n"


def write_json_report(
    report: dict[str, Any],
    output_path: Path | str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(report, indent=2) + "\n"
    ).encode("utf-8")
    path.write_bytes(payload)
    return path


def write_markdown_report(
    report: dict[str, Any],
    output_path: Path | str,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        render_markdown_report(report).encode("utf-8")
    )
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the BuildShield-CI curated deterministic H9 corpus."
        )
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Repository root containing evaluation/corpus-design-v1.json.",
    )
    parser.add_argument(
        "--design",
        default=None,
        help="Optional explicit corpus design JSON path.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional deterministic JSON report output path.",
    )
    parser.add_argument(
        "--markdown-out",
        default=None,
        help="Optional Markdown report output path.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = evaluate_static_corpus(
        project_root=Path(args.project_root),
        design_path=(
            Path(args.design)
            if args.design is not None
            else None
        ),
    )

    if args.json_out:
        write_json_report(report, args.json_out)

    if args.markdown_out:
        write_markdown_report(report, args.markdown_out)

    if not args.json_out and not args.markdown_out:
        print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
