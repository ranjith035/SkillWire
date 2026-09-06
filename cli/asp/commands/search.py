"""asp search — search for skills in registries."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def command(
    query: str = typer.Argument(..., help="Search term (name, tag, or description)."),
    registry_url: Optional[str] = typer.Option(
        None,
        "--registry",
        "-r",
        help="Registry URL to search. Defaults to GitHub topic search.",
    ),
) -> None:
    """
    Search for ASP skills in public registries.

    In the MVP, this searches GitHub repositories tagged with the
    'asp-skill' topic. Use --registry to search a custom HTTP registry.
    """
    console.print(f"\nSearching for [cyan]{query}[/cyan]...\n")

    if registry_url:
        _search_http_registry(query, registry_url)
    else:
        _search_github(query)


def _search_github(query: str) -> None:
    """Search GitHub for repositories with the asp-skill topic."""
    try:
        import httpx
    except ImportError:
        console.print("[red]✗ httpx not installed. Run: pip install httpx[/red]")
        raise typer.Exit(1)

    # GitHub topic search
    search_url = (
        f"https://api.github.com/search/repositories"
        f"?q={query}+topic:asp-skill&sort=stars&order=desc&per_page=20"
    )
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "asp-cli/0.1.0",
    }

    try:
        with httpx.Client(timeout=15, headers=headers) as client:
            r = client.get(search_url)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            console.print("[yellow]⚠ GitHub API rate limit reached. Try again in a few minutes.[/yellow]")
        else:
            console.print(f"[red]✗ GitHub API error: {e}[/red]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]✗ Network error: {e}[/red]")
        raise typer.Exit(1)

    items = data.get("items", [])
    total = data.get("total_count", 0)

    if not items:
        console.print(Panel(
            Text.assemble(
                (f"No skills found for '{query}'\n\n", "dim"),
                ("To publish your skill, add the [bold]asp-skill[/bold] topic\n"
                 "to your GitHub repository.\n\n", "white"),
                ("  github.com/your-repo → Settings → Topics → asp-skill", "cyan"),
            ),
            title="No Results",
            border_style="dim",
        ))
        return

    console.print(f"[dim]Found {total} result(s) on GitHub (showing up to 20)[/dim]\n")

    table = Table(
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Repository", style="cyan", min_width=30)
    table.add_column("Description", style="white", min_width=40)
    table.add_column("Stars", style="yellow", min_width=6)
    table.add_column("Install", style="dim", min_width=30)

    for item in items:
        full_name = item.get("full_name", "")
        description = item.get("description") or ""
        stars = str(item.get("stargazers_count", 0))
        install_cmd = f"github:{full_name}"

        table.add_row(
            full_name,
            description[:60] + ("..." if len(description) > 60 else ""),
            stars,
            install_cmd,
        )

    console.print(table)
    console.print()
    console.print("[dim]Install a skill:[/dim] [cyan]asp install github:owner/repo[/cyan]")
    console.print()


def _search_http_registry(query: str, registry_url: str) -> None:
    """Search a custom HTTP registry."""
    try:
        import httpx
    except ImportError:
        console.print("[red]✗ httpx not installed. Run: pip install httpx[/red]")
        raise typer.Exit(1)

    url = f"{registry_url.rstrip('/')}/v1/skills?q={query}"
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        console.print(f"[red]✗ Registry error: {e}[/red]")
        raise typer.Exit(1)

    skills = data.get("skills", [])
    if not skills:
        console.print(f"[dim]No results found at {registry_url}[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="dim")
    table.add_column("Description", style="white")

    for s in skills:
        table.add_row(s.get("name", ""), s.get("version", ""), s.get("description", ""))

    console.print(table)
