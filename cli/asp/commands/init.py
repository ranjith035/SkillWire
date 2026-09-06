"""asp init — scaffold a new skill directory."""

from __future__ import annotations

import re
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def _slugify(text: str) -> str:
    """Convert a string to lowercase-hyphen slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def command(
    directory: Path = typer.Argument(
        Path("."),
        help="Directory to initialize the skill in. Defaults to current directory.",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing skill.yaml."),
) -> None:
    """
    Initialize a new ASP skill in the specified directory.

    Creates skill.yaml, README.md, and an examples/ directory scaffold.
    """
    target = directory.resolve()
    manifest_path = target / "skill.yaml"

    if manifest_path.exists() and not force:
        console.print(
            f"[red]✗[/red] skill.yaml already exists at [cyan]{manifest_path}[/cyan]\n"
            "  Use [bold]--force[/bold] to overwrite."
        )
        raise typer.Exit(1)

    target.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit("[bold cyan]ASP Skill Initializer[/bold cyan]", border_style="cyan"))
    console.print()

    # Interactive prompts
    skill_name = typer.prompt("Skill name (e.g., code-review)")
    skill_name = _slugify(skill_name)

    description = typer.prompt("Description (one line)")
    author_name = typer.prompt("Author name", default="")
    author_github = typer.prompt("GitHub username (for skill ID)", default="")
    license_name = typer.prompt("License", default="MIT")

    # Build skill ID
    if author_github:
        skill_id = f"io.github.{_slugify(author_github)}.{skill_name}"
    else:
        skill_id = f"io.example.{skill_name}"

    # Build manifest
    manifest: dict = {
        "asp": "1.0",
        "id": skill_id,
        "name": skill_name,
        "version": "0.1.0",
        "description": description,
        "instructions": (
            f"You are an expert assistant specialized in {skill_name.replace('-', ' ')}.\n\n"
            "# Instructions\n\nDescribe what the skill should do here.\n\n"
            "## Format\n\nDescribe the expected output format here."
        ),
    }

    if author_name:
        manifest["authors"] = [{"name": author_name}]
        if author_github:
            manifest["authors"][0]["url"] = f"https://github.com/{author_github}"

    manifest["license"] = license_name

    manifest["inputs"] = [
        {
            "name": "input",
            "type": "string",
            "description": "Primary input for this skill.",
            "required": True,
        }
    ]

    manifest["outputs"] = [
        {
            "name": "result",
            "type": "string",
            "description": "The skill's output.",
        }
    ]

    manifest["capabilities"] = {"required": ["text_generation", "instruction_following"]}

    manifest["permissions"] = {
        "network": False,
        "filesystem": False,
        "code_execution": False,
    }

    manifest["metadata"] = {
        "tags": [skill_name],
        "created_at": _today(),
        "asp_compatible": ">=1.0.0",
    }

    # Write skill.yaml
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Write README stub
    readme_path = target / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            f"# {skill_name}\n\n{description}\n\n"
            "## Installation\n\n```bash\nasp install github:your-username/"
            f"{skill_name}-skill\n```\n\n"
            "## Usage\n\nDescribe how to use this skill.\n\n"
            "## License\n\n" + license_name + "\n",
            encoding="utf-8",
        )

    # Create examples directory
    examples_dir = target / "examples"
    examples_dir.mkdir(exist_ok=True)
    (examples_dir / ".gitkeep").touch()

    console.print()
    console.print(Panel(
        Text.assemble(
            ("✓ ", "green bold"),
            ("Skill initialized!\n\n", "white bold"),
            ("  Directory: ", "dim"), (str(target), "cyan"), ("\n", ""),
            ("  Skill ID:  ", "dim"), (skill_id, "cyan"), ("\n", ""),
            ("  Version:   ", "dim"), ("0.1.0", "cyan"), ("\n\n", ""),
            ("Next steps:\n", "white bold"),
            ("  1. Edit ", "dim"), ("skill.yaml", "cyan"), (" — add your instructions\n", "dim"),
            ("  2. ", "dim"), ("asp validate", "cyan"), (" — check for errors\n", "dim"),
            ("  3. ", "dim"), ("asp pack", "cyan"), (" — create distributable package\n", "dim"),
        ),
        title="[green]Success[/green]",
        border_style="green",
    ))


def _today() -> str:
    from datetime import date
    return date.today().isoformat()
