from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from supplysentinel.core.models import ComparisonResult, ScanResult


console = Console()


def render_banner() -> None:
    """
    Render SupplySentinel CLI banner.
    """
    banner = """
[bold cyan]SupplySentinel[/bold cyan]
Advanced CI/CD Supply Chain Risk Detection and Dependency Confusion Defense Platform
"""
    console.print(Panel.fit(banner, border_style="cyan"))


def render_scan_summary(result: ScanResult) -> None:
    """
    Render high-level scan summary.
    """
    summary = result.summary

    table = Table(title="Scan Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="green")

    table.add_row("Target Path", summary.target_path)
    table.add_row("Files Discovered", str(summary.files_discovered))
    table.add_row("Files Scanned", str(summary.files_scanned))
    table.add_row("Findings", str(summary.findings_count))
    table.add_row("Critical", str(summary.critical_count))
    table.add_row("High", str(summary.high_count))
    table.add_row("Medium", str(summary.medium_count))
    table.add_row("Low", str(summary.low_count))
    table.add_row("Info", str(summary.info_count))
    table.add_row("Security Score", f"{summary.security_score}/100")
    table.add_row("Risk Level", summary.risk_level.value)

    console.print(table)


def render_risk_profile(result: ScanResult) -> None:
    """
    Render advanced risk intelligence.
    """
    profile = result.risk_profile

    risk_table = Table(
        title="Advanced Risk Intelligence",
        show_header=True,
        header_style="bold cyan",
    )
    risk_table.add_column("Metric", style="white")
    risk_table.add_column("Value", style="green")

    risk_table.add_row("Overall Security Score", f"{profile.overall_security_score}/100")
    risk_table.add_row("Overall Risk Level", profile.overall_risk_level.value)
    risk_table.add_row("Build Gate Status", profile.build_gate_status)
    risk_table.add_row("Build Gate Reason", profile.build_gate_reason)

    console.print(risk_table)

    if profile.category_risks:
        category_table = Table(
            title="Category-wise Risk Breakdown",
            show_header=True,
            header_style="bold magenta",
        )
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Findings", justify="right")
        category_table.add_column("Penalty Points", justify="right")
        category_table.add_column("Risk Score", justify="right")
        category_table.add_column("Risk Level", style="red")

        for category_risk in profile.category_risks:
            category_table.add_row(
                category_risk.category.value,
                str(category_risk.finding_count),
                str(category_risk.penalty_points),
                f"{category_risk.risk_score}/100",
                category_risk.risk_level.value,
            )

        console.print(category_table)

    if profile.top_risk_drivers:
        driver_table = Table(
            title="Top Risk Drivers",
            show_header=True,
            header_style="bold red",
        )
        driver_table.add_column("Rank", justify="right")
        driver_table.add_column("Rule ID", style="cyan")
        driver_table.add_column("Severity", style="red")
        driver_table.add_column("Category", style="magenta")
        driver_table.add_column("Title", style="white")
        driver_table.add_column("File", style="green")
        driver_table.add_column("Line", justify="right")
        driver_table.add_column("Contribution", justify="right")

        for index, driver in enumerate(profile.top_risk_drivers, start=1):
            driver_table.add_row(
                str(index),
                driver.rule_id,
                driver.severity.value,
                driver.category.value,
                driver.title,
                driver.file_path,
                str(driver.line_number or "-"),
                str(driver.contribution_points),
            )

        console.print(driver_table)


def render_discovered_files(result: ScanResult) -> None:
    """
    Render discovered security-relevant files.
    """
    table = Table(
        title="Security-Relevant Files Discovered",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Relative Path", style="white")
    table.add_column("Type", style="cyan")
    table.add_column("Size", justify="right", style="green")

    for repo_file in result.discovered_files:
        table.add_row(
            repo_file.relative_path,
            repo_file.file_type,
            f"{repo_file.size_bytes} bytes",
        )

    console.print(table)


def render_findings(result: ScanResult) -> None:
    """
    Render all security findings with detailed explanation.
    """
    if not result.findings:
        console.print("[bold green]No security findings detected.[/bold green]")
        return

    table = Table(title="Security Findings", show_header=True, header_style="bold red")
    table.add_column("Rule ID", style="cyan")
    table.add_column("Severity", style="red")
    table.add_column("Category", style="magenta")
    table.add_column("Title", style="white")
    table.add_column("File", style="green")
    table.add_column("Line", justify="right")

    for finding in result.findings:
        table.add_row(
            finding.rule_id,
            finding.severity.value,
            finding.category.value,
            finding.title,
            finding.evidence.file_path,
            str(finding.evidence.line_number or "-"),
        )

    console.print(table)

    for finding in result.findings:
        border_style = (
            "red"
            if finding.severity.value in {"HIGH", "CRITICAL"}
            else "yellow"
        )

        details = (
            f"[bold]Description:[/bold] {finding.description}\n"
            f"[bold]Impact:[/bold] {finding.impact}\n"
            f"[bold]Evidence:[/bold] {finding.evidence.snippet or 'N/A'}\n"
            f"[bold]Remediation:[/bold] {finding.remediation}"
        )

        console.print(
            Panel.fit(
                details,
                title=f"{finding.rule_id} - {finding.severity.value}",
                border_style=border_style,
            )
        )


def render_comparison(comparison: ComparisonResult) -> None:
    """
    Render before/after repository security comparison.
    """
    table = Table(
        title="Before vs After Security Posture Comparison",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Metric", style="white")
    table.add_column(comparison.baseline_label, style="red")
    table.add_column(comparison.target_label, style="green")
    table.add_column("Delta", style="cyan")

    baseline = comparison.baseline.summary
    target = comparison.target.summary

    table.add_row(
        "Security Score",
        f"{baseline.security_score}/100",
        f"{target.security_score}/100",
        f"{comparison.score_delta:+d}",
    )
    table.add_row(
        "Risk Level",
        baseline.risk_level.value,
        target.risk_level.value,
        "-",
    )
    table.add_row(
        "Findings",
        str(baseline.findings_count),
        str(target.findings_count),
        str(target.findings_count - baseline.findings_count),
    )
    table.add_row(
        "Critical Findings",
        str(baseline.critical_count),
        str(target.critical_count),
        str(target.critical_count - baseline.critical_count),
    )
    table.add_row(
        "High Findings",
        str(baseline.high_count),
        str(target.high_count),
        str(target.high_count - baseline.high_count),
    )
    table.add_row(
        "Build Gate",
        comparison.baseline.risk_profile.build_gate_status,
        comparison.target.risk_profile.build_gate_status,
        "-",
    )

    console.print(table)

    summary = (
        f"[bold]Verdict:[/bold] {comparison.verdict}\n"
        f"[bold]Score Improvement:[/bold] {comparison.score_delta:+d} points\n"
        f"[bold]Findings Reduced:[/bold] {comparison.findings_reduced}\n"
        f"[bold]Risk Reduction:[/bold] {comparison.risk_reduction_percentage}%"
    )

    border_style = "green" if comparison.score_delta > 0 else "red"

    console.print(
        Panel.fit(
            summary,
            title="Comparison Summary",
            border_style=border_style,
        )
    )