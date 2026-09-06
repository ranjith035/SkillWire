# AI Skill Protocol (ASP) Specification

**Version:** 1.0-draft  
**Status:** Experimental  
**Date:** 2025-01-15  

---

## Abstract

The AI Skill Protocol (ASP) defines an open, vendor-neutral standard for packaging, versioning, distributing, validating, and consuming reusable AI skills. A skill is a portable unit of AI behavior consisting of instructions, typed inputs/outputs, dependency declarations, and execution metadata. ASP enables skills to move between AI assistants, coding agents, LLM applications, and agent frameworks without modification.

---

## Status of This Document

This document is an experimental specification. It may change without notice. Implementations built against this specification should track the version field (`asp: "1.0"`) for compatibility.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://tools.ietf.org/html/rfc2119).

---

## 1. Core Concepts

### 1.1 What is a Skill?

A **skill** is a reusable, versioned, self-describing unit of AI behavior. A skill consists of:

- **Instructions** — the system/user prompt that defines the AI's behavior
- **Input schema** — typed, named parameters the skill accepts
- **Output schema** — typed, named values the skill produces
- **Dependencies** — other skills this skill depends on
- **Metadata** — name, version, author, license, tags
- **Capabilities** — what the AI model must be able to do to run this skill
- **Permissions** — what the skill needs access to (network, filesystem, etc.)
- **Examples** — sample inputs and expected outputs
- **Evaluation** — test cases for quality assurance

Skills are intentionally model-agnostic. The same skill MUST be consumable by any AI runtime that satisfies the declared capability requirements.

### 1.2 Skill Identity

Every skill has a globally unique identity composed of:

```
{id}@{version}
```

Examples:
- `io.github.ranjith.code-review@1.2.0`
- `io.github.example.sql-generation@2.0.0-beta.1`

**Skill ID format:** Reverse-domain notation, lowercase, hyphen-separated segments. Pattern: `^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9-]*)+$`

**Version format:** Semantic Versioning 2.0.0 (semver.org). MUST be valid semver.

### 1.3 Skill Lifecycle

```
DISCOVER → GET → VALIDATE → RESOLVE → LOAD → EXECUTE
```

| Phase | Description | Protocol Primitive |
|---|---|---|
| DISCOVER | Find skills in a registry | `search` |
| GET | Download a skill package | `install` |
| VALIDATE | Check manifest against schema | `validate` |
| RESOLVE | Resolve dependency versions deterministically | internal |
| LOAD | Parse manifest, inject instructions into runtime | internal |
| EXECUTE | Run with a specific model and runtime | runtime-specific |

---

## 2. Manifest Format (skill.yaml)

The skill manifest is a YAML file named `skill.yaml`. It is the single source of truth for a skill. The manifest MUST validate against the JSON Schema at `schema/skill-manifest.schema.json`.

### 2.1 Required Fields

Every manifest MUST contain these fields:

| Field | Type | Description |
|---|---|---|
| `asp` | string | Protocol version. MUST be `"1.0"`. |
| `id` | string | Globally unique skill identifier in reverse-domain notation. |
| `name` | string | Short name for the skill. Lowercase, hyphen-separated. |
| `version` | string | Semantic version (semver 2.0.0). |
| `description` | string | Human-readable description. 10–500 characters. |
| `instructions` | string | The LLM instructions. This is the skill's core behavior. |

### 2.2 Optional Fields

| Field | Type | Description |
|---|---|---|
| `authors` | array | List of author objects with `name`, `url`, `email`. |
| `license` | string | SPDX license identifier (e.g., `MIT`, `Apache-2.0`). |
| `homepage` | string | URL to skill homepage or documentation. |
| `repository` | string | URL to source repository. |
| `inputs` | array | Typed input parameter definitions. |
| `outputs` | array | Typed output value definitions. |
| `capabilities` | object | Required and optional model capabilities. |
| `models` | object | Model preferences and constraints. |
| `dependencies` | array | Other skills this skill depends on. |
| `tools` | array | External tools this skill may invoke. |
| `runtime` | object | Execution parameters (timeout, max_tokens). |
| `examples` | array | Sample inputs with expected outputs. |
| `evaluation` | object | Test cases for quality verification. |
| `permissions` | object | Runtime permission requirements. |
| `metadata` | object | Tags, category, dates, compatibility. |

