"""asp pack — create a distributable .skill package."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from asp.console import console
from asp.core.integrity import sha256_file
from asp.core.packager import pack_skill
from asp.errors import ASPError


def command(
    directory: Path = typer.Argument(
        Path("."),
        help="Skill directory to pack. Defaults to current directory.",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for the .skill file. Defaults to current directory.",
    ),
) -> None:
    """
    Pack a skill directory into a distributable .skill package.

    Validates the manifest, generates skill.lock, and creates a
    gzip-compressed tar archive named {name}-{version}.skill.
    """
    skill_dir = directory.resolve()
    out_dir = (output or Path(".")).resolve()

    console.print(f"\nPacking [cyan]{skill_dir}[/cyan]...\n")

    try:
        skill_path = pack_skill(skill_dir, out_dir)
    except ASPError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error: {e}[/red]")
        raise typer.Exit(1)

    # Compute package info for display
    size_bytes = skill_path.stat().st_size
    sha256 = sha256_file(skill_path)
    size_human = _format_size(size_bytes)

    # List package contents
    import tarfile
    with tarfile.open(skill_path, "r:gz") as tar:
        contents = sorted(m.name for m in tar.getmembers())

    # Display results
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim", width=14)
    table.add_column("Value", style="white")

    table.add_row("Package", f"[cyan]{skill_path.name}[/cyan]")
    table.add_row("Location", str(skill_path))
    table.add_row("Size", size_human)
    table.add_row("SHA-256", sha256[:16] + "..." + sha256[-8:])
    table.add_row("Contents", "\n" + "\n".join(f"  {c}" for c in contents))

    console.print(Panel(table, title="[green]✓ Package Created[/green]", border_style="green"))
    console.print()
    console.print("  Next: [cyan]asp install[/cyan] or share the .skill file")


def _format_size(size_bytes: int) -> str:
    """Format byte count as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"
