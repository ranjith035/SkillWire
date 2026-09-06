<div align="center">

```
  ███████╗██╗  ██╗██╗██╗     ██╗     ██╗    ██╗██╗██████╗ ███████╗
  ██╔════╝██║ ██╔╝██║██║     ██║     ██║    ██║██║██╔══██╗██╔════╝
  ███████╗█████═╝ ██║██║     ██║     ██║ █╗ ██║██║██████╔╝█████╗  
  ╚════██║██╔═██╗ ██║██║     ██║     ██║███╗██║██║██╔══██╗██╔══╝  
  ███████║██║  ██╗██║███████╗███████╗╚███╔███╔╝██║██║  ██║███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚══════╝
```

### The Open, Vendor-Neutral Protocol for Reusable AI Skills
**"npm for AI Skills" — Package, Version, Validate, Compose, and Execute Across Any AI Runtime**

[![Specification](https://img.shields.io/badge/spec-ASP%20v1.0-6366f1.svg?style=for-the-badge)](SPEC.md)
[![Schema](https://img.shields.io/badge/schema-Draft%202020--12-10b981.svg?style=for-the-badge)](schema/skill-manifest.schema.json)
[![Tests](https://img.shields.io/badge/tests-96%20passed-brightgreen.svg?style=for-the-badge)](cli/tests/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg?style=for-the-badge)](https://python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-red.svg?style=for-the-badge)](LICENSE)

[**Read the Spec**](SPEC.md) • [**Quickstart**](#-quickstart) • [**Claude Code & Gemini Setup**](#-using-with-claude-code--gemini-cli) • [**Architecture**](docs/architecture.md) • [**Security Model**](docs/security-model.md)

</div>

---

## ⚡ Executive Summary

Today, AI prompt logic is deeply fragmented. A code-review prompt crafted for **Claude Code** cannot run in **Gemini CLI**. An agent persona developed for **LangChain** cannot be shared with a **VS Code Copilot** workspace without manual rewriting. There is no standard for:

* **Semantic Versioning** (`skill-name@1.4.2`)
* **Input / Output Schema Validation** (JSON Schema typed contracts)
* **Deterministic Dependencies** (Skill A composes with Skill B via `skill.lock`)
* **Integrity & Auditing** (SHA-256 package checksums)
* **Decentralized Discovery** (Git-native distribution without proprietary lock-in)

**SkillWire (AI Skill Protocol / ASP 1.0)** solves this by introducing a standardized packaging, validation, and delivery layer for reusable AI behaviors.

---

## 🧩 The Core Problem: The $N \times M$ Fragmentation

```
WITHOUT SKILLWIRE:
  Claude Code ──────> Custom CLAUDE.md prompts (unversioned, untyped)
  Gemini CLI  ──────> Custom GEMINI.md prompts (duplicated logic)
  LangChain   ──────> Framework-specific PromptTemplates (locked into Python)
  Custom App  ──────> Hardcoded prompt strings in application code
  [Result: N runtimes × M skills = N × M duplicate implementations]

WITH SKILLWIRE:
                          ┌──────────────────────────┐
                          │   SkillWire (.skill)     │
                          │   • skill.yaml manifest  │
                          │   • skill.lock SHA-256   │
                          │   • JSON Schema Draft    │
                          └─────────────┬────────────┘
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
     Claude Code (MCP)           Gemini CLI (MCP)             Custom LLM App
(prompts/get: rendered)     (prompts/get: rendered)       (Python/TS SDK load)
```

---

## 🚀 Quickstart

### 1. Install the Reference CLI
```bash
pip install asp-cli
# Or install in development mode from source:
git clone https://github.com/ranjith035/SkillWire.git
cd SkillWire/cli && pip install -e .
```

### 2. Scaffold a New Skill
```bash
mkdir my-skill && cd my-skill
asp init
```

### 3. Validate Against Normative JSON Schema
```bash
asp validate
```
```
Validating skill.yaml...
✓ Manifest is valid

┌─────────────────────────────── Skill Summary ───────────────────────────────┐
│   Name                code-review                                           │
│   Version             1.0.0                                                 │
│   ID                  io.github.example.code-review                         │
│   Description         Reviews source code for bugs and vulnerabilities.     │
│   Inputs              code (required), language (optional)                  │
│   Outputs             review, severity                                      │
│   Permissions         none (sandboxed)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Pack for Deterministic Distribution
```bash
asp pack . -o ./dist
```
Produces an immutable `code-review-1.0.0.skill` gzip archive containing `skill.yaml` and `skill.lock` with SHA-256 integrity pinning.

### 5. Install Directly from Git
```bash
asp install github:ranjith035/SkillWire@1.0.0
```

---

## 🤖 Using with Claude Code & Gemini CLI

SkillWire ships with a built-in **Model Context Protocol (MCP)** server (`asp mcp serve`). Installed skills are automatically exposed as native, parameterized **MCP Prompts**.

### Method 1: Live MCP Server (Recommended)

Add to your tool's configuration file:

#### For **Claude Code** (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "asp": {
      "command": "asp",
      "args": ["mcp", "serve"],
      "description": "SkillWire — Installed AI skills as prompts"
    }
  }
}
```

#### For **Gemini CLI** (`~/.gemini/settings.json`):
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

#### Experience in Action
1. Install any skill: `asp install github:org/security-analysis`
2. Start Claude Code or Gemini CLI.
3. Your AI assistant immediately auto-discovers `/security-analysis` with typed parameters!

---

### Method 2: Offline Markdown Adapters

For headless pipelines or environments without MCP daemon support:

```bash
# Generate .claude/skills/code-review.md for Claude Code
asp generate claude

# Generate GEMINI.md managed skill blocks for Gemini CLI
asp generate gemini
```

---

## 📄 Anatomy of a Skill Manifest (`skill.yaml`)

```yaml
asp: "1.0"                                      # Protocol specification version

id: "io.github.example.code-review"              # Reverse-domain unique identity
name: "code-review"                             # Canonical handle
version: "1.0.0"                                # Strict SemVer 2.0.0
description: "Automated code reviewer for security and performance flaws."

authors:
  - name: "SkillWire Contributors"
    url: "https://github.com/ranjith035/SkillWire"
license: "MIT"

inputs:
  - name: code
    type: string
    description: "Source code snippet or file content to analyze"
    required: true
  - name: language
    type: string
    description: "Programming language (e.g., python, go, rust)"
    required: false
    default: "auto"

outputs:
  - name: review
    type: string
    description: "Structured markdown review"
  - name: severity
    type: string
    enum: [none, low, medium, high, critical]

instructions: |
  You are an expert principal software engineer and security auditor.
  Analyze the provided code for logic bugs, memory leaks, and vulnerabilities (OWASP Top 10).
  Format your response as:
  ## Summary
  ## Findings (Severity, Location, Issue, Mitigation)
  ## Overall Severity

capabilities:
  required: [text_generation, instruction_following]
  optional: [reasoning]

permissions:
  network: false                                 # Sandbox guarantees
  filesystem: false
  code_execution: false

metadata:
  tags: [security, code-review, static-analysis]
  category: engineering
  asp_compatible: ">=1.0.0"
```

---

## 🐍 Programmatic Python API

Integrate SkillWire directly into your own applications:

```python
from pathlib import Path
from asp.core.manifest import load_manifest
from asp.core.registry import InstalledSkillsDB

# 1. Access installed skills repository
db = InstalledSkillsDB()
skill_path = db.get_installed_manifest_path("io.github.example.code-review")
skill = load_manifest(skill_path)

# 2. Render instructions with validated inputs
rendered_prompt = skill.render_input({
    "code": "def query_user(user_id): return db.execute(f'SELECT * FROM users WHERE id={user_id}')",
    "language": "python"
})

# 3. Pass to ANY LLM provider (Zero vendor lock-in)
# Works identically with Anthropic, Google Gemini, OpenAI, or local Ollama
print(rendered_prompt)
```

---

## 📊 Feature Comparison

| Capability | Plain Prompts | MCP (Anthropic) | LangChain / LlamaIndex | **SkillWire (ASP)** |
|:---|:---:|:---:|:---:|:---:|
| **Standard Scope** | Raw Text | Tools & Data I/O | Agent Graph Orchestration | **Portable Skill Packaging** |
| **Semantic Versioning** | ❌ None | ❌ None | ❌ None | ✅ **Strict SemVer 2.0.0** |
| **JSON Schema Validation** | ❌ None | ⚠️ Tools only | ⚠️ Pydantic only | ✅ **Draft 2020-12 Contract** |
| **Integrity & Checksums** | ❌ None | ❌ None | ❌ None | ✅ **SHA-256 `skill.lock`** |
| **Dependency Chains** | ❌ None | ❌ None | ⚠️ Python package deps | ✅ **Skill-to-Skill SemVer** |
| **Runtime Portability** | ❌ Fragmented | ⚠️ Host dependent | ❌ Python framework lock | ✅ **Runs anywhere** |
| **MCP Integration** | ❌ | Host standard | Custom tool bridges | ✅ **Native MCP Prompt Server** |
| **Sandboxed Permissions** | ❌ | ⚠️ Tool permissions | ❌ Framework level | ✅ **Explicit capability gates** |

---

## 🔒 Security & Threat Model

Skills contain instructions executed by LLMs with access to developer workflows. SkillWire implements defensive safeguards:

* **T-01: Package Tampering**: Enforced via cryptographic SHA-256 digests in `skill.lock`. Any byte alteration triggers `IntegrityError`.
* **T-03: Privilege Escalation**: Skills must explicitly declare permission requirements (`network`, `filesystem`, `code_execution`). Default is `false` (sandboxed). The CLI prompts for approval before installing elevated skills.
* **T-05: Path Traversal**: Package unpackers strictly reject relative (`../`) and absolute paths in `.skill` archives.

Read the complete [Security Model & Threat Analysis](docs/security-model.md).

---

## 🛠️ CLI Reference

| Command | Syntax | Description |
|---|---|---|
| `init` | `asp init [DIR]` | Scaffolds a new skill directory interactively |
| `validate` | `asp validate [PATH] [--strict]` | Validates `skill.yaml` against JSON Schema |
| `pack` | `asp pack [DIR] [-o OUT]` | Builds `.skill` tarball and generates `skill.lock` |
| `install` | `asp install <SOURCE>` | Installs from `github:owner/repo` or local directory |
| `list` | `asp list [--json]` | Lists all installed skills, versions, and origins |
| `search` | `asp search <QUERY>` | Queries GitHub topic registry for skills |
| `generate` | `asp generate <claude\|gemini>` | Creates native Markdown adapters for AI runtimes |
| `mcp serve`| `asp mcp serve` | Launches stdio JSON-RPC 2.0 MCP Prompt server |
| `mcp info` | `asp mcp info` | Prints MCP config JSON for Claude and Gemini |

---

## 📂 Repository Layout

```
SkillWire/
├── SPEC.md                             # Normative protocol specification
├── schema/skill-manifest.schema.json   # Normative JSON Schema
├── docs/
│   ├── architecture.md                 # Layered architecture design
│   ├── competitive-analysis.md         # Industry positioning & gap analysis
│   ├── security-model.md               # Threat model & cryptographic verification
│   └── adr/                            # Architecture Decision Records (0001-0004)
├── cli/
│   ├── asp/                            # Core engine & CLI commands
│   └── tests/                          # 96 automated tests (100% pass)
└── examples/
    ├── code-review/                    # Reference code audit skill
    ├── sql-generation/                 # Reference SQL query generator
    └── security-analysis/              # Reference STRIDE threat modeling skill
```

---

## 🗺️ Roadmap

- [x] **v0.1.0 (Alpha)**: Normative Specification, JSON Schema Draft 2020-12, Python Reference CLI (`asp`), MCP Prompt Server, Git-native distribution.
- [ ] **v0.2.0 (Beta)**: Public Skill Registry (`registry.skillwire.org`), `asp publish` command, Cryptographic signing (`x-signature`).
- [ ] **v0.3.0**: Automated Evaluation Runner (`asp eval`) executing evaluation assertions against configured model targets.
- [ ] **v1.0.0**: Multi-language SDKs (TypeScript / Node.js, Go, Rust), enterprise private registry support.

---

## 🤝 Contributing

We welcome contributions from AI engineers, protocol architects, and security researchers!
Review [CONTRIBUTING.md](CONTRIBUTING.md) for details on proposing specification changes, code formatting (`black`, `ruff`, `mypy`), and our ADR process.

---

## 📜 License

Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for details.

Copyright (c) 2025–2026 SkillWire Protocol Contributors.
