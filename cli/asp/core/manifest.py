"""
Skill manifest parsing and validation.

This module provides the canonical in-memory representation of a skill manifest
and handles loading from disk with full JSON Schema validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from asp.errors import ManifestError, ValidationError

# ---------------------------------------------------------------------------
# Data classes — canonical in-memory representation of skill.yaml
# ---------------------------------------------------------------------------


@dataclass
class SkillAuthor:
    """An author or contributor."""

    name: str
    url: Optional[str] = None
    email: Optional[str] = None


@dataclass
class SkillInput:
    """A typed input parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] = field(default_factory=list)
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class SkillOutput:
    """A typed output value."""

    name: str
    type: str
    description: str
    enum: list[Any] = field(default_factory=list)


@dataclass
class SkillDependency:
    """A dependency on another ASP skill."""

    id: str
    version: str  # semver range
    optional: bool = False


@dataclass
class SkillCapabilities:
    """Model capability requirements."""

    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


@dataclass
class SkillPermissions:
    """Runtime permission requirements."""

    network: bool = False
    filesystem: bool = False
    code_execution: bool = False
    tool_use: bool = False

    def has_non_default(self) -> bool:
        """Return True if any permission is enabled."""
        return self.network or self.filesystem or self.code_execution or self.tool_use

    def to_list(self) -> list[str]:
        """Return list of enabled permission names."""
        perms = []
        if self.network:
            perms.append("network")
        if self.filesystem:
            perms.append("filesystem")
        if self.code_execution:
            perms.append("code_execution")
        if self.tool_use:
            perms.append("tool_use")
        return perms


@dataclass
class SkillRuntime:
    """Execution parameters."""

    timeout_seconds: int = 120
    max_tokens: int = 4096


@dataclass
class SkillExample:
    """A sample input/output pair."""

    description: str
    input: dict[str, Any] = field(default_factory=dict)
    expected_output_contains: list[str] = field(default_factory=list)


@dataclass
class EvaluationCase:
    """A quality assurance test case."""

    input: dict[str, Any] = field(default_factory=dict)
    assert_contains: list[str] = field(default_factory=list)
    assert_not_contains: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class SkillMetadata:
    """Registry and discoverability metadata."""

    tags: list[str] = field(default_factory=list)
    category: str = ""
    created_at: str = ""
    asp_compatible: str = ""


