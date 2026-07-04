import json
from html import escape
from pathlib import Path
from typing import Literal

from supplysentinel.core.models import ComparisonResult, ScanResult


ReportFormat = Literal["json", "md", "html"]


def ensure_parent_directory(output_path: Path) -> None:
    """
    Ensure the output directory exists before writing report files.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)


def write_report(output_path: str, content: str) -> Path:
    """
    Write report content to disk.
    """
    path = Path(output_path)
    ensure_parent_directory(path)
    path.write_text(content, encoding="utf-8")
    return path


def scan_result_to_dict(result: ScanResult) -> dict:
    """
    Convert ScanResult into a JSON-safe dictionary.
    """
    return result.model_dump(mode="json")


def comparison_result_to_dict(result: ComparisonResult) -> dict:
    """
    Convert ComparisonResult into a JSON-safe dictionary.
    """
    return result.model_dump(mode="json")


def generate_scan_json(result: ScanResult) -> str:
    """
    Generate JSON report for a repository scan.
    """
    return json.dumps(scan_result_to_dict(result), indent=2)


def generate_comparison_json(result: ComparisonResult) -> str:
    """
    Generate JSON report for repository comparison.
    """
    return json.dumps(comparison_result_to_dict(result), indent=2)


def generate_scan_markdown(result: ScanResult) -> str:
    """
    Generate Markdown report for a repository scan.
    """
    summary = result.summary
    profile = result.risk_profile

    lines: list[str] = []

    lines.append("# BuildShield-CI Scan Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Target Path:** `{summary.target_path}`")
    lines.append(f"- **Security Score:** `{summary.security_score}/100`")
    lines.append(f"- **Risk Level:** `{summary.risk_level.value}`")
    lines.append(f"- **Build Gate Status:** `{profile.build_gate_status}`")
    lines.append(f"- **Build Gate Reason:** {profile.build_gate_reason}")
    lines.append(f"- **Total Findings:** `{summary.findings_count}`")
    lines.append("")

    lines.append("## Finding Severity Summary")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Critical | {summary.critical_count} |")
    lines.append(f"| High | {summary.high_count} |")
    lines.append(f"| Medium | {summary.medium_count} |")
    lines.append(f"| Low | {summary.low_count} |")
    lines.append(f"| Info | {summary.info_count} |")
    lines.append("")

    lines.append("## Category-wise Risk Breakdown")
    lines.append("")
    if profile.category_risks:
        lines.append("| Category | Findings | Penalty Points | Risk Score | Risk Level |")
        lines.append("|---|---:|---:|---:|---|")
        for category_risk in profile.category_risks:
            lines.append(
                "| "
                f"{category_risk.category.value} | "
                f"{category_risk.finding_count} | "
                f"{category_risk.penalty_points} | "
                f"{category_risk.risk_score}/100 | "
                f"{category_risk.risk_level.value} |"
            )
    else:
        lines.append("No category risk detected.")
    lines.append("")

    lines.append("## Top Risk Drivers")
    lines.append("")
    if profile.top_risk_drivers:
        lines.append("| Rank | Rule ID | Severity | Category | Title | File | Line | Contribution |")
        lines.append("|---:|---|---|---|---|---|---:|---:|")
        for index, driver in enumerate(profile.top_risk_drivers, start=1):
            lines.append(
                "| "
                f"{index} | "
                f"{driver.rule_id} | "
                f"{driver.severity.value} | "
                f"{driver.category.value} | "
                f"{driver.title} | "
                f"`{driver.file_path}` | "
                f"{driver.line_number or '-'} | "
                f"{driver.contribution_points} |"
            )
    else:
        lines.append("No top risk drivers detected.")
    lines.append("")

    lines.append("## Security-Relevant Files Discovered")
    lines.append("")
    if result.discovered_files:
        lines.append("| Relative Path | Type | Size |")
        lines.append("|---|---|---:|")
        for repo_file in result.discovered_files:
            lines.append(
                "| "
                f"`{repo_file.relative_path}` | "
                f"{repo_file.file_type} | "
                f"{repo_file.size_bytes} bytes |"
            )
    else:
        lines.append("No security-relevant files discovered.")
    lines.append("")

    lines.append("## Detailed Findings")
    lines.append("")
    if result.findings:
        for finding in result.findings:
            lines.append(f"### {finding.rule_id}: {finding.title}")
            lines.append("")
            lines.append(f"- **Severity:** `{finding.severity.value}`")
            lines.append(f"- **Category:** `{finding.category.value}`")
            lines.append(f"- **Confidence:** `{finding.confidence}`")
            lines.append(f"- **File:** `{finding.evidence.file_path}`")
            lines.append(f"- **Line:** `{finding.evidence.line_number or '-'}`")
            lines.append(f"- **Evidence:** `{finding.evidence.snippet or 'N/A'}`")
            lines.append(f"- **Description:** {finding.description}")
            lines.append(f"- **Impact:** {finding.impact}")
            lines.append(f"- **Remediation:** {finding.remediation}")
            if finding.reference:
                lines.append(f"- **Reference:** {finding.reference}")
            lines.append("")
    else:
        lines.append("No security findings detected.")
        lines.append("")

    return "\n".join(lines)


def generate_comparison_markdown(result: ComparisonResult) -> str:
    """
    Generate Markdown report for before/after repository comparison.
    """
    baseline = result.baseline.summary
    target = result.target.summary

    lines: list[str] = []

    lines.append("# BuildShield-CI Security Posture Comparison Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Verdict:** `{result.verdict}`")
    lines.append(f"- **Score Improvement:** `{result.score_delta:+d}` points")
    lines.append(f"- **Findings Reduced:** `{result.findings_reduced}`")
    lines.append(f"- **Risk Reduction:** `{result.risk_reduction_percentage}%`")
    lines.append("")

    lines.append("## Before vs After Comparison")
    lines.append("")
    lines.append(
        f"| Metric | {result.baseline_label} | {result.target_label} | Delta |"
    )
    lines.append("|---|---:|---:|---:|")
    lines.append(
        f"| Security Score | {baseline.security_score}/100 | "
        f"{target.security_score}/100 | {result.score_delta:+d} |"
    )
    lines.append(
        f"| Findings | {baseline.findings_count} | "
        f"{target.findings_count} | {target.findings_count - baseline.findings_count} |"
    )
    lines.append(
        f"| Critical Findings | {baseline.critical_count} | "
        f"{target.critical_count} | {target.critical_count - baseline.critical_count} |"
    )
    lines.append(
        f"| High Findings | {baseline.high_count} | "
        f"{target.high_count} | {target.high_count - baseline.high_count} |"
    )
    lines.append("")

    lines.append("## Build Gate Comparison")
    lines.append("")
    lines.append(f"- **Baseline Build Gate:** `{result.baseline.risk_profile.build_gate_status}`")
    lines.append(f"- **Target Build Gate:** `{result.target.risk_profile.build_gate_status}`")
    lines.append("")

    return "\n".join(lines)


def generate_scan_html(result: ScanResult) -> str:
    """
    Generate standalone HTML report for a repository scan.
    """
    summary = result.summary
    profile = result.risk_profile

    category_rows = ""
    for category_risk in profile.category_risks:
        category_rows += f"""
        <tr>
            <td>{escape(category_risk.category.value)}</td>
            <td>{category_risk.finding_count}</td>
            <td>{category_risk.penalty_points}</td>
            <td>{category_risk.risk_score}/100</td>
            <td>{escape(category_risk.risk_level.value)}</td>
        </tr>
        """

    driver_rows = ""
    for index, driver in enumerate(profile.top_risk_drivers, start=1):
        driver_rows += f"""
        <tr>
            <td>{index}</td>
            <td>{escape(driver.rule_id)}</td>
            <td>{escape(driver.severity.value)}</td>
            <td>{escape(driver.category.value)}</td>
            <td>{escape(driver.title)}</td>
            <td>{escape(driver.file_path)}</td>
            <td>{driver.line_number or "-"}</td>
            <td>{driver.contribution_points}</td>
        </tr>
        """

    file_rows = ""
    for repo_file in result.discovered_files:
        file_rows += f"""
        <tr>
            <td>{escape(repo_file.relative_path)}</td>
            <td>{escape(repo_file.file_type)}</td>
            <td>{repo_file.size_bytes} bytes</td>
        </tr>
        """

    finding_cards = ""
    if result.findings:
        for finding in result.findings:
            finding_cards += f"""
            <div class="finding-card {escape(finding.severity.value.lower())}">
                <h3>{escape(finding.rule_id)}: {escape(finding.title)}</h3>
                <p><strong>Severity:</strong> {escape(finding.severity.value)}</p>
                <p><strong>Category:</strong> {escape(finding.category.value)}</p>
                <p><strong>Confidence:</strong> {escape(finding.confidence)}</p>
                <p><strong>File:</strong> <code>{escape(finding.evidence.file_path)}</code></p>
                <p><strong>Line:</strong> {finding.evidence.line_number or "-"}</p>
                <p><strong>Evidence:</strong> <code>{escape(finding.evidence.snippet or "N/A")}</code></p>
                <p><strong>Description:</strong> {escape(finding.description)}</p>
                <p><strong>Impact:</strong> {escape(finding.impact)}</p>
                <p><strong>Remediation:</strong> {escape(finding.remediation)}</p>
                <p><strong>Reference:</strong> {escape(finding.reference or "N/A")}</p>
            </div>
            """
    else:
        finding_cards = "<p class='success'>No security findings detected.</p>"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BuildShield-CI Scan Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
            margin: 0;
            padding: 24px;
        }}
        h1, h2, h3 {{
            color: #38bdf8;
        }}
        .card {{
            background: #111827;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #334155;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #1e293b;
            color: #7dd3fc;
        }}
        code {{
            background: #020617;
            padding: 3px 6px;
            border-radius: 5px;
            color: #facc15;
        }}
        .score {{
            font-size: 38px;
            font-weight: bold;
            color: #22c55e;
        }}
        .failed {{
            color: #f87171;
            font-weight: bold;
        }}
        .passed {{
            color: #22c55e;
            font-weight: bold;
        }}
        .finding-card {{
            background: #111827;
            border-left: 6px solid #64748b;
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 8px;
        }}
        .critical {{
            border-left-color: #dc2626;
        }}
        .high {{
            border-left-color: #f97316;
        }}
        .medium {{
            border-left-color: #eab308;
        }}
        .low {{
            border-left-color: #22c55e;
        }}
        .success {{
            color: #22c55e;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>BuildShield-CI Scan Report</h1>

    <div class="card">
        <h2>Executive Summary</h2>
        <p><strong>Target:</strong> <code>{escape(summary.target_path)}</code></p>
        <p class="score">{summary.security_score}/100</p>
        <p><strong>Risk Level:</strong> {escape(summary.risk_level.value)}</p>
        <p><strong>Build Gate:</strong>
            <span class="{escape(profile.build_gate_status.lower())}">
                {escape(profile.build_gate_status)}
            </span>
        </p>
        <p><strong>Reason:</strong> {escape(profile.build_gate_reason)}</p>
    </div>

    <div class="card">
        <h2>Severity Summary</h2>
        <table>
            <tr><th>Severity</th><th>Count</th></tr>
            <tr><td>Critical</td><td>{summary.critical_count}</td></tr>
            <tr><td>High</td><td>{summary.high_count}</td></tr>
            <tr><td>Medium</td><td>{summary.medium_count}</td></tr>
            <tr><td>Low</td><td>{summary.low_count}</td></tr>
            <tr><td>Info</td><td>{summary.info_count}</td></tr>
        </table>
    </div>

    <div class="card">
        <h2>Category-wise Risk Breakdown</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Findings</th>
                <th>Penalty Points</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
            </tr>
            {category_rows}
        </table>
    </div>

    <div class="card">
        <h2>Top Risk Drivers</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>Rule ID</th>
                <th>Severity</th>
                <th>Category</th>
                <th>Title</th>
                <th>File</th>
                <th>Line</th>
                <th>Contribution</th>
            </tr>
            {driver_rows}
        </table>
    </div>

    <div class="card">
        <h2>Security-Relevant Files</h2>
        <table>
            <tr><th>Relative Path</th><th>Type</th><th>Size</th></tr>
            {file_rows}
        </table>
    </div>

    <div class="card">
        <h2>Detailed Findings</h2>
        {finding_cards}
    </div>
</body>
</html>
"""


