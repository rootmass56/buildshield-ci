from pathlib import Path

import typer

from supplysentinel.core.comparison import build_comparison_result
from supplysentinel.core.exceptions import SupplySentinelError
from supplysentinel.core.output import (
    console,
    render_banner,
    render_comparison,
    render_discovered_files,
    render_findings,
    render_risk_profile,
    render_scan_summary,
)
from supplysentinel.core.scanner import scan_repository
from supplysentinel.reporters.report_generator import (
    generate_comparison_report,
    generate_scan_report,
    write_report,
)


app = typer.Typer(
    help="SupplySentinel: Advanced CI/CD Supply Chain Risk Detection Platform"
)


def validate_report_format(report_format: str) -> str:
    """
    Validate report format provided by user.
    """
    normalized_format = report_format.lower().strip()

    if normalized_format not in {"json", "md", "html"}:
        raise typer.BadParameter("Report format must be one of: json, md, html")

    return normalized_format


def default_scan_report_path(target: str, report_format: str) -> str:
    """
    Build default scan report output path.
    """
    target_name = Path(target).name or "repository"
    return f"reports/{target_name}-scan-report.{report_format}"


def default_comparison_report_path(report_format: str) -> str:
    """
    Build default comparison report output path.
    """
    return f"reports/comparison-report.{report_format}"


@app.command()
def scan(
    target: str = typer.Argument(".", help="Path to repository to scan"),
    show_files: bool = typer.Option(
        True,
        "--show-files/--hide-files",
        help="Show security-relevant files discovered during scan.",
    ),
    report_format: str | None = typer.Option(
        None,
        "--report-format",
        help="Generate report in selected format: json, md, html.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Report output file path.",
    ),
):
    """
    Scan a repository for dependency confusion and CI/CD supply-chain risks.
    """
    render_banner()

    try:
        result = scan_repository(target)
    except SupplySentinelError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    render_scan_summary(result)
    render_risk_profile(result)

    if show_files:
        render_discovered_files(result)

    render_findings(result)

    if report_format:
        normalized_format = validate_report_format(report_format)
        report_content = generate_scan_report(result, normalized_format)

        output_path = output or default_scan_report_path(
            target=target,
            report_format=normalized_format,
        )

        written_path = write_report(output_path, report_content)
        console.print(f"[bold green]Report written to:[/bold green] {written_path}")


@app.command()
def compare(
    baseline: str = typer.Argument(
        ...,
        help="Path to baseline or vulnerable repository.",
    ),
    target: str = typer.Argument(
        ...,
        help="Path to target or hardened repository.",
    ),
    baseline_label: str = typer.Option(
        "Vulnerable Repo",
        "--baseline-label",
        help="Display label for baseline repository.",
    ),
    target_label: str = typer.Option(
        "Secure Repo",
        "--target-label",
        help="Display label for target repository.",
    ),
    report_format: str | None = typer.Option(
        None,
        "--report-format",
        help="Generate comparison report in selected format: json, md, html.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Comparison report output file path.",
    ),
):
    """
    Compare two repositories and show security posture improvement.
    """
    render_banner()

    try:
        baseline_result = scan_repository(baseline)
        target_result = scan_repository(target)
    except SupplySentinelError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    comparison = build_comparison_result(
        baseline=baseline_result,
        target=target_result,
        baseline_label=baseline_label,
        target_label=target_label,
    )

    render_comparison(comparison)

    if report_format:
        normalized_format = validate_report_format(report_format)
        report_content = generate_comparison_report(comparison, normalized_format)

        output_path = output or default_comparison_report_path(
            report_format=normalized_format,
        )

        written_path = write_report(output_path, report_content)
        console.print(f"[bold green]Report written to:[/bold green] {written_path}")


@app.command()
def version():
    """
    Show SupplySentinel version.
    """
    from supplysentinel import __version__

    console.print(f"SupplySentinel version: [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()