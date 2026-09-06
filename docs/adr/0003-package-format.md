# ADR 0003 — Package Format: .skill Tarball + skill.lock

**Status:** Accepted  
**Date:** 2025-01-15  

---

## Context

Skills need to be packaged for distribution. The package format must support:

- Atomic distribution (install = download one thing)
- Integrity verification (tamper detection)
- Deterministic builds (same inputs → same outputs)
- Cross-platform compatibility (Windows, macOS, Linux)
- Human-auditability (developers should be able to inspect packages)

---

## Decision

A `.skill` file is a **gzip-compressed tar archive** (`.tar.gz`) with the `.skill` extension.

### Why tar.gz?

| Format | Cross-platform | Streaming | Standard | Widely understood |
|---|---|---|---|---|
| `.tar.gz` | ✅ | ✅ | ✅ | ✅ |
| `.zip` | ✅ | ❌ | ✅ | ✅ |
| `.skill` (custom binary) | ✅ | ✅ | ❌ | ❌ |
| Directory | ✅ | N/A | N/A | ✅ |

Tar is the standard for Python wheels (`.whl`), npm packages (tarballs), and Linux packages. It supports streaming extraction and is available as a standard library in every language.

### Package Contents

```
code-review-1.0.0.skill  (tar.gz)
├── skill.yaml            ← Required: the manifest
├── skill.lock            ← Required: integrity manifest
├── README.md             ← Optional: documentation
└── examples/             ← Optional: example files
```

### skill.lock

The lockfile records:

1. The SHA-256 of `skill.yaml` at pack time
2. The resolved versions of all dependencies with their SHA-256 hashes
3. The source URLs for all dependencies

This enables:
- **Tamper detection**: if skill.yaml changes after packing, the hash won't match
- **Reproducible installs**: the lockfile pins exact versions
- **Audit trail**: the source of every dependency is recorded

```json
{
  "asp": "1.0",
  "skill_id": "io.github.example.code-review",
  "skill_version": "1.0.0",
  "manifest_sha256": "abc123...",
  "generated_at": "2025-01-15T10:00:00Z",
  "dependencies": []
}
```

### Filename Convention

`{name}-{version}.skill` — e.g., `code-review-1.0.0.skill`

This mirrors Python wheel naming and makes version clear from the filename alone.

---

## Consequences

- Any `tar` utility can inspect a `.skill` package
- The `skill.lock` must be committed to version control for reproducibility
- Installation without a `skill.lock` is possible but warns the user
- The `.skill` extension distinguishes from plain tarballs

## Rejected Alternatives

**Zip**: No streaming extraction. ZIP64 format has edge cases.  
**Directory**: Not atomic. Cannot be integrity-verified as a unit.  
**Custom binary format**: Unnecessary complexity. No tooling ecosystem.
