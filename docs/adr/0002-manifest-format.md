# ADR 0002 — Manifest Format: YAML + JSON Schema

**Status:** Accepted  
**Date:** 2025-01-15  

---

## Context

The skill manifest is the core artifact of the protocol. Every skill must have one. The format must be:

1. Human-readable and human-writable (developers will author these directly)
2. Machine-validatable (tools need to check correctness)
3. Able to contain multi-line text (the `instructions` field is a full prompt, potentially hundreds of lines)
4. Widely supported across languages and platforms

We evaluated four options: YAML, TOML, JSON, and a custom DSL.

---

## Decision

Use **YAML** for human authoring, validated against a **JSON Schema (Draft 2020-12)**.

### Why YAML?

| Requirement | YAML | TOML | JSON | Custom DSL |
|---|---|---|---|---|
| Multi-line strings (instructions) | ✅ Native `\|` block scalar | ⚠️ Multi-line requires workarounds | ❌ Escape sequences everywhere | Depends |
| Human readability | ✅ | ✅ | ⚠️ Verbose | Depends |
| Comments | ✅ | ✅ | ❌ | Depends |
| Ecosystem support | ✅ Universal | ✅ Growing | ✅ Universal | ❌ Custom parser |
| Familiar to AI/DevOps engineers | ✅ Docker Compose, GitHub Actions | ✅ Cargo.toml | ⚠️ API config | ❌ |

YAML's `|` block scalar is critical for the `instructions` field:

```yaml
instructions: |
  You are an expert code reviewer. Analyze the code
  for bugs, security issues, and style problems.
  
  Format your response as:
  ## Findings
  ...
```

This is much better than JSON's `"instructions": "You are an expert...\n\nFormat your response as:\n## Findings\n..."`.

### Why JSON Schema for validation?

- JSON Schema is a well-established open standard
- Draft 2020-12 is the current stable version
- Supported by validators in every major language
- Allows the schema itself to be published as the normative spec artifact
- Tools like VS Code can provide real-time YAML validation using JSON Schema

### JSON Schema as the spec artifact

The `schema/skill-manifest.schema.json` file is the normative source of truth for what constitutes a valid skill manifest. The prose in SPEC.md explains the semantics, but the schema enforces the structure. This is analogous to how OpenAPI specs work.

---

## Consequences

- Developers can use `$schema` annotations in skill.yaml for IDE validation
- The JSON Schema can be registered at `https://asp-protocol.org/schema/` for auto-discovery
- YAML parsers must be careful about YAML 1.1 vs 1.2 differences (use `yaml.safe_load` not `yaml.load`)
- The `asp: "1.0"` field is quoted because YAML would parse `1.0` as a float otherwise
