# ADR 0001 — Initial Architecture

**Status:** Accepted  
**Date:** 2025-01-15  
**Deciders:** ASP Core Team  

---

## Context

Every AI application that supports "skills", "agents", "personas", or "assistants" invents its own format for defining reusable AI behavior:

- Claude Code reads `CLAUDE.md` files
- Gemini CLI reads `GEMINI.md` files
- LangChain has its own chain/prompt abstractions
- OpenAI Assistants have their own managed format
- Custom AI platforms invent their own YAML/JSON schemas

This means that a "code review" skill written for one platform cannot be reused on another without rewriting it from scratch. There is no:

- Standard packaging format
- Versioning mechanism
- Dependency management
- Integrity verification
- Discovery mechanism
- Cross-platform portability

The problem is analogous to the pre-npm era of JavaScript: every project manually copied dependencies, with no versioning, no dependency management, and no discoverability.

---

## Decision

Build an open, vendor-neutral protocol called the **AI Skill Protocol (ASP)** with the following properties:

1. **Spec-first**: The protocol specification (SPEC.md) and JSON Schema are the normative source of truth. Implementations must conform to the spec, not the other way around.

2. **Git-native**: Skills should live in Git repositories. GitHub support is natural but not required. This gives us free hosting, versioning, pull requests for skill contributions, and the existing developer mental model.

3. **Vendor-neutral**: The protocol must not reference OpenAI, Anthropic, Google, or any other vendor. Model compatibility is expressed via capability names (e.g., `instruction_following`, `reasoning`) not model names.

4. **Small core**: The core protocol covers: manifest format, package format, dependency declaration, integrity verification, and registry abstraction. Everything else (signing, telemetry, marketplace) is an extension.

5. **Python reference implementation**: The reference CLI is written in Python because:
   - Python is the primary language of the AI/ML ecosystem
   - Excellent YAML, JSON Schema, and semver tooling exists
   - AI engineers will be the primary users and contributors
   - Easy to install via `pip install asp-cli`

6. **MCP as delivery mechanism**: Rather than inventing a new runtime protocol, ASP exposes installed skills via the existing MCP (Model Context Protocol) `prompts/` API. This gives immediate compatibility with Claude Code, Gemini CLI, and any other MCP client.

---

## Consequences

### Positive

- Skills become portable across AI runtimes
- Developers get a familiar package manager experience (init, validate, pack, install)
- Spec-first design means independent implementations can interoperate
- Git-native means no infrastructure needed to publish a skill
- MCP integration means immediate usefulness in existing tools

### Negative

- Another standard for the community to learn
- Python CLI may not be the final implementation language for all consumers
- MCP dependency means the MCP server integration must be maintained alongside the MCP protocol

### Neutral

- The Python reference implementation is a reference, not a requirement
- Other language implementations (TypeScript, Go, Rust) are expected and encouraged
- The protocol name "ASP" is provisional
