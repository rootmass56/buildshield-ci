from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from supplysentinel.core.models import ScanResult


console = Console()


def render_banner() -> None:
    banner = """
[bold cyan]SupplySentinel[/bold cyan]
Advanced CI/CD Supply Chain Risk Detection and Dependency Confusion Defense Platform
"""
    console.print(Panel.fit(banner, border_style="cyan"))


def render_scan_summary(result: ScanResult) -> None:
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


def render_discovered_files(result: ScanResult) -> None:
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
    if not result.findings:
        console.print(
            "[bold green]No security findings detected yet. "
            "Stage 1 only performs repository discovery.[/bold green]"
        )
        return

    table = Table(title="Security Findings", show_header=True, header_style="bold red")
    table.add_column("Rule ID")
    table.add_column("Severity")
    table.add_column("Category")
    table.add_column("Title")
    table.add_column("File")

    for finding in result.findings:
        table.add_row(
            finding.rule_id,
            finding.severity.value,
            finding.category.value,
            finding.title,
            finding.evidence.file_path,
        )

    console.print(table)