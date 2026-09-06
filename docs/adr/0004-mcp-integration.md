# ADR 0004 — MCP Integration: Skills as MCP Prompts

**Status:** Accepted  
**Date:** 2025-01-15  

---

## Context

Claude Code and Gemini CLI both support the **Model Context Protocol (MCP)**, which provides three primitive types: Resources (data), Tools (callable functions), and Prompts (parameterized templates).

ASP installed skills need to be accessible from these tools. We need to decide how to expose ASP skills to MCP clients.

---

## Decision

Expose ASP skills via the MCP **Prompts** primitive (`prompts/list` and `prompts/get`).

### Why Prompts, not Tools or Resources?

| MCP Primitive | Description | Fits Skills? |
|---|---|---|
| **Prompts** | Parameterized prompt templates with typed arguments | ✅ Perfect fit |
| **Tools** | Callable functions with schemas | ⚠️ Skills aren't side-effectful functions |
| **Resources** | Read-only data/file access | ❌ Skills aren't static data |

An ASP skill is fundamentally a parameterized prompt template — it has named inputs (prompt arguments), instructions (the prompt body), and produces text output. This maps exactly to the MCP Prompt primitive.

### Mapping

**ASP skill.yaml → MCP prompt:**

```yaml
# skill.yaml
name: "code-review"
description: "Reviews source code for issues"
inputs:
  - name: code
    required: true
  - name: language
    required: false
```

Becomes MCP `prompts/list` entry:

```json
{
  "name": "code-review",
  "description": "Reviews source code for issues (v1.0.0)",
  "arguments": [
    {"name": "code", "description": "...", "required": true},
    {"name": "language", "description": "...", "required": false}
  ]
}
```

### MCP Server Architecture

The `asp mcp serve` command runs a lightweight JSON-RPC 2.0 server on stdio. When an MCP client (Claude Code, Gemini CLI) calls `prompts/get` with argument values, the server:

1. Loads the installed skill manifest
2. Validates the argument values against the skill's input schema
3. Calls `skill.render_input(arguments)` to produce a rendered prompt
4. Returns the rendered prompt as an MCP message

```json
{
  "description": "...",
  "messages": [{"role": "user", "content": {"type": "text", "text": "..."}}]
}
```

### File-based Adapter Fallback

For tools that don't support MCP, `asp generate claude` and `asp generate gemini` produce native adapter files (`.claude/skills/*.md`, `GEMINI.md`). These are less dynamic but require no running process.

---

## Consequences

- ASP MCP server must track the MCP specification for `prompts/list` and `prompts/get`
- When skills are installed/uninstalled, MCP clients must reconnect to see changes (MCP doesn't support hot-reload in v1)
- The MCP server is a separate process managed by the AI tool's MCP client lifecycle
- Skills with `code_execution: true` permissions should warn users in the MCP integration since the AI tool gains the ability to request these capabilities

## Future Consideration

When MCP adds `prompts/listChanged` notifications, the ASP server should emit them after `asp install` or `asp remove`.