### 2.3 Input and Output Schema

Each input/output item:

```yaml
inputs:
  - name: code          # Required. Lowercase, underscore-separated.
    type: string        # Required. One of: string, number, integer, boolean, object, array
    description: "..."  # Required. Human-readable description.
    required: true      # Optional. Default: true.
    default: null       # Optional. Used when value not provided.
    enum: []            # Optional. Constrains to specific values.
```

### 2.4 Capabilities

Skills declare capability requirements independently of vendor names:

```yaml
capabilities:
  required:
    - text_generation
    - instruction_following
  optional:
    - reasoning
    - code_generation
```

Valid capability names:
- `text_generation` — basic LLM text output
- `code_generation` — producing syntactically correct code
- `code_execution` — running code in a sandbox
- `image_understanding` — vision/multimodal input
- `tool_use` — calling external tools/functions
- `instruction_following` — following complex multi-step instructions
- `reasoning` — chain-of-thought, multi-step reasoning
- `retrieval` — RAG / document retrieval

### 2.5 Dependencies

```yaml
dependencies:
  - id: "io.github.example.language-detector"
    version: ">=1.0.0,<2.0.0"
    optional: false
```

Version ranges follow npm-style semver:
- `>=1.0.0,<2.0.0` — AND of constraints
- `^1.2.3` — compatible with 1.x.x where x >= 2.3
- `~1.2.3` — patch-level: 1.2.x where x >= 3
- `*` — any version
- `1.2.3` — exact version

### 2.6 Permissions

Skills MUST declare all runtime permissions they require:

```yaml
permissions:
  network: false         # HTTP/network access
  filesystem: false      # Read/write local files
  code_execution: false  # Execute code
  tool_use: false        # Call external tools/MCP servers
```

A client MUST display requested permissions to users before execution. A client SHOULD reject skills that request undeclared capabilities.

### 2.7 Extension Fields

Any field prefixed with `x-` is an extension field and MUST be preserved by conforming implementations. Example:

```yaml
x-my-platform-config:
  custom_setting: value
```

### 2.8 Complete Manifest Example

```yaml
asp: "1.0"

id: "io.github.example.code-review"
name: "code-review"
version: "1.2.0"
description: "Reviews source code for bugs, security vulnerabilities, and style issues."

authors:
  - name: "Jane Doe"
    url: "https://github.com/janedoe"

license: "MIT"
homepage: "https://github.com/janedoe/code-review-skill"
repository: "https://github.com/janedoe/code-review-skill"

inputs:
  - name: code
    type: string
    description: "Source code to review"
    required: true
  - name: language
    type: string
    description: "Programming language. Use 'auto' to detect."
    required: false
    default: "auto"

outputs:
  - name: review
    type: string
    description: "Structured review with findings"
  - name: severity
    type: string
    description: "Overall severity"
    enum: [none, low, medium, high, critical]

instructions: |
  You are an expert code reviewer...

capabilities:
  required: [text_generation, instruction_following]
  optional: [reasoning]

dependencies:
  - id: "io.github.example.language-detector"
    version: ">=1.0.0,<2.0.0"
    optional: true

runtime:
  timeout_seconds: 120
  max_tokens: 4096

permissions:
  network: false
  filesystem: false
  code_execution: false

metadata:
  tags: [code-quality, security, review]
  category: engineering
  created_at: "2025-01-15"
  asp_compatible: ">=1.0.0"
```

---

## 3. Package Format (.skill)

### 3.1 Overview

A `.skill` file is a **gzip-compressed tar archive** containing a skill and its metadata. The format mirrors Python `.whl` files and npm tarballs — well-understood, cross-platform, and human-auditable.

### 3.2 Filename Convention

```
{name}-{version}.skill
```

Example: `code-review-1.2.0.skill`

### 3.3 Required Contents

Every `.skill` archive MUST contain:

| File | Description |
|---|---|
| `skill.yaml` | The skill manifest |
| `skill.lock` | Integrity manifest (JSON) |

### 3.4 Optional Contents

| File | Description |
|---|---|
| `README.md` | Human-readable documentation |
| `examples/` | Example input/output files |
| `tests/` | Evaluation test data |

