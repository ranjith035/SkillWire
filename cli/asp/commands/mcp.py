"""
asp mcp — MCP server that exposes installed ASP skills as prompts.

This server implements the Model Context Protocol (MCP) over stdio,
allowing Claude Code, Gemini CLI, and any MCP-compatible client to
access installed ASP skills as native MCP prompts.

Protocol: JSON-RPC 2.0 over stdio
Capabilities exposed: prompts/list, prompts/get
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Optional

import typer
from rich.console import Console

from asp import __protocol_version__, __version__
from asp.core.manifest import load_manifest
from asp.core.registry import InstalledSkillsDB
from asp.errors import ASPError

console = Console()

# MCP logging MUST go to stderr — stdout is the protocol channel
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[asp-mcp] %(levelname)s %(message)s",
)
logger = logging.getLogger("asp.mcp")


# ---------------------------------------------------------------------------
# MCP Server — stdio JSON-RPC 2.0
# ---------------------------------------------------------------------------


class ASPMCPServer:
    """
    Minimal MCP server that exposes ASP skills as MCP prompts.

    Reads JSON-RPC requests from stdin, writes responses to stdout.
    Never writes non-JSON to stdout.
    """

    def __init__(self) -> None:
        self.db = InstalledSkillsDB()
        self._initialized = False

    def run(self) -> None:
        """Main event loop — reads lines from stdin, handles requests."""
        logger.info(f"ASP MCP Server v{__version__} starting. Reading from stdin...")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                self._write_error(None, -32700, "Parse error")
                continue

            self._handle(request)

    def _handle(self, req: dict[str, Any]) -> None:
        """Dispatch a JSON-RPC request."""
        req_id = req.get("id")
        method = req.get("method", "")

        logger.info(f"← {method} (id={req_id})")

        try:
            if method == "initialize":
                result = self._on_initialize(req.get("params", {}))
            elif method == "initialized":
                # Notification — no response needed
                self._initialized = True
                return
            elif method == "prompts/list":
                result = self._on_prompts_list(req.get("params", {}))
            elif method == "prompts/get":
                result = self._on_prompts_get(req.get("params", {}))
            elif method == "ping":
                result = {}
            else:
                self._write_error(req_id, -32601, f"Method not found: {method}")
                return

            self._write_response(req_id, result)
        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            self._write_error(req_id, -32603, f"Internal error: {e}")

    def _on_initialize(self, params: dict) -> dict:
        """Handle MCP initialize handshake."""
        client_info = params.get("clientInfo", {})
        logger.info(f"Client: {client_info.get('name', 'unknown')} {client_info.get('version', '')}")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "prompts": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": "asp",
                "version": __version__,
            },
        }

    def _on_prompts_list(self, params: dict) -> dict:
        """Return all installed skills as MCP prompts."""
        records = self.db.list_installed()
        prompts = []

        for record in records:
            skill_id = record.get("id", "")
            manifest_path = self.db.get_installed_manifest_path(skill_id)
            if not manifest_path:
                continue

            try:
                manifest = load_manifest(manifest_path)
            except ASPError as e:
                logger.warning(f"Skipping {skill_id}: {e}")
                continue

            # Convert skill inputs to MCP prompt arguments
            arguments = [
                {
                    "name": inp.name,
                    "description": inp.description,
                    "required": inp.required,
                }
                for inp in manifest.inputs
            ]

            prompts.append({
                "name": manifest.name,
                "description": f"{manifest.description} (v{manifest.version})",
                "arguments": arguments,
            })

        logger.info(f"→ prompts/list: {len(prompts)} skill(s)")
        return {"prompts": prompts}

    def _on_prompts_get(self, params: dict) -> dict:
        """Return a specific skill as an MCP prompt with rendered messages."""
        prompt_name = params.get("name", "")
        arguments = params.get("arguments", {})

        # Find the installed skill
        records = self.db.list_installed()
        record = next((r for r in records if r.get("name") == prompt_name), None)

        if not record:
            raise ValueError(f"Prompt '{prompt_name}' not found. Run 'asp install' first.")

        skill_id = record.get("id", "")
        manifest_path = self.db.get_installed_manifest_path(skill_id)
        if not manifest_path:
            raise ValueError(f"Skill '{skill_id}' installation is corrupted.")

        manifest = load_manifest(manifest_path)

        # Render the prompt with provided argument values
        try:
            rendered_text = manifest.render_input(arguments)
        except ValueError as e:
            raise ValueError(f"Invalid skill input: {e}") from e

        logger.info(f"→ prompts/get: {prompt_name} with args {list(arguments.keys())}")

        return {
            "description": manifest.description,
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": rendered_text,
                    },
                }
            ],
        }

    def _write_response(self, req_id: Any, result: Any) -> None:
        """Write a successful JSON-RPC response to stdout."""
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }
        self._write_json(response)

    def _write_error(self, req_id: Any, code: int, message: str) -> None:
        """Write a JSON-RPC error response to stdout."""
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
        self._write_json(response)

    @staticmethod
    def _write_json(obj: Any) -> None:
        """Write a JSON object as a single line to stdout and flush."""
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


def serve_command() -> None:
    """
    Start the ASP MCP server on stdio.

    This server exposes all installed ASP skills as MCP prompts,
    making them available to Claude Code, Gemini CLI, and any
    MCP-compatible AI tool.

    Add to Claude Code config (~/.claude/claude_desktop_config.json):

      {
        "mcpServers": {
          "asp": {
            "command": "asp",
            "args": ["mcp", "serve"]
          }
        }
      }
    """
    server = ASPMCPServer()
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped.")


def info_command() -> None:
    """
    Show MCP configuration snippets for Claude Code and Gemini CLI.

    Displays the JSON to add to your AI tool's configuration file.
    """
    import json

    console.print()
    console.print("[bold]ASP MCP Server[/bold] — exposes your installed skills to AI tools\n")

    claude_config = {
        "mcpServers": {
            "asp": {
                "command": "asp",
                "args": ["mcp", "serve"],
                "description": "AI Skill Protocol — installed skills as prompts",
            }
        }
    }

    gemini_config = {
        "mcpServers": {
            "asp": {
                "command": "asp",
                "args": ["mcp", "serve"],
            }
        }
    }

    console.print("[bold cyan]Claude Code[/bold cyan] — add to [cyan]~/.claude/claude_desktop_config.json[/cyan]:")
    console.print()
    console.print_json(json.dumps(claude_config, indent=2))

    console.print()
    console.print("[bold cyan]Gemini CLI[/bold cyan] — add to [cyan]~/.gemini/settings.json[/cyan]:")
    console.print()
    console.print_json(json.dumps(gemini_config, indent=2))

    console.print()
    console.print("[dim]After configuring your AI tool, install skills with:[/dim]")
    console.print("[cyan]  asp install github:owner/skill-repo[/cyan]")
    console.print()
    console.print("[dim]The MCP server starts automatically when your AI tool needs it.[/dim]")
    console.print()
