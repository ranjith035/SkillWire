"""asp list — list installed skills."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from asp.core.registry import InstalledSkillsDB

console = Console()


def command(
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON for machine-readable use.",
    ),
) -> None:
    """
    List all installed ASP skills.

    Shows name, version, ID, source, and installation date.
    """
    db = InstalledSkillsDB()
    records = db.list_installed()

    if output_json:
        console.print_json(json.dumps(records, indent=2))
        return

    if not records:
        console.print(Panel(
            Text.assemble(
                ("No skills installed.\n\n", "dim"),
                ("Install one with:\n", "white"),
                ("  asp install github:owner/skill-repo\n", "cyan"),
            ),
            title="Installed Skills",
            border_style="dim",
        ))
        return

    table = Table(
        title=f"Installed Skills ({len(records)})",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="white bold", min_width=16)
    table.add_column("Version", style="cyan", min_width=10)
    table.add_column("ID", style="dim", min_width=30)
    table.add_column("Source", style="dim", min_width=24)
    table.add_column("Installed", style="dim")

    for r in records:
        installed_at = r.get("installed_at", "")[:10]  # date only
        table.add_row(
            r.get("name", ""),
            r.get("version", ""),
            r.get("id", ""),
            _truncate(r.get("source_url", ""), 30),
            installed_at,
        )

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]To use in Claude Code:[/dim] [cyan]asp generate claude[/cyan]")
    console.print("[dim]To use in Gemini CLI: [/dim] [cyan]asp generate gemini[/cyan]")
    console.print("[dim]Via MCP:              [/dim] [cyan]asp mcp serve[/cyan]")
    console.print()


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."
