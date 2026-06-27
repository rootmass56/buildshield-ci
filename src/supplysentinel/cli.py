import typer

from supplysentinel.core.exceptions import SupplySentinelError
from supplysentinel.core.output import (
    console,
    render_banner,
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
def version():
    """
    Show SupplySentinel version.
    """
    from supplysentinel import __version__

    console.print(f"SupplySentinel version: [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()