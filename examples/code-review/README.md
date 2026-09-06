# Code Review Skill

An ASP 1.0 reference skill for automated code reviews covering quality, security, and performance.

## Manifest Details

- **ID**: `io.github.example.code-review`
- **Version**: `1.0.0`
- **Target Capabilities**: `text_generation`, `instruction_following`, `reasoning`
- **Permissions**: Fully sandboxed (no network, filesystem, or execution access)

## Installation

```bash
asp install github:ai-skill-protocol/examples/code-review
```

## Quick Verification

```bash
asp validate ./skill.yaml
asp pack .
```