def generate_comparison_html(result: ComparisonResult) -> str:
    """
    Generate standalone HTML report for repository comparison.
    """
    baseline = result.baseline.summary
    target = result.target.summary

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BuildShield-CI Comparison Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e5e7eb;
            margin: 0;
            padding: 24px;
        }}
        h1, h2 {{
            color: #38bdf8;
        }}
        .card {{
            background: #111827;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 18px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            border: 1px solid #334155;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #1e293b;
            color: #7dd3fc;
        }}
        .good {{
            color: #22c55e;
            font-weight: bold;
        }}
        .bad {{
            color: #f87171;
            font-weight: bold;
        }}
        .big {{
            font-size: 32px;
            font-weight: bold;
            color: #22c55e;
        }}
    </style>
</head>
<body>
    <h1>BuildShield-CI Security Posture Comparison Report</h1>

    <div class="card">
        <h2>Comparison Summary</h2>
        <p><strong>Verdict:</strong> <span class="good">{escape(result.verdict)}</span></p>
        <p class="big">Score Improvement: {result.score_delta:+d} points</p>
        <p><strong>Findings Reduced:</strong> {result.findings_reduced}</p>
        <p><strong>Risk Reduction:</strong> {result.risk_reduction_percentage}%</p>
    </div>

    <div class="card">
        <h2>Before vs After Security Posture</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>{escape(result.baseline_label)}</th>
                <th>{escape(result.target_label)}</th>
                <th>Delta</th>
            </tr>
            <tr>
                <td>Security Score</td>
                <td class="bad">{baseline.security_score}/100</td>
                <td class="good">{target.security_score}/100</td>
                <td>{result.score_delta:+d}</td>
            </tr>
            <tr>
                <td>Risk Level</td>
                <td class="bad">{escape(baseline.risk_level.value)}</td>
                <td class="good">{escape(target.risk_level.value)}</td>
                <td>-</td>
            </tr>
            <tr>
                <td>Findings</td>
                <td>{baseline.findings_count}</td>
                <td>{target.findings_count}</td>
                <td>{target.findings_count - baseline.findings_count}</td>
            </tr>
            <tr>
                <td>Critical Findings</td>
                <td>{baseline.critical_count}</td>
                <td>{target.critical_count}</td>
                <td>{target.critical_count - baseline.critical_count}</td>
            </tr>
            <tr>
                <td>High Findings</td>
                <td>{baseline.high_count}</td>
                <td>{target.high_count}</td>
                <td>{target.high_count - baseline.high_count}</td>
            </tr>
            <tr>
                <td>Build Gate</td>
                <td class="bad">{escape(result.baseline.risk_profile.build_gate_status)}</td>
                <td class="good">{escape(result.target.risk_profile.build_gate_status)}</td>
                <td>-</td>
            </tr>
        </table>
    </div>
</body>
</html>
"""


def generate_scan_report(
    result: ScanResult,
    report_format: ReportFormat,
) -> str:
    """
    Generate scan report content based on selected format.
    """
    if report_format == "json":
        return generate_scan_json(result)

    if report_format == "md":
        return generate_scan_markdown(result)

    if report_format == "html":
        return generate_scan_html(result)

    raise ValueError(f"Unsupported report format: {report_format}")


def generate_comparison_report(
    result: ComparisonResult,
    report_format: ReportFormat,
) -> str:
    """
    Generate comparison report content based on selected format.
    """
    if report_format == "json":
        return generate_comparison_json(result)

    if report_format == "md":
        return generate_comparison_markdown(result)

    if report_format == "html":
        return generate_comparison_html(result)

    raise ValueError(f"Unsupported report format: {report_format}")