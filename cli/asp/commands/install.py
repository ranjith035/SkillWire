"""asp install — install a skill from GitHub or local path."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from asp.core.integrity import generate_lockfile, sha256_file, write_lockfile
from asp.core.manifest import load_manifest
from asp.core.registry import GitRegistry, InstalledSkillsDB, parse_source
from asp.core.resolver import DependencyResolver
from asp.errors import ASPError

console = Console()


def command(
    source: str = typer.Argument(
        ...,
        help="Skill source: 'github:owner/repo', 'github:owner/repo@1.2.0', or local path.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be installed without making changes.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip permission confirmation prompts.",
    ),
) -> None:
    """
    Install a skill from GitHub or a local path.

    Examples:
      asp install github:your-org/code-review-skill
      asp install github:your-org/code-review-skill@1.2.0
      asp install ./my-local-skill/
    """
    console.print(f"\nInstalling [cyan]{source}[/cyan]...\n")

    db = InstalledSkillsDB()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)

        # Download / copy skill
        try:
            registry = parse_source(source)
            console.print(f"  [dim]Fetching from {type(registry).__name__}...[/dim]")

            record = registry.get(source)
            skill_dir = registry.download(record, tmp_dir)
        except ASPError as e:
            console.print(f"\n[red]✗ {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"\n[red]✗ Failed to download: {e}[/red]")
            raise typer.Exit(1)

        # Load and validate manifest
        manifest_path = skill_dir / "skill.yaml"
        if not manifest_path.exists():
            console.print(
                f"[red]✗ No skill.yaml found in downloaded source.[/red]\n"
                "  Make sure the repository contains a skill.yaml at its root."
            )
            raise typer.Exit(1)

        try:
            manifest = load_manifest(manifest_path)
        except ASPError as e:
            console.print(f"\n[red]✗ Invalid skill manifest:\n{e}[/red]")
            raise typer.Exit(1)

        # Show skill info
        console.print(f"  [dim]Found:[/dim] [white bold]{manifest.name}[/white bold] "
                      f"[dim]v{manifest.version}[/dim]")
        console.print(f"  [dim]{manifest.description}[/dim]\n")

        # Permission check
        if manifest.permissions.has_non_default() and not yes:
            perms = manifest.permissions.to_list()
            console.print(Panel(
                Text.assemble(
                    ("This skill requests the following permissions:\n\n", "yellow"),
                    *[Text(f"  ⚠  {p}\n", style="yellow") for p in perms],
                    ("\nOnly install skills you trust.", "dim"),
                ),
                title="[yellow]⚠ Permission Request[/yellow]",
                border_style="yellow",
            ))
            if not typer.confirm("Proceed with installation?"):
                console.print("[dim]Installation cancelled.[/dim]")
                raise typer.Exit(0)

        # Dependency resolution
        resolver = DependencyResolver(registry=None)
        try:
            resolved = resolver.resolve(manifest)
        except ASPError as e:
            console.print(f"\n[red]✗ Dependency resolution failed:\n{e}[/red]")
            raise typer.Exit(1)

        if resolved:
            console.print("  [dim]Resolved dependencies:[/dim]")
            for dep_id, dep_ver in resolved.items():
                console.print(f"    [cyan]{dep_id}[/cyan] → {dep_ver}")
            console.print()

        if dry_run:
            console.print(Panel(
                f"[green]Would install:[/green] {manifest.name}@{manifest.version}\n"
                f"[dim]Dry run — no changes made.[/dim]",
                border_style="dim",
            ))
            return

        # Generate lockfile
        lock = generate_lockfile(manifest_path, manifest)
        write_lockfile(lock, skill_dir)

        # Compute SHA-256
        pkg_sha256 = sha256_file(manifest_path)

        # Install to ~/.asp/skills/
        install_dir = db.skills_dir / manifest.name
        if install_dir.exists():
            shutil.rmtree(install_dir)
        shutil.copytree(skill_dir, install_dir)

        # Record installation
        db.install(manifest, source_url=source, sha256=pkg_sha256)

    console.print(Panel(
        Text.assemble(
            ("✓ Installed ", "green bold"),
            (f"{manifest.name}", "cyan bold"),
            (f"@{manifest.version}\n\n", "dim"),
            ("  Use it:\n", "white"),
            ("  • MCP:     ", "dim"), ("asp mcp serve\n", "cyan"),
            ("  • Claude:  ", "dim"), ("asp generate claude\n", "cyan"),
            ("  • Gemini:  ", "dim"), ("asp generate gemini\n", "cyan"),
        ),
        title="[green]Installation Complete[/green]",
        border_style="green",
    ))
