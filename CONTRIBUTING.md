## Contributing to the AI Skill Protocol

Thank you for your interest in contributing! ASP is an open protocol — contributions to the specification, reference CLI, examples, and documentation are all welcome.

---

## Ways to Contribute

1. **Publish a skill** — create a GitHub repository with a `skill.yaml`, tag it `asp-skill`, and it's discoverable via `asp search`
2. **Improve the spec** — open an issue or PR for `SPEC.md` or `schema/skill-manifest.schema.json`
3. **Improve the CLI** — bug fixes, new features, better error messages
4. **Add examples** — create new example skills in `examples/`
5. **Write documentation** — improve architecture docs, add tutorials
6. **Report bugs** — file issues with reproduction steps

---

## Getting Started

```bash
git clone https://github.com/ranjith035/SkillWire.git
cd SkillWire/cli

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
ruff check asp/
black --check asp/

# Run type checking
mypy asp/
```

---

## Proposing Spec Changes

Specification changes require more scrutiny than implementation changes because they affect all conforming implementations.

**Process:**

1. Open a GitHub issue with the `spec:` prefix in the title
2. Describe the problem you're solving and why the current spec doesn't address it
3. Propose the change with concrete examples
4. If the issue gains consensus, create a PR with changes to `SPEC.md` and `schema/skill-manifest.schema.json`
5. For major changes, create an ADR in `docs/adr/` documenting the decision

**Changes that require an ADR:**
- New top-level manifest fields
- Changes to the package format
- Changes to the registry protocol
- Changes to the MCP integration design
- Breaking changes to any existing field

---

## Architecture Decision Records (ADRs)

We use ADRs to document significant architectural decisions. ADRs live in `docs/adr/`.

**ADR format:**
```markdown
# ADR NNNN — Title

**Status:** Proposed | Accepted | Deprecated | Superseded  
**Date:** YYYY-MM-DD  

## Context
Why does this decision need to be made?

## Decision
What did we decide?

## Consequences
What are the positive, negative, and neutral consequences?
```

---

## Code Style

We follow these conventions for the Python reference implementation:

- **Formatter**: [black](https://github.com/psf/black), line length 100
- **Linter**: [ruff](https://github.com/astral-sh/ruff)
- **Type checker**: [mypy](https://mypy.readthedocs.io/) in strict mode
- **Docstrings**: Google-style docstrings
- **Type hints**: Required on all public functions and methods

Run all checks:
```bash
black asp/ tests/
ruff check asp/ tests/
mypy asp/
pytest tests/ -v --cov=asp
```

---

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(cli): add asp update command
fix(manifest): handle YAML anchors correctly
docs(spec): clarify dependency version range syntax
test(integrity): add tampered package detection test
spec: add evaluation.cases required field
```

Types: `feat`, `fix`, `docs`, `test`, `spec`, `refactor`, `chore`

---

## Test Requirements

All PRs must:
- Pass all existing tests: `pytest tests/ -v`
- Add tests for new functionality
- Not reduce test coverage below the current threshold

For new protocol features, prefer **interoperability tests** that verify the behavior as specified, not implementation details.

---

## Publishing a Skill

To publish a skill and make it discoverable via `asp search`:

1. Create a public GitHub repository
2. Add `skill.yaml` at the repository root
3. Run `asp validate` to verify it's correct
4. Add the `asp-skill` topic to your repository (Settings → Topics)
5. Create a GitHub release tagged with the version (e.g., `v1.0.0`)
6. Test installation: `asp install github:your-username/your-repo-name`

---

## License

By contributing, you agree that your contributions are licensed under the Apache 2.0 license. No CLA is required.