### 3.5 skill.lock Format

`skill.lock` is a JSON file that records the exact state of the skill at pack time:

```json
{
  "asp": "1.0",
  "skill_id": "io.github.example.code-review",
  "skill_version": "1.2.0",
  "manifest_sha256": "abc123...",
  "generated_at": "2025-01-15T10:00:00Z",
  "dependencies": [
    {
      "id": "io.github.example.language-detector",
      "resolved_version": "1.3.0",
      "sha256": "def456...",
      "source": "github:example/language-detector-skill@1.3.0"
    }
  ]
}
```

A client MUST verify `manifest_sha256` against the actual `skill.yaml` content before trusting the package.

---

## 4. Dependency Resolution

### 4.1 Algorithm

Dependency resolution MUST be deterministic. Given the same `skill.lock`, the same dependency versions MUST be resolved every time.

1. Parse all `dependencies` from the manifest.
2. For each dependency, query the registry for available versions.
3. Select the highest version satisfying the declared range.
4. Recursively resolve transitive dependencies.
5. Detect and reject circular dependencies.
6. Write resolved versions to `skill.lock`.

### 4.2 Lockfile Pinning

When `skill.lock` exists, clients MUST use the pinned versions rather than re-resolving. This ensures reproducibility. To update dependencies, use `asp update`.

### 4.3 Circular Dependencies

If skill A depends on skill B, and skill B depends on skill A, resolution MUST fail with a clear error identifying the cycle.

---

## 5. Registry Protocol

### 5.1 Registry Types

| Type | Description | Example |
|---|---|---|
| Git-native | GitHub/GitLab repositories | `github:user/repo@1.0.0` |
| Filesystem | Local directory of skills | `/path/to/skills/` |
| HTTP | REST API registry | `https://registry.asp-protocol.org` |

### 5.2 Git-native Source Syntax

```
github:{owner}/{repo}
github:{owner}/{repo}@{version}
github:{owner}/{repo}#{branch-or-tag}
git+https://{host}/{owner}/{repo}
```

The repository MUST contain `skill.yaml` at its root.

### 5.3 HTTP Registry API

A conforming HTTP registry MUST implement:

```
GET /v1/skills
    Query params: q (search), tags, category, page, per_page
    Returns: { skills: [SkillRecord], total: int, page: int }

GET /v1/skills/{id}
    Returns: SkillRecord with all versions

GET /v1/skills/{id}/{version}
    Returns: SkillRecord for specific version

GET /v1/skills/{id}/{version}/download
    Returns: .skill file (application/octet-stream)
```

### 5.4 SkillRecord Schema

```json
{
  "id": "io.github.example.code-review",
  "name": "code-review",
  "version": "1.2.0",
  "description": "...",
  "source_url": "https://github.com/example/code-review-skill",
  "sha256": "abc123...",
  "tags": ["code-quality", "security"],
  "author": "Jane Doe",
  "published_at": "2025-01-15T10:00:00Z"
}
```

---

## 6. Permissions Model

### 6.1 Permission Categories

| Permission | Description | Default |
|---|---|---|
| `network` | HTTP/network requests | `false` |
| `filesystem` | Read or write local files | `false` |
| `code_execution` | Execute code in a sandbox | `false` |
| `tool_use` | Call external MCP tools or APIs | `false` |

### 6.2 Client Requirements

A conforming client:

1. MUST display all non-default permissions to the user before executing a skill.
2. SHOULD prompt for explicit user confirmation when `code_execution: true`.
3. MUST NOT grant permissions that the user has not approved.
4. SHOULD log permission grants for audit purposes.

### 6.3 Skill Publisher Requirements

A skill MUST NOT request permissions it does not need. Requesting unnecessary permissions is grounds for removal from a public registry.

---

## 7. Security Model

### 7.1 Integrity Verification

Every package MUST have a `skill.lock` with SHA-256 of `skill.yaml`. Clients MUST verify integrity before loading any skill content. An integrity mismatch MUST cause installation to fail.

### 7.2 Prompt Injection

Skill instructions are user-controlled text that becomes part of LLM prompts. Clients MUST treat skill instructions as untrusted content from third parties. Clients SHOULD:

- Display the instructions to users before first use
- Not automatically grant tool access based on instructions alone
- Apply the same prompt injection mitigations as for user input

