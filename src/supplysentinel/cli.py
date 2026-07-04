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


app = typer.Typer(
    help="SupplySentinel: Advanced CI/CD Supply Chain Risk Detection Platform"
)


@app.command()
def scan(
    target: str = typer.Argument(".", help="Path to repository to scan"),
    show_files: bool = typer.Option(
        True,
        "--show-files/--hide-files",
        help="Show security-relevant files discovered during scan.",
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


@app.command()
def version():
    """
    Show SupplySentinel version.
    """
    from supplysentinel import __version__

    console.print(f"SupplySentinel version: [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()