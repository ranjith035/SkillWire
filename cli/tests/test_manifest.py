"""Tests for skill manifest parsing and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from asp.core.manifest import (
    SkillInput,
    SkillManifest,
    find_manifest,
    load_manifest,
    parse_manifest,
    validate_manifest_dict,
)
from asp.errors import ManifestError, ValidationError


class TestValidateManifestDict:
    """Tests for validate_manifest_dict() — JSON Schema validation."""

    def test_valid_manifest_passes(self, valid_manifest_dict: dict) -> None:
        errors = validate_manifest_dict(valid_manifest_dict)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_minimal_manifest_passes(self, minimal_manifest_dict: dict) -> None:
        errors = validate_manifest_dict(minimal_manifest_dict)
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_missing_asp_field(self, valid_manifest_dict: dict) -> None:
        del valid_manifest_dict["asp"]
        errors = validate_manifest_dict(valid_manifest_dict)
        assert any("asp" in e for e in errors)

    def test_missing_id_field(self, valid_manifest_dict: dict) -> None:
        del valid_manifest_dict["id"]
        errors = validate_manifest_dict(valid_manifest_dict)
        assert any("id" in e for e in errors)

    def test_missing_instructions_field(self, valid_manifest_dict: dict) -> None:
        del valid_manifest_dict["instructions"]
        errors = validate_manifest_dict(valid_manifest_dict)
        assert any("instructions" in e for e in errors)

    def test_invalid_asp_version(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["asp"] = "2.0"  # Not "1.0"
        errors = validate_manifest_dict(valid_manifest_dict)
        assert len(errors) > 0

    def test_invalid_semver_version(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["version"] = "not-a-semver"
        errors = validate_manifest_dict(valid_manifest_dict)
        assert len(errors) > 0

    def test_invalid_skill_id_format(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["id"] = "bad_id_format"  # No dots
        errors = validate_manifest_dict(valid_manifest_dict)
        assert len(errors) > 0

    def test_valid_skill_id_formats(self) -> None:
        """Various valid reverse-domain IDs should pass."""
        valid_ids = [
            "io.github.user.my-skill",
            "com.example.skill",
            "org.myorg.tools.code-review",
        ]
        base = {
            "asp": "1.0",
            "id": "",
            "name": "test",
            "version": "1.0.0",
            "description": "A test skill description.",
            "instructions": "You are a helpful assistant.",
        }
        for skill_id in valid_ids:
            base["id"] = skill_id
            base["name"] = "test"
            errors = validate_manifest_dict(base)
            assert errors == [], f"ID '{skill_id}' should be valid, got: {errors}"

    def test_extension_fields_allowed(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["x-custom-config"] = {"key": "value"}
        errors = validate_manifest_dict(valid_manifest_dict)
        assert errors == []

    def test_unknown_non_extension_field_rejected(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["unknown_field"] = "should fail"
        errors = validate_manifest_dict(valid_manifest_dict)
        assert len(errors) > 0

    def test_description_too_short(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["description"] = "Short"  # < 10 chars
        errors = validate_manifest_dict(valid_manifest_dict)
        assert len(errors) > 0


class TestParseManifest:
    """Tests for parse_manifest() — dataclass construction."""

    def test_parses_required_fields(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        assert manifest.asp == "1.0"
        assert manifest.id == "io.github.test.code-review"
        assert manifest.name == "code-review"
        assert manifest.version == "1.0.0"
        assert "code reviewer" in manifest.instructions

    def test_parses_inputs_correctly(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        assert len(manifest.inputs) == 2
        code_input = manifest.inputs[0]
        assert isinstance(code_input, SkillInput)
        assert code_input.name == "code"
        assert code_input.type == "string"
        assert code_input.required is True

    def test_parses_optional_input_with_default(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        lang_input = manifest.inputs[1]
        assert lang_input.name == "language"
        assert lang_input.required is False
        assert lang_input.default == "auto"

    def test_parses_capabilities(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        assert "text_generation" in manifest.capabilities.required
        assert "instruction_following" in manifest.capabilities.required
        assert "reasoning" in manifest.capabilities.optional

    def test_parses_permissions_all_false(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        assert manifest.permissions.network is False
        assert manifest.permissions.filesystem is False
        assert manifest.permissions.code_execution is False

    def test_permissions_has_non_default_false_when_all_false(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        assert manifest.permissions.has_non_default() is False

    def test_permissions_has_non_default_true_when_network(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["permissions"]["network"] = True
        manifest = parse_manifest(valid_manifest_dict)
        assert manifest.permissions.has_non_default() is True

    def test_parses_minimal_manifest(self, minimal_manifest_dict: dict) -> None:
        manifest = parse_manifest(minimal_manifest_dict)
        assert manifest.inputs == []
        assert manifest.outputs == []
        assert manifest.dependencies == []

    def test_raises_on_missing_required_key(self) -> None:
        with pytest.raises(ManifestError, match="Missing required fields"):
            parse_manifest({"asp": "1.0", "name": "test"})

    def test_extensions_captured(self, valid_manifest_dict: dict) -> None:
        valid_manifest_dict["x-my-config"] = {"key": "value"}
        manifest = parse_manifest(valid_manifest_dict)
        assert "x-my-config" in manifest.extensions
        assert manifest.extensions["x-my-config"] == {"key": "value"}

    def test_qualified_name(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        assert manifest.qualified_name == "code-review@1.0.0"


class TestRenderInput:
    """Tests for SkillManifest.render_input()."""

    def test_render_basic_input(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        rendered = manifest.render_input({"code": "def foo(): pass"})
        assert "def foo(): pass" in rendered
        assert manifest.instructions.strip() in rendered

    def test_render_uses_default_for_optional(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        rendered = manifest.render_input({"code": "x = 1"})
        assert "auto" in rendered  # default for language

    def test_render_raises_on_missing_required(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        with pytest.raises(ValueError, match="Required input 'code' is missing"):
            manifest.render_input({})

    def test_render_with_all_inputs(self, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        rendered = manifest.render_input({"code": "print('hello')", "language": "python"})
        assert "python" in rendered
        assert "print" in rendered


class TestLoadManifest:
    """Tests for load_manifest() — loading from disk."""

    def test_load_valid_manifest(self, tmp_skill_dir: Path) -> None:
        manifest = load_manifest(tmp_skill_dir / "skill.yaml")
        assert isinstance(manifest, SkillManifest)
        assert manifest.name == "code-review"

    def test_load_minimal_manifest(self, tmp_minimal_skill_dir: Path) -> None:
        manifest = load_manifest(tmp_minimal_skill_dir / "skill.yaml")
        assert manifest.name == "minimal-skill"

    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestError, match="not found"):
            load_manifest(tmp_path / "skill.yaml")

    def test_raises_on_invalid_yaml(self, tmp_path: Path) -> None:
        bad_yaml = tmp_path / "skill.yaml"
        bad_yaml.write_text("{ broken yaml: [unclosed", encoding="utf-8")
        with pytest.raises(ManifestError, match="Invalid YAML"):
            load_manifest(bad_yaml)

    def test_raises_validation_error_with_all_errors(self, tmp_path: Path, invalid_manifest_dict: dict) -> None:
        path = tmp_path / "skill.yaml"
        with path.open("w") as f:
            yaml.dump(invalid_manifest_dict, f)
        with pytest.raises(ValidationError) as exc_info:
            load_manifest(path)
        assert len(exc_info.value.errors) > 0


class TestFindManifest:
    """Tests for find_manifest() — upward directory search."""

    def test_finds_in_current_dir(self, tmp_skill_dir: Path) -> None:
        found = find_manifest(tmp_skill_dir)
        assert found == tmp_skill_dir / "skill.yaml"

    def test_finds_in_parent_dir(self, tmp_skill_dir: Path) -> None:
        subdir = tmp_skill_dir / "subdir"
        subdir.mkdir()
        found = find_manifest(subdir)
        assert found == tmp_skill_dir / "skill.yaml"

    def test_raises_when_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestError, match="not found"):
            find_manifest(tmp_path)
