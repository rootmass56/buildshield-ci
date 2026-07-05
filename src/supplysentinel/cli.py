from pathlib import Path

import typer
from rich.table import Table

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
from supplysentinel.inventory.dependency_inventory import (
    DependencyInventory,
    build_dependency_inventory,
    write_inventory_json,
)
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


def default_inventory_report_path(target: str) -> str:
    target_name = Path(target).name or "repository"
    return f"reports/{target_name}-dependency-inventory.json"


def generate_scan_report_by_format(result, report_format: str) -> str:
    if report_format == "sarif":
        return generate_scan_sarif(result)

    return generate_scan_report(result, report_format)


def render_dependency_inventory(
    inventory: DependencyInventory,
    show_packages: bool,
) -> None:
    summary = inventory.summary

    summary_table = Table(
        title="SBOM-lite Dependency Inventory Summary",
        show_header=True,
        header_style="bold cyan",
    )
    summary_table.add_column("Metric", style="white")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Target Path", inventory.target_path)
    summary_table.add_row("Total Dependencies", str(summary.total_dependencies))
    summary_table.add_row("npm Dependencies", str(summary.npm_dependencies))
    summary_table.add_row("Python Dependencies", str(summary.python_dependencies))
    summary_table.add_row("Pinned Dependencies", str(summary.pinned_dependencies))
    summary_table.add_row("Loose Dependencies", str(summary.loose_dependencies))
    summary_table.add_row("Unpinned Dependencies", str(summary.unpinned_dependencies))
    summary_table.add_row(
        "Internal Candidates",
        str(summary.internal_candidate_dependencies),
    )
    summary_table.add_row(
        "Missing Private Registry",
        str(summary.dependencies_missing_private_registry),
    )
    summary_table.add_row(
        "npm Dependencies Without Lockfile",
        str(summary.npm_dependencies_without_lockfile),
    )
    summary_table.add_row(
        "Ecosystems",
        ", ".join(summary.ecosystems_detected) or "None",
    )

    console.print(summary_table)

    if not show_packages:
        return

    if not inventory.dependencies:
        console.print("[bold green]No dependencies discovered.[/bold green]")
        return

    package_table = Table(
        title="Dependency Inventory",
        show_header=True,
        header_style="bold magenta",
    )
    package_table.add_column("Ecosystem", style="cyan")
    package_table.add_column("Package", style="white")
    package_table.add_column("Version", style="green")
    package_table.add_column("Group", style="magenta")
    package_table.add_column("Pinned", style="yellow")
    package_table.add_column("Internal", style="red")
    package_table.add_column("File", style="blue")
    package_table.add_column("Risk Indicators", style="red")

    for dependency in inventory.dependencies:
        package_table.add_row(
            dependency.ecosystem,
            dependency.name,
            dependency.declared_version or "-",
            dependency.dependency_group,
            "YES" if dependency.is_pinned else "NO",
            "YES" if dependency.is_internal_candidate else "NO",
            dependency.file_path,
            ", ".join(dependency.risk_indicators),
        )

    console.print(package_table)


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
def inventory(
    target: str = typer.Argument(
        ".",
        help="Path to repository for SBOM-lite dependency inventory.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write inventory JSON report to this path.",
    ),
    show_packages: bool = typer.Option(
        True,
        "--show-packages/--hide-packages",
        help="Show individual dependency records.",
    ),
):
    """
    Generate SBOM-lite dependency inventory for npm and Python projects.
    """
    render_banner()

    try:
        dependency_inventory = build_dependency_inventory(target)
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    render_dependency_inventory(
        inventory=dependency_inventory,
        show_packages=show_packages,
    )

    if output:
        output_path = output
    else:
        output_path = default_inventory_report_path(target)

    written_path = write_inventory_json(
        inventory=dependency_inventory,
        output_path=output_path,
    )

    console.print(
        f"[bold green]Dependency inventory written to:[/bold green] {written_path}"
    )


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
def dashboard(
    host: str = typer.Option("127.0.0.1", "--host", help="Dashboard host."),
    port: int = typer.Option(8080, "--port", help="Dashboard port."),
    reload: bool = typer.Option(
        False,
        "--reload/--no-reload",
        help="Enable auto-reload during development.",
    ),
):
    """
    Launch the BuildShield-CI web dashboard.
    """
    import uvicorn

    console.print(
        f"[bold cyan]Starting {PRODUCT_NAME} dashboard[/bold cyan] "
        f"at [bold green]http://{host}:{port}[/bold green]"
    )

    uvicorn.run(
        "supplysentinel.web.app:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def version():
    """
    Show BuildShield-CI version.
    """
    console.print(f"{PRODUCT_NAME} version: [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()