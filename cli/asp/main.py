"""
ASP CLI entry point.

Registers all commands and subcommands. The 'asp' script in PATH
maps to the app() callable here.
"""

from __future__ import annotations

from typing import Optional

import typer
from asp.console import console
from asp import __version__
from asp.commands import generate, init, install, list_, mcp, pack, search, validate

app = typer.Typer(
    name="asp",
    help=(
        "[bold]ASP[/bold] — AI Skill Protocol\n\n"
        "Package, distribute, and consume reusable AI skills across "
        "Claude Code, Gemini CLI, and any AI runtime."
    ),
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# MCP subcommand group
# ---------------------------------------------------------------------------

mcp_app = typer.Typer(
    name="mcp",
    help="MCP server integration — expose installed skills to Claude Code and Gemini CLI.",
    rich_markup_mode="rich",
)
app.add_typer(mcp_app, name="mcp")


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Start the ASP MCP server on stdio (for use with Claude Code / Gemini CLI)."""
    mcp.serve_command()


@mcp_app.command("info")
def mcp_info() -> None:
    """Show MCP configuration snippets for Claude Code and Gemini CLI."""
    mcp.info_command()


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------


app.command("init")(init.command)
app.command("validate")(validate.command)
app.command("pack")(pack.command)
app.command("install")(install.command)
app.command("list")(list_.command)
app.command("search")(search.command)
app.command("generate")(generate.command)


# ---------------------------------------------------------------------------
# Version callback
# ---------------------------------------------------------------------------


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"asp [bold]{__version__}[/bold]  (protocol [cyan]{__version__}[/cyan])")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """AI Skill Protocol reference CLI."""


if __name__ == "__main__":
    app()
