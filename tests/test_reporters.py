import json

from supplysentinel.reporters.report_generator import (
    generate_comparison_report,
    generate_scan_report,
)
from supplysentinel.reporters.sarif_reporter import generate_scan_sarif
from supplysentinel.core.comparison import build_comparison_result


def test_json_report_generation(vulnerable_scan):
    report = generate_scan_report(vulnerable_scan, "json")
    data = json.loads(report)

    assert data["summary"]["findings_count"] == vulnerable_scan.summary.findings_count
    assert data["summary"]["security_score"] == vulnerable_scan.summary.security_score
    assert "findings" in data


def test_markdown_report_generation(vulnerable_scan):
    report = generate_scan_report(vulnerable_scan, "md")

    assert "# BuildShield-CI Scan Report" in report
    assert "Executive Summary" in report
    assert "Detailed Findings" in report
    assert "DG-GHA-004" in report


def test_html_report_generation(vulnerable_scan):
    report = generate_scan_report(vulnerable_scan, "html")

    assert "<!DOCTYPE html>" in report
    assert "BuildShield-CI Scan Report" in report
    assert "Detailed Findings" in report
    assert "DG-GHA-004" in report


def test_comparison_report_generation(vulnerable_scan, secure_scan):
    comparison = build_comparison_result(
        baseline=vulnerable_scan,
        target=secure_scan,
        baseline_label="Vulnerable Repo",
        target_label="Secure Repo",
    )

    markdown_report = generate_comparison_report(comparison, "md")
    html_report = generate_comparison_report(comparison, "html")
    json_report = generate_comparison_report(comparison, "json")

    assert "Security Posture Comparison Report" in markdown_report
    assert "BuildShield-CI Security Posture Comparison Report" in html_report

    data = json.loads(json_report)
    assert data["score_delta"] > 0


def test_sarif_report_generation(vulnerable_scan):
    report = generate_scan_sarif(vulnerable_scan)
    data = json.loads(report)

    assert data["version"] == "2.1.0"

    run = data["runs"][0]

    assert run["tool"]["driver"]["name"] == "BuildShield-CI"
    assert "runAutomationDetails" not in run
    assert len(run["results"]) == vulnerable_scan.summary.findings_count

    first_result = run["results"][0]
    first_uri = first_result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]

    assert first_result["ruleId"]
    assert first_result["level"] in {"error", "warning", "note"}
    assert "samples" in first_uri or ".github" in first_uri or "package.json" in first_uri