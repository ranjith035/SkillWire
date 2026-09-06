"""asp validate — validate a skill manifest against the JSON Schema."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from asp.console import console
from asp.core.manifest import find_manifest, load_manifest, validate_manifest_dict
from asp.errors import ManifestError, ValidationError

import yaml


def command(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to skill.yaml or skill directory. Defaults to searching upward from cwd.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Also require examples and evaluation cases to be present.",
    ),
) -> None:
    """
    Validate a skill manifest (skill.yaml) against the ASP JSON Schema.

    Displays all validation errors at once with field-level context.
    Exits with code 0 on success, 1 on failure.
    """
    # Resolve manifest path
    try:
        if path is None:
            manifest_path = find_manifest()
        elif path.is_dir():
            manifest_path = path / "skill.yaml"
        elif path.name == "skill.yaml":
            manifest_path = path
        else:
            manifest_path = path / "skill.yaml"
    except ManifestError as e:
        console.print(f"\n[red]✗ {e}[/red]")
        raise typer.Exit(1)

    console.print(f"\nValidating [cyan]{manifest_path}[/cyan]...\n")

    # Load raw YAML (catch YAML parse errors before schema validation)
    try:
        with manifest_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except FileNotFoundError:
        console.print(f"[red]✗ File not found: {manifest_path}[/red]")
        raise typer.Exit(1)
    except yaml.YAMLError as e:
        console.print(f"[red]✗ Invalid YAML: {e}[/red]")
        raise typer.Exit(1)

    if not isinstance(raw, dict):
        console.print("[red]✗ skill.yaml must be a YAML mapping (key: value pairs)[/red]")
        raise typer.Exit(1)

    # Schema validation
    errors = validate_manifest_dict(raw)

    # Strict mode checks
    strict_warnings: list[str] = []
    if strict:
        if not raw.get("examples"):
            strict_warnings.append("No 'examples' defined. Add at least one input/output example.")
        if not raw.get("evaluation"):
            strict_warnings.append("No 'evaluation' cases defined. Add test cases for quality assurance.")
        if not raw.get("authors"):
            strict_warnings.append("No 'authors' defined. Add author information for attribution.")

    if errors:
        console.print(Panel(
            Text.assemble(
                (f"Found {len(errors)} error(s):\n\n", "red bold"),
                *[Text(f"  ✗ {err}\n", style="red") for err in errors],
            ),
            title="[red]Validation Failed[/red]",
            border_style="red",
        ))
        raise typer.Exit(1)

    # Success — print skill summary
    _print_success_panel(raw, manifest_path, strict_warnings)


def _print_success_panel(raw: dict, path: Path, warnings: list[str]) -> None:
    """Print a beautiful success panel with skill summary."""
    console.print("[green]✓ Manifest is valid[/green]\n")

    # Summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim", width=16)
    table.add_column("Value", style="white")

    table.add_row("Name", f"[cyan]{raw.get('name', '')}[/cyan]")
    table.add_row("Version", f"[cyan]{raw.get('version', '')}[/cyan]")
    table.add_row("ID", str(raw.get("id", "")))
    table.add_row("Description", str(raw.get("description", "")))

    inputs = raw.get("inputs", [])
    if inputs:
        input_list = ", ".join(f"{i['name']} ({'required' if i.get('required', True) else 'optional'})" for i in inputs)
        table.add_row("Inputs", input_list)

    outputs = raw.get("outputs", [])
    if outputs:
        output_list = ", ".join(o["name"] for o in outputs)
        table.add_row("Outputs", output_list)

    deps = raw.get("dependencies", [])
    if deps:
        dep_list = ", ".join(f"{d['id']}@{d['version']}" for d in deps)
        table.add_row("Dependencies", dep_list)

    perms = raw.get("permissions", {})
    if any(perms.values()):
        perm_list = ", ".join(k for k, v in perms.items() if v)
        table.add_row("Permissions", f"[yellow]{perm_list}[/yellow]")
    else:
        table.add_row("Permissions", "[green]none (sandboxed)[/green]")

    console.print(Panel(table, title="[green]Skill Summary[/green]", border_style="green"))

    if warnings:
        console.print()
        for w in warnings:
            console.print(f"  [yellow]⚠[/yellow] {w}")
