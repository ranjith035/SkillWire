# SkillWire — AI Skill Protocol (ASP)

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()
[![Protocol](https://img.shields.io/badge/protocol-ASP%201.0-green.svg)]()

> **SkillWire is an open, vendor-neutral protocol for packaging, versioning, distributing, and consuming reusable AI skills — across Claude Code, Gemini CLI, GPT, and any AI runtime.**

---

## Why ASP?

Right now, every AI application invents its own skill format. A "code review" prompt written for Claude Code cannot be installed in Gemini CLI. A skill built for LangChain cannot be consumed by a VS Code agent. There is no:

- Versioning (`code-review@1.2.0`)
- Schema validation (typed inputs/outputs)
- Dependency management (skill A depends on skill B)
- Integrity verification (SHA-256 checksums)
- Discoverability (searchable registry)
- Portability (write once, run on any AI runtime)

ASP fixes this. It is to AI skills what `npm` is to JavaScript packages — a packaging standard, not a framework.

---

## Quick Start

```bash
# Install the reference CLI
pip install asp-cli

# Create a new skill
mkdir my-skill && cd my-skill
asp init

# Validate it
asp validate

# Pack it for distribution
asp pack

# Install a skill from GitHub
asp install github:your-org/code-review-skill

# Use it in Claude Code or Gemini CLI
asp mcp serve          # exposes all installed skills via MCP
asp generate claude    # generates .claude/skills/ adapter files
asp generate gemini    # generates GEMINI.md skill blocks
```

---

## A Minimal Skill

```yaml
# skill.yaml
asp: "1.0"

id: "io.github.yourname.code-review"
name: "code-review"
version: "1.0.0"
description: "Reviews source code for bugs, security issues, and style."

inputs:
  - name: code
    type: string
    description: "Source code to review"
    required: true

outputs:
  - name: review
    type: string
    description: "Structured code review"

instructions: |
  You are an expert code reviewer. Analyze the provided code for:
  1. Bugs and logic errors
  2. Security vulnerabilities
  3. Style and readability issues

  Format findings with severity: critical | high | medium | low
```

That's it. One file. Version-controlled, schema-validated, portable.

---

## How It Works With Claude Code

### Option A: MCP Server (Recommended)

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "asp": {
      "command": "asp",
      "args": ["mcp", "serve"],
      "description": "AI Skill Protocol — your installed skills as prompts"
    }
  }
}
```

Install skills and they instantly appear in Claude Code as slash commands:

```bash
asp install github:your-org/code-review-skill
# Now available in Claude Code as a prompt
```

### Option B: Adapter Files

```bash
asp install github:your-org/code-review-skill
asp generate claude   # writes .claude/skills/code-review.md
```

Claude Code reads `.claude/skills/` automatically.

---

## How It Works With Gemini CLI

Add to `~/.gemini/settings.json`:

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

Or generate adapter files:

```bash
asp install github:your-org/code-review-skill
asp generate gemini   # appends skill block to GEMINI.md
```

---

## ASP vs Alternatives

| Feature | Plain Prompts | MCP | LangChain | **ASP** |
|---|---|---|---|---|
| Versioning | ❌ | ❌ | ❌ | ✅ `@1.2.0` |
| Schema validation | ❌ | ❌ | ❌ | ✅ JSON Schema |
| Dependency management | ❌ | ❌ | ⚠️ Python only | ✅ |
| Integrity (SHA-256) | ❌ | ❌ | ❌ | ✅ |
| Discoverability | ❌ | ❌ | ⚠️ | ✅ |
| Vendor neutral | ✅ | ✅ | ❌ | ✅ |
| Claude Code support | Manual | ✅ Tools | ❌ | ✅ Prompts |
| Gemini CLI support | Manual | ✅ Tools | ❌ | ✅ Prompts |
| Write once, run anywhere | ❌ | ❌ | ❌ | ✅ |

**MCP** solves tool/resource connectivity. **ASP** solves skill portability. They are complementary — ASP uses MCP as a delivery mechanism.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AI Applications                        │
│   Claude Code    Gemini CLI    GPT    Custom Agent       │
└──────────┬───────────┬────────────────────┘
           │ MCP       │ MCP / adapter files
           ▼           ▼
┌─────────────────────────────────────────────────────────┐
│              ASP Reference CLI (asp)                     │
│  init  validate  pack  install  list  search  generate  │
└──────────────────────────┬──────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    Git Registry    Filesystem      HTTP Registry
   (GitHub URLs)    (local dev)    (future: asp.dev)
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                  Skill Package (.skill)                  │
│   skill.yaml + skill.lock + README + examples           │
└─────────────────────────────────────────────────────────┘
```

### Protocol Layers

| Layer | What | Key Files |
|---|---|---|
| 0 — Specification | The normative protocol definition | `SPEC.md`, `schema/skill-manifest.schema.json` |
| 1 — Package Format | `.skill` tarball with lockfile | `skill.yaml`, `skill.lock` |
| 2 — Registry | Discovery and distribution | Git URLs, HTTP registry |
| 3 — CLI | Reference implementation | `asp` command |
| 4 — Runtime Adapters | MCP server, Claude/Gemini adapters | `asp mcp serve`, `asp generate` |

---

## Repository Structure

```
OpenProtocol/
├── README.md               ← You are here
├── SPEC.md                 ← Protocol specification (normative)
├── CONTRIBUTING.md
├── LICENSE                 ← Apache 2.0
├── schema/
│   └── skill-manifest.schema.json  ← JSON Schema (normative)
├── docs/
│   ├── architecture.md
│   ├── competitive-analysis.md
│   ├── security-model.md
│   └── adr/               ← Architecture Decision Records
├── cli/                   ← Reference CLI (Python)
│   ├── pyproject.toml
│   ├── asp/
│   └── tests/
└── examples/
    ├── code-review/
    ├── sql-generation/
    └── security-analysis/
```

---

## Roadmap

### v0.1 (Alpha — current)
- [x] Protocol specification (SPEC.md)
- [x] JSON Schema for skill.yaml
- [x] Reference CLI: `init`, `validate`, `pack`, `install`, `list`
- [x] MCP server integration (`asp mcp serve`)
- [x] Claude Code adapter (`asp generate claude`)
- [x] Gemini CLI adapter (`asp generate gemini`)
- [x] Git-native registry (GitHub URL install)
- [x] SHA-256 integrity verification
- [x] Example skills

### v0.2 (Beta)
- [ ] Public skill registry (asp.dev)
- [ ] `asp search` against public registry
- [ ] `asp publish` to public registry
- [ ] Cryptographic signing extension
- [ ] Skill evaluation runner

### v1.0 (Stable)
- [ ] Protocol stability guarantee
- [ ] Multi-language SDK (TypeScript, Go)
- [ ] Enterprise private registry
- [ ] Skill marketplace

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions welcome.

## License

Apache 2.0 — see [LICENSE](LICENSE).
