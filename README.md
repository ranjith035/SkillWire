<div align="center">

```
  ███████╗██╗  ██╗██╗██╗     ██╗     ██╗    ██╗██╗██████╗ ███████╗
  ██╔════╝██║ ██╔╝██║██║     ██║     ██║    ██║██║██╔══██╗██╔════╝
  ███████╗█████═╝ ██║██║     ██║     ██║ █╗ ██║██║██████╔╝█████╗  
  ╚════██║██╔═██╗ ██║██║     ██║     ██║███╗██║██║██╔══██╗██╔══╝  
  ███████║██║  ██╗██║███████╗███████╗╚███╔███╔╝██║██║  ██║███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚══════╝
```

### The Open, Vendor-Neutral Protocol for Enterprise AI Skills
**Standardized Packaging, Cryptographic Provenance, and Cross-Platform Delivery for Enterprise AI Workflows**

[![Specification](https://img.shields.io/badge/Specification-ASP%20v1.0-6366f1.svg?style=for-the-badge)](SPEC.md)
[![Schema](https://img.shields.io/badge/JSON%20Schema-Draft%202020--12-10b981.svg?style=for-the-badge)](schema/skill-manifest.schema.json)
[![Compliance](https://img.shields.io/badge/Governance-Zero--Trust%20Sandboxing-blue.svg?style=for-the-badge)](docs/security-model.md)
[![Tests](https://img.shields.io/badge/Verification-96%20Passed-brightgreen.svg?style=for-the-badge)](cli/tests/)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg?style=for-the-badge)](LICENSE)

[**Protocol Specification**](SPEC.md) • [**Architecture Whitepaper**](docs/architecture.md) • [**Enterprise Security Model**](docs/security-model.md) • [**Competitive Analysis**](docs/competitive-analysis.md)

</div>

---

## 🏛️ Executive Summary & Strategic Value

As enterprises scale generative AI and agentic engineering, organizations face a critical structural challenge: **prompt and skill fragmentation**.

Internal AI logic today exists in scattered markdown documents, bespoke Python scripts, proprietary SaaS dashboards, or localized IDE files. This unmanaged proliferation creates severe operational and governance risks:

* **Model Vendor Lock-in**: Prompt logic tightly coupled to a single vendor API restricts the ability to leverage competitive multi-model routing (Anthropic Claude, Google Gemini, OpenAI, or on-premise open weights).
* **Supply Chain Vulnerability & Prompt Sprawl**: Lack of versioning, dependency tracking, or integrity validation exposes corporate environments to indirect prompt injection and uncontrolled prompt drift.
* **Absence of Governance & Auditability**: Inability to verify which version of a skill was executed in production or enforce strict capability boundaries (network, filesystem, code execution).
* **Developer Inefficiency**: Engineering teams repeatedly re-invent the same review, analysis, and data transformation logic across different tools.

**SkillWire (AI Skill Protocol / ASP 1.0)** is an open standard that brings **package management rigor, deterministic provenance, and schema-enforced contracts** to AI behaviors—enabling enterprises to package, version, govern, and distribute skills seamlessly across **Claude Code, Gemini CLI, enterprise agents, and internal platforms**.

---

## 🏢 Enterprise Architecture Overview

SkillWire decouples **skill authoring and governance** from **underlying model execution**. The architecture operates across five distinct layers:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       ENTERPRISE CONSUMPTION LAYER                           │
│   Developer IDEs (Claude Code, Cursor)  │  Terminal CLI (Gemini CLI)         │
│   Enterprise RAG Platforms              │  CI/CD Automated Review Pipelines  │
└──────────────────────────────────────▲───────────────────────────────────────┘
                                       │ stdio / JSON-RPC 2.0 (MCP Prompts)
┌──────────────────────────────────────┴───────────────────────────────────────┐
│                    SKILLWIRE AGENT ENGINE & CLI (asp)                        │
│   • Input/Output Contract Validation    • Deterministic Dependency Engine    │
│   • Capability Sandboxing Enforcer      • Lockfile Provenance Verification   │
└──────────────────────────────────────▲───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴───────────────────────────────────────┐
│                      ENTERPRISE REGISTRY LAYER                               │
│   Internal Git Repositories (GitHub Enterprise, GitLab, Bitbucket)           │
│   Air-Gapped / Artifact Storage (S3, Artifactory, OCI Registries)            │
└──────────────────────────────────────▲───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴───────────────────────────────────────┐
│                  DETERMINISTIC PACKAGE FORMAT (.skill)                       │
│   Immutable tar.gz artifact: skill.yaml + skill.lock (SHA-256 integrity)     │
└──────────────────────────────────────▲───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴───────────────────────────────────────┐
│                    NORMATIVE PROTOCOL SPECIFICATION                          │
│   SPEC.md + schema/skill-manifest.schema.json (JSON Schema Draft 2020-12)    │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Enterprise Security & Zero-Trust Governance

SkillWire was designed from the ground up to address enterprise risk postures, SOC2 requirements, and ISO 27001 supply-chain controls:

### 1. Cryptographic Provenance & Tamper Evidence
Every `.skill` package compiled via `asp pack` generates a machine-verified `skill.lock` recording SHA-256 checksums of all manifest files and pinned dependencies. Any in-transit tampering or unauthorized instruction modification immediately halts deployment with an `IntegrityError`.

### 2. Explicit Capability & Permission Gating
Skills must declaratively state their required host access. By default, all capabilities are strictly sandboxed:
```yaml
permissions:
  network: false          # Restricts outbound HTTP/socket egress
  filesystem: false       # Denies local file access
  code_execution: false   # Disallows shell or sandbox execution
  tool_use: false         # Restricts downstream MCP tool invocation
```
Enterprise runtime hosts inspect these flags prior to execution. If a skill does not explicitly declare `code_execution: true`, host environments reject execution requests.

### 3. Namespace Ownership via Reverse-Domain Notation
Skill identifiers enforce reverse-domain notation:
```
com.organization.security.code-review
org.enterprise.compliance.pii-detector
```
This binds namespace ownership to corporate-controlled domain namespaces, preventing typosquatting and internal dependency confusion attacks.

### 4. Safe Archive Extraction
The unpacker rejects any package containing relative path traversal (`../`) or absolute paths, mitigating archive extraction exploits (Zip Slip vulnerabilities).

---

## 🔄 Dual Integration: Claude Code & Gemini CLI

SkillWire provides out-of-the-box support for corporate AI tools via the **Model Context Protocol (MCP)** and native configuration generators.

```
                         ┌─────────────────────────────┐
                         │ Enterprise Skill Repository │
                         │ (com.corp.security-review)  │
                         └──────────────┬──────────────┘
                                        │ asp install
                                        ▼
                         ┌─────────────────────────────┐
                         │   ASP Engine (Local/Host)   │
                         └──────┬───────────────┬──────┘
                                │               │
          MCP Server (stdio)    │               │  Native Adapter Generator
          asp mcp serve         │               │  asp generate claude / gemini
                                ▼               ▼
                     ┌──────────────────┐    ┌──────────────────┐
                     │   Claude Code    │    │    Gemini CLI    │
                     │  (/code-review)  │    │   (GEMINI.md)    │
                     └──────────────────┘    └──────────────────┘
```

### Method 1: Centralized MCP Integration (Recommended)
Add the ASP MCP server to your enterprise workstation configuration:

* **For Claude Code** (`~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "asp": {
      "command": "asp",
      "args": ["mcp", "serve"],
      "description": "Enterprise AI Skill Protocol Engine"
    }
  }
}
```

* **For Gemini CLI** (`~/.gemini/settings.json`):
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

Once installed, corporate skills appear immediately as first-class, typed prompt commands across developer environments.

### Method 2: Headless & Air-Gapped Markdown Adapters
For secure pipelines or build runners operating without background daemons:
```bash
# Generate .claude/skills/review.md for local Claude workspaces
asp generate claude

# Generate managed skill blocks in GEMINI.md for terminal environments
asp generate gemini
```

---

## 📑 The Canonical Skill Manifest (`skill.yaml`)

```yaml
asp: "1.0"                                      # Protocol specification version

id: "com.enterprise.compliance.code-review"      # Reverse-domain unique identity
name: "code-review"                             # Canonical handle
version: "1.2.0"                                # Strict SemVer 2.0.0
description: "Audits source code against corporate security and OWASP Top 10 guidelines."

authors:
  - name: "Enterprise Architecture & Security CoE"
    url: "https://internal.git.corp/ai-standards"
license: "Apache-2.0"

inputs:
  - name: code
    type: string
    description: "Source code diff or snippet under review"
    required: true
  - name: language
    type: string
    description: "Programming language (e.g., python, go, typescript)"
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
  You are an enterprise application security auditor.
  Analyze the provided code for logic vulnerabilities, hardcoded credentials, and memory safety.
  Format your output as:
  ## Executive Summary
  ## Audit Findings (Severity, Code Reference, Risk, Mitigation)
  ## Compliance Recommendation

capabilities:
  required:
    - text_generation
    - instruction_following
  optional:
    - reasoning

models:
  preferred:
    - capability: instruction_following
      context_window: ">=32k"

dependencies:
  - id: "com.enterprise.compliance.credential-scanner"
    version: ">=1.0.0,<2.0.0"

permissions:
  network: false
  filesystem: false
  code_execution: false

metadata:
  tags: [security, appsec, compliance]
  category: engineering
  asp_compatible: ">=1.0.0"
```

---

## 💻 Programmatic SDK Integration

Incorporate approved enterprise skills directly into internal Python microservices, agent frameworks, or middleware:

```python
from asp.core.manifest import load_manifest
from asp.core.registry import InstalledSkillsDB

# 1. Access the enterprise-governed skills cache
db = InstalledSkillsDB()
skill_path = db.get_installed_manifest_path("com.enterprise.compliance.code-review")
skill = load_manifest(skill_path)

# 2. Render verified input contracts
rendered_context = skill.render_input({
    "code": "auth_header = request.headers.get('Authorization')",
    "language": "python"
})

# 3. Route to your approved model provider (Anthropic, Gemini, Azure OpenAI, or Ollama)
# Zero vendor lock-in — prompt logic remains an independent corporate asset
print(rendered_context)
```

---

## 📊 Enterprise Value Matrix: Why Standards Matter

| Capability | Unmanaged Prompts | Model Context Protocol (MCP) | Proprietary Frameworks | **SkillWire (ASP 1.0)** |
|---|:---:|:---:|:---:|:---:|
| **Standard Scope** | Raw Text Snippets | I/O & Tool Connectivity | Application Frameworks | **Portable Skill Packaging & Governance** |
| **Multi-Model Portability** | ❌ Manual rewrite | ⚠️ Host-dependent | ❌ Framework runtime lock | ✅ **Vendor Neutral by Design** |
| **Cryptographic Integrity** | ❌ None | ❌ None | ❌ None | ✅ **SHA-256 `skill.lock`** |
| **Dependency Resolution** | ❌ None | ❌ None | ⚠️ Python packages only | ✅ **Strict SemVer Resolution** |
| **Schema Validation** | ❌ None | ⚠️ Tool parameters only | ⚠️ Python Pydantic only | ✅ **JSON Schema Draft 2020-12** |
| **Permission Sandboxing** | ❌ Full exposure | ⚠️ Tool-level grants | ❌ Unmanaged | ✅ **Declarative Capability Gating** |
| **Enterprise Tool Interop** | ❌ Bespoke | Host standard | Custom adapters | ✅ **Claude Code & Gemini CLI Ready** |

---

## ⚙️ Enterprise CLI Reference

The reference CLI (`asp`) provides standard DevOps commands:

```bash
# Initialize a new standardized skill
asp init [DIRECTORY]

# Validate schema conformance and contract integrity
asp validate [PATH] [--strict]

# Compile into an immutable, distributable .skill archive
asp pack [DIRECTORY] --output [DIST_DIR]

# Install from internal Git, private URL, or local path
asp install [SOURCE] [--yes] [--dry-run]

# Inspect installed enterprise inventory
asp list [--json]

# Serve skills to Claude Code & Gemini CLI via stdio MCP
asp mcp serve
```

---

## 📈 Enterprise Adoption Roadmap

1. **Phase 1: Standardization (Immediate)**
   * Form an internal AI Standards Taskforce.
   * Adopt `schema/skill-manifest.schema.json` as the internal contract for reusable prompts and agents.
2. **Phase 2: Tooling Integration**
   * Configure `asp mcp serve` within enterprise developer workstations running Claude Code and Gemini CLI.
   * Eliminate manual copy-pasting of prompt instructions.
3. **Phase 3: CI/CD Quality Assurance**
   * Integrate `asp validate` into pull-request validation pipelines.
   * Enforce regression testing using manifest `evaluation` suites prior to skill release.
4. **Phase 4: Air-Gapped Governance**
   * Host internal private skill repositories on corporate Git infrastructure.
   * Implement automated checksum verification in production agent execution loops.

---

## 🤝 Governance & Community

SkillWire is an open standard published under the **Apache License, Version 2.0**.
Organizations are encouraged to participate in protocol evolution:

* **Specification**: [`SPEC.md`](SPEC.md)
* **Architecture RFCs**: [`docs/adr/`](docs/adr/)
* **Contribution Guidelines**: [`CONTRIBUTING.md`](CONTRIBUTING.md)

Copyright (c) 2025–2026 SkillWire Protocol Contributors.
