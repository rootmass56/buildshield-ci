from pathlib import Path

import typer

from supplysentinel import DESCRIPTION, PRODUCT_NAME, __version__
from supplysentinel.core.comparison import build_comparison_result
from supplysentinel.core.exceptions import SupplySentinelError
from supplysentinel.core.output import (
    console,
    render_banner,
    render_comparison,
    render_discovered_files,
    render_findings,
    render_policy_evaluation,
    render_risk_profile,
    render_scan_summary,
)
from supplysentinel.core.scanner import scan_repository
from supplysentinel.policies.policy_engine import evaluate_policy
from supplysentinel.reporters.report_generator import (
    generate_comparison_report,
    generate_scan_report,
    write_report,
)
from supplysentinel.reporters.sarif_reporter import generate_scan_sarif


app = typer.Typer(
    help=f"{PRODUCT_NAME}: {DESCRIPTION}"
)


def validate_scan_report_format(report_format: str) -> str:
    normalized_format = report_format.lower().strip()

    if normalized_format not in {"json", "md", "html", "sarif"}:
        raise typer.BadParameter("Report format must be one of: json, md, html, sarif")

    return normalized_format


def validate_comparison_report_format(report_format: str) -> str:
    normalized_format = report_format.lower().strip()

    if normalized_format not in {"json", "md", "html"}:
        raise typer.BadParameter("Comparison report format must be one of: json, md, html")

    return normalized_format


def default_scan_report_path(target: str, report_format: str) -> str:
    target_name = Path(target).name or "repository"
    return f"reports/{target_name}-scan-report.{report_format}"


def default_comparison_report_path(report_format: str) -> str:
    return f"reports/comparison-report.{report_format}"


def generate_scan_report_by_format(result, report_format: str) -> str:
    if report_format == "sarif":
        return generate_scan_sarif(result)

    return generate_scan_report(result, report_format)


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
        help="Generate report in selected format: json, md, html, sarif.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Report output file path.",
    ),
    policy: str | None = typer.Option(
        None,
        "--policy",
        "-p",
        help="Path to policy-as-code YAML file.",
    ),
    fail_on_policy: bool = typer.Option(
        False,
        "--fail-on-policy/--no-fail-on-policy",
        help="Exit with non-zero code if policy evaluation fails.",
    ),
):
    """
    Scan a repository for CI/CD supply-chain and dependency confusion risks.
    """
    render_banner()

    try:
        result = scan_repository(target)

        if policy:
            policy_evaluation = evaluate_policy(
                result=result,
                policy_path=policy,
            )
            result = result.model_copy(
                update={"policy_evaluation": policy_evaluation}
            )

    except (SupplySentinelError, FileNotFoundError, ValueError) as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    render_scan_summary(result)
    render_risk_profile(result)
    render_policy_evaluation(result)

    if show_files:
        render_discovered_files(result)

    render_findings(result)

    if report_format:
        normalized_format = validate_scan_report_format(report_format)
        report_content = generate_scan_report_by_format(result, normalized_format)

        output_path = output or default_scan_report_path(
            target=target,
            report_format=normalized_format,
        )

        written_path = write_report(output_path, report_content)
        console.print(f"[bold green]Report written to:[/bold green] {written_path}")

    if policy and fail_on_policy and result.policy_evaluation and not result.policy_evaluation.passed:
        console.print("[bold red]Policy failed. Exiting with code 2 for CI/CD gate.[/bold red]")
        raise typer.Exit(code=2)


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
    Compare vulnerable and hardened repositories to measure security improvement.
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
        normalized_format = validate_comparison_report_format(report_format)
        report_content = generate_comparison_report(comparison, normalized_format)

        output_path = output or default_comparison_report_path(
            report_format=normalized_format,
        )

        written_path = write_report(output_path, report_content)
        console.print(f"[bold green]Report written to:[/bold green] {written_path}")


@app.command()
def version():
    """
    Show BuildShield-CI version.
    """
    console.print(f"{PRODUCT_NAME} version: [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()