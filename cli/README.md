# asp — AI Skill Protocol CLI

Reference CLI for the [AI Skill Protocol (ASP)](../README.md).

## Installation

```bash
pip install asp-cli
```

## Commands

| Command | Description |
|---|---|
| `asp init` | Scaffold a new skill directory |
| `asp validate` | Validate skill.yaml against the JSON Schema |
| `asp pack` | Create a .skill distributable package |
| `asp install github:owner/repo` | Install a skill from GitHub |
| `asp list` | List installed skills |
| `asp search <query>` | Search for skills |
| `asp generate claude` | Generate Claude Code adapter files |
| `asp generate gemini` | Generate Gemini CLI adapter files |
| `asp mcp serve` | Start the MCP server (for Claude Code / Gemini CLI) |
| `asp mcp info` | Show MCP configuration snippets |

## MCP Integration

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "asp": {
      "command": "asp",
      "args": ["mcp", "serve"]
    }
  }
}
```

Then install skills and they appear automatically in Claude Code.