@dataclass
class SkillManifest:
    """
    The canonical in-memory representation of a skill.yaml manifest.

    Required fields are set at construction. Optional fields default to
    empty/falsy values matching the JSON Schema defaults.
    """

    # Required
    asp: str
    id: str
    name: str
    version: str
    description: str
    instructions: str

    # Optional
    authors: list[SkillAuthor] = field(default_factory=list)
    license: str = ""
    homepage: str = ""
    repository: str = ""
    inputs: list[SkillInput] = field(default_factory=list)
    outputs: list[SkillOutput] = field(default_factory=list)
    dependencies: list[SkillDependency] = field(default_factory=list)
    capabilities: SkillCapabilities = field(default_factory=SkillCapabilities)
    permissions: SkillPermissions = field(default_factory=SkillPermissions)
    runtime: SkillRuntime = field(default_factory=SkillRuntime)
    examples: list[SkillExample] = field(default_factory=list)
    evaluation: list[EvaluationCase] = field(default_factory=list)
    metadata: SkillMetadata = field(default_factory=SkillMetadata)
    extensions: dict[str, Any] = field(default_factory=dict)

    # Internal: raw parsed YAML for round-trip fidelity
    _raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def render_input(self, values: dict[str, Any]) -> str:
        """
        Validate input values against the schema and render them into a
        prompt string suitable for injection into an LLM context.

        Raises ValueError for missing required inputs.
        """
        resolved: dict[str, Any] = {}

        for inp in self.inputs:
            if inp.name in values:
                resolved[inp.name] = values[inp.name]
            elif inp.default is not None:
                resolved[inp.name] = inp.default
            elif inp.required:
                raise ValueError(
                    f"Required input '{inp.name}' is missing. "
                    f"Description: {inp.description}"
                )

        # Render: instructions + input block
        parts = [self.instructions.strip(), "", "---", ""]
        for name, val in resolved.items():
            parts.append(f"{name}: {val}")

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Return the raw YAML data for serialization."""
        return self._raw

    @property
    def qualified_name(self) -> str:
        """Return 'name@version' qualified identifier."""
        return f"{self.name}@{self.version}"


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------


def _find_schema() -> dict[str, Any]:
    """
    Locate and load the JSON Schema for skill manifests.

    Search order:
    1. Relative to this file: ../../schema/skill-manifest.schema.json (dev layout)
    2. Relative to cwd: schema/skill-manifest.schema.json
    """
    candidates = [
        Path(__file__).parent.parent.parent.parent / "schema" / "skill-manifest.schema.json",
        Path.cwd() / "schema" / "skill-manifest.schema.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            with candidate.open(encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]

    # Fallback: minimal inline schema for environments where the file isn't present
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["asp", "id", "name", "version", "description", "instructions"],
        "properties": {
            "asp": {"type": "string", "const": "1.0"},
            "id": {"type": "string"},
            "name": {"type": "string"},
            "version": {"type": "string"},
            "description": {"type": "string"},
            "instructions": {"type": "string"},
        },
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_manifest_dict(data: dict[str, Any]) -> list[str]:
    """
    Validate a manifest dict against the JSON Schema.

    Returns a list of error messages. Empty list means valid.
    """
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
    except ImportError:
        return ["jsonschema not installed; cannot validate. Run: pip install jsonschema"]

    schema = _find_schema()
    validator = Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda e: e.path):
        path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"[{path}] {error.message}")
    return errors


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_authors(raw: list[dict[str, Any]]) -> list[SkillAuthor]:
    return [
        SkillAuthor(
            name=a["name"],
            url=a.get("url"),
            email=a.get("email"),
        )
        for a in (raw or [])
    ]


def _parse_inputs(raw: list[dict[str, Any]]) -> list[SkillInput]:
    result = []
    for item in raw or []:
        result.append(
            SkillInput(
                name=item["name"],
                type=item["type"],
                description=item["description"],
                required=item.get("required", True),
                default=item.get("default"),
                enum=item.get("enum", []),
                min_length=item.get("minLength"),
                max_length=item.get("maxLength"),
            )
        )
    return result


def _parse_outputs(raw: list[dict[str, Any]]) -> list[SkillOutput]:
    result = []
    for item in raw or []:
        result.append(
            SkillOutput(
                name=item["name"],
                type=item["type"],
                description=item["description"],
                enum=item.get("enum", []),
            )
        )
    return result


def _parse_dependencies(raw: list[dict[str, Any]]) -> list[SkillDependency]:
    return [
        SkillDependency(
            id=dep["id"],
            version=dep["version"],
            optional=dep.get("optional", False),
        )
        for dep in (raw or [])
    ]


def _parse_capabilities(raw: Optional[dict[str, Any]]) -> SkillCapabilities:
    if not raw:
        return SkillCapabilities()
    return SkillCapabilities(
        required=raw.get("required", []),
        optional=raw.get("optional", []),
    )


def _parse_permissions(raw: Optional[dict[str, Any]]) -> SkillPermissions:
    if not raw:
        return SkillPermissions()
    return SkillPermissions(
        network=raw.get("network", False),
        filesystem=raw.get("filesystem", False),
        code_execution=raw.get("code_execution", False),
        tool_use=raw.get("tool_use", False),
    )


def _parse_runtime(raw: Optional[dict[str, Any]]) -> SkillRuntime:
    if not raw:
        return SkillRuntime()
    return SkillRuntime(
        timeout_seconds=raw.get("timeout_seconds", 120),
        max_tokens=raw.get("max_tokens", 4096),
    )


def _parse_examples(raw: list[dict[str, Any]]) -> list[SkillExample]:
    return [
        SkillExample(
            description=ex.get("description", ""),
            input=ex.get("input", {}),
            expected_output_contains=ex.get("expected_output_contains", []),
        )
        for ex in (raw or [])
    ]


def _parse_evaluation(raw: Optional[dict[str, Any]]) -> list[EvaluationCase]:
    if not raw:
        return []
    return [
        EvaluationCase(
            input=case.get("input", {}),
            assert_contains=case.get("assert_contains", []),
            assert_not_contains=case.get("assert_not_contains", []),
            description=case.get("description", ""),
        )
        for case in raw.get("cases", [])
    ]


def _parse_metadata(raw: Optional[dict[str, Any]]) -> SkillMetadata:
    if not raw:
        return SkillMetadata()
    return SkillMetadata(
        tags=raw.get("tags", []),
        category=raw.get("category", ""),
        created_at=raw.get("created_at", ""),
        asp_compatible=raw.get("asp_compatible", ""),
    )


def _parse_extensions(data: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k.startswith("x-")}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_manifest(data: dict[str, Any]) -> SkillManifest:
    """
    Parse a raw YAML dict into a SkillManifest dataclass.

    Does NOT perform schema validation — call validate_manifest_dict() first.
    Raises ManifestError on missing required keys.
    """
    required_keys = ["asp", "id", "name", "version", "description", "instructions"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ManifestError(
            f"Missing required fields: {', '.join(missing)}",
            hint="Run 'asp validate' to see all issues.",
        )

    return SkillManifest(
        asp=str(data["asp"]),
        id=str(data["id"]),
        name=str(data["name"]),
        version=str(data["version"]),
        description=str(data["description"]),
        instructions=str(data["instructions"]),
        authors=_parse_authors(data.get("authors", [])),
        license=str(data.get("license", "")),
        homepage=str(data.get("homepage", "")),
        repository=str(data.get("repository", "")),
        inputs=_parse_inputs(data.get("inputs", [])),
        outputs=_parse_outputs(data.get("outputs", [])),
        dependencies=_parse_dependencies(data.get("dependencies", [])),
        capabilities=_parse_capabilities(data.get("capabilities")),
        permissions=_parse_permissions(data.get("permissions")),
        runtime=_parse_runtime(data.get("runtime")),
        examples=_parse_examples(data.get("examples", [])),
        evaluation=_parse_evaluation(data.get("evaluation")),
        metadata=_parse_metadata(data.get("metadata")),
        extensions=_parse_extensions(data),
        _raw=data,
    )


def load_manifest(path: Path) -> SkillManifest:
    """
    Load, validate, and parse a skill.yaml manifest from disk.

    Raises:
        ManifestError: if the file doesn't exist or is invalid YAML.
        ValidationError: if the manifest fails JSON Schema validation.
    """
    if not path.exists():
        raise ManifestError(
            f"skill.yaml not found at {path}",
            hint="Run 'asp init' to create a new skill.",
        )

    try:
        with path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ManifestError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ManifestError(
            f"{path} does not contain a YAML mapping at the top level.",
            hint="skill.yaml must be a YAML object (key: value pairs).",
        )

    errors = validate_manifest_dict(raw)
    if errors:
        raise ValidationError(
            f"skill.yaml at {path} has {len(errors)} validation error(s):",
            errors=errors,
            hint="Fix the errors above, then run 'asp validate' to confirm.",
        )

    return parse_manifest(raw)


def find_manifest(start_dir: Optional[Path] = None) -> Path:
    """
    Search upward from start_dir (default: cwd) for skill.yaml.

    Raises ManifestError if not found.
    """
    current = (start_dir or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / "skill.yaml"
        if candidate.exists():
            return candidate
    raise ManifestError(
        "skill.yaml not found in current directory or any parent directory.",
        hint="Run 'asp init' to create a new skill, or cd into a skill directory.",
    )