### 7.3 Trust Levels

| Level | Meaning |
|---|---|
| `verified` | Published by a registry-verified organization |
| `community` | Published by a GitHub-authenticated user |
| `unverified` | Source unknown or unverified |

Clients SHOULD display the trust level to users.

### 7.4 Supply Chain

Clients MUST verify SHA-256 checksums of all installed skills and their dependencies. The lockfile MUST be committed to version control for reproducibility.

---

## 8. MCP Integration

### 8.1 Overview

ASP provides a built-in MCP server (`asp mcp serve`) that exposes installed skills as MCP **prompts**. This allows Claude Code, Gemini CLI, and any MCP-compatible client to access ASP skills natively.

Skills map to MCP prompts because both are parameterized text templates with typed arguments.

### 8.2 prompts/list Response

```json
{
  "prompts": [
    {
      "name": "code-review",
      "description": "Reviews source code for bugs and security issues",
      "arguments": [
        {
          "name": "code",
          "description": "Source code to review",
          "required": true
        },
        {
          "name": "language",
          "description": "Programming language",
          "required": false
        }
      ]
    }
  ]
}
```

### 8.3 prompts/get Response

```json
{
  "description": "Reviews source code for bugs and security issues",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "{skill instructions rendered with provided argument values}"
      }
    }
  ]
}
```

### 8.4 Argument Rendering

When a skill is invoked via MCP with argument values, the ASP MCP server MUST:

1. Validate argument values against input schemas
2. Apply defaults for missing optional arguments
3. Render the instructions with argument values appended
4. Return the rendered prompt as an MCP message

---

## 9. Model Compatibility

### 9.1 Capability-Based Requirements

Skills MUST declare model requirements using capability names, not vendor names:

```yaml
capabilities:
  required:
    - instruction_following
    - reasoning
models:
  preferred:
    - capability: reasoning
      context_window: ">=32k"
```

### 9.2 Context Window

Context window requirements are expressed as semver-style ranges on token count:
- `>=16k` — at least 16,000 tokens
- `>=100k` — at least 100,000 tokens

### 9.3 Vendor Names

Skills MAY list specific unsupported models:

```yaml
models:
  unsupported:
    - "gpt-3.5-turbo"  # Insufficient instruction following
```

However, vendor-specific configuration MUST be in extension fields (`x-`).

---

## 10. Extension Points

### 10.1 Extension Fields

Any field prefixed with `x-` is an extension and MUST be preserved by conforming clients. Example:

```yaml
x-claude-config:
  cache_control: ephemeral

x-enterprise-policy:
  approval_required: true
  approver: "security-team"
```

### 10.2 Registered Extensions

| Extension | Description | Status |
|---|---|---|
| `x-signing` | Cryptographic signature for the package | Proposed |
| `x-telemetry` | Usage telemetry configuration | Proposed |
| `x-auth` | Authentication requirements for skill execution | Proposed |
| `x-policy` | Enterprise governance policy | Proposed |

---

## 11. Protocol Versioning

The `asp` field in every manifest specifies the protocol version the manifest was written for.

```yaml
asp: "1.0"
```

### Compatibility Rules

- Clients MUST reject manifests with a higher major version than they support.
- Clients SHOULD warn on manifests with a higher minor version.
- Clients MUST ignore unknown optional fields (forward compatibility).
- The protocol version `1.x` guarantees that all `1.0` features remain valid.

---

## 12. Conformance

A **conforming client** MUST:

1. Accept and validate skill manifests against the JSON Schema.
2. Verify SHA-256 integrity of installed packages.
3. Respect the `permissions` model and display permissions to users.
4. Implement deterministic dependency resolution using `skill.lock`.
5. Support Git-native source format (`github:owner/repo@version`).
6. Reject manifests that fail JSON Schema validation.
7. Reject packages whose `skill.yaml` SHA-256 does not match `skill.lock`.

A **conforming skill publisher** MUST:

1. Provide a valid `skill.yaml` at the repository root.
2. Use valid semver for the `version` field.
3. Use reverse-domain notation for the `id` field.
4. Declare all required permissions accurately.
5. Not include malicious instructions or prompt injection attempts.

---

*End of Specification*
