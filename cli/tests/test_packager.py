"""Tests for .skill package creation and extraction."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest
import yaml

from asp.core.packager import inspect_package, pack_skill, unpack_skill
from asp.errors import IntegrityError, PackageError


class TestPackSkill:
    """Tests for pack_skill()."""

    def test_pack_creates_skill_file(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        out_dir = tmp_path / "dist"
        result = pack_skill(tmp_skill_dir, out_dir)
        assert result.exists()
        assert result.suffix == ".skill"

    def test_pack_filename_format(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        out_dir = tmp_path / "dist"
        result = pack_skill(tmp_skill_dir, out_dir)
        # Should be: {name}-{version}.skill
        assert result.name == "code-review-1.0.0.skill"

    def test_pack_creates_valid_tar(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        result = pack_skill(tmp_skill_dir, tmp_path)
        assert tarfile.is_tarfile(result)

    def test_pack_contains_required_files(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        result = pack_skill(tmp_skill_dir, tmp_path)
        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
        assert "skill.yaml" in names
        assert "skill.lock" in names

    def test_pack_includes_optional_readme(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        readme = tmp_skill_dir / "README.md"
        readme.write_text("# Test Skill\n", encoding="utf-8")
        result = pack_skill(tmp_skill_dir, tmp_path)
        with tarfile.open(result, "r:gz") as tar:
            names = tar.getnames()
        assert "README.md" in names

    def test_pack_rejects_missing_manifest(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(PackageError, match="skill.yaml not found"):
            pack_skill(empty_dir, tmp_path)

    def test_pack_generates_lockfile(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        pack_skill(tmp_skill_dir, tmp_path)
        assert (tmp_skill_dir / "skill.lock").exists()


class TestUnpackSkill:
    """Tests for unpack_skill()."""

    def test_unpack_extracts_skill_yaml(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        skill_file = pack_skill(tmp_skill_dir, tmp_path / "dist")
        dest = tmp_path / "extracted"
        extracted_dir = unpack_skill(skill_file, dest)
        assert (extracted_dir / "skill.yaml").exists()

    def test_unpack_extracts_lockfile(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        skill_file = pack_skill(tmp_skill_dir, tmp_path / "dist")
        dest = tmp_path / "extracted"
        extracted_dir = unpack_skill(skill_file, dest)
        assert (extracted_dir / "skill.lock").exists()

    def test_pack_unpack_roundtrip(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        """Pack then unpack should yield identical skill.yaml content."""
        original_yaml = (tmp_skill_dir / "skill.yaml").read_text(encoding="utf-8")

        skill_file = pack_skill(tmp_skill_dir, tmp_path / "dist")
        dest = tmp_path / "extracted"
        extracted_dir = unpack_skill(skill_file, dest)

        extracted_yaml = (extracted_dir / "skill.yaml").read_text(encoding="utf-8")
        # Parse both to compare semantically (formatting may differ due to lockfile generation)
        original_data = yaml.safe_load(original_yaml)
        extracted_data = yaml.safe_load(extracted_yaml)
        assert original_data["id"] == extracted_data["id"]
        assert original_data["version"] == extracted_data["version"]

    def test_unpack_rejects_invalid_file(self, tmp_path: Path) -> None:
        fake = tmp_path / "fake.skill"
        fake.write_bytes(b"not a tar file")
        with pytest.raises(PackageError, match="valid .skill package"):
            unpack_skill(fake, tmp_path / "dest")

    def test_unpack_detects_tampering(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        """Modifying skill.yaml after packing should fail integrity check on unpack."""
        skill_file = pack_skill(tmp_skill_dir, tmp_path / "dist")

        # Tamper with the archive: modify skill.yaml inside it
        import io
        tampered = tmp_path / "dist" / "tampered.skill"
        with tarfile.open(skill_file, "r:gz") as original_tar:
            with tarfile.open(tampered, "w:gz") as new_tar:
                for member in original_tar.getmembers():
                    if member.name == "skill.yaml":
                        # Replace content with tampered version
                        content = b"asp: '1.0'\nid: 'tampered'\nname: 'tampered'\nversion: '0.0.0'\ndescription: 'Tampered'\ninstructions: 'Tampered'\n"
                        member.size = len(content)
                        new_tar.addfile(member, io.BytesIO(content))
                    else:
                        f = original_tar.extractfile(member)
                        new_tar.addfile(member, f)

        with pytest.raises(IntegrityError, match="Integrity check failed"):
            unpack_skill(tampered, tmp_path / "dest")


class TestInspectPackage:
    """Tests for inspect_package()."""

    def test_inspect_returns_metadata(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        skill_file = pack_skill(tmp_skill_dir, tmp_path)
        info = inspect_package(skill_file)
        assert info["name"] == "code-review"
        assert info["version"] == "1.0.0"
        assert info["id"] == "io.github.test.code-review"

    def test_inspect_lists_files(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        skill_file = pack_skill(tmp_skill_dir, tmp_path)
        info = inspect_package(skill_file)
        assert "skill.yaml" in info["files"]
        assert "skill.lock" in info["files"]

    def test_inspect_reports_size(self, tmp_skill_dir: Path, tmp_path: Path) -> None:
        skill_file = pack_skill(tmp_skill_dir, tmp_path)
        info = inspect_package(skill_file)
        assert info["size_bytes"] > 0

    def test_inspect_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(PackageError, match="not found"):
            inspect_package(tmp_path / "nonexistent.skill")
