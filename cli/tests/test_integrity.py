"""Tests for integrity verification and skill.lock management."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from asp.core.integrity import (
    SkillLock,
    generate_lockfile,
    load_lockfile,
    sha256_file,
    sha256_string,
    verify_lockfile,
    write_lockfile,
)
from asp.core.manifest import parse_manifest
from asp.errors import IntegrityError


class TestSha256:
    """Tests for hashing functions."""

    def test_sha256_file(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")
        digest = sha256_file(test_file)
        # Well-known SHA-256 of "hello world"
        assert digest == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert len(digest) == 64  # SHA-256 hex = 64 chars
        assert all(c in "0123456789abcdef" for c in digest)

    def test_sha256_file_empty(self, tmp_path: Path) -> None:
        empty_file = tmp_path / "empty.txt"
        empty_file.write_bytes(b"")
        digest = sha256_file(empty_file)
        assert len(digest) == 64
        # SHA-256 of empty string is well-known
        assert digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_sha256_string(self) -> None:
        digest = sha256_string("hello world")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_sha256_string_deterministic(self) -> None:
        d1 = sha256_string("test content")
        d2 = sha256_string("test content")
        assert d1 == d2

    def test_sha256_string_different_content(self) -> None:
        d1 = sha256_string("content A")
        d2 = sha256_string("content B")
        assert d1 != d2

    def test_sha256_file_matches_string(self, tmp_path: Path) -> None:
        content = "this is a test"
        test_file = tmp_path / "test.txt"
        test_file.write_text(content, encoding="utf-8")
        assert sha256_file(test_file) == sha256_string(content)


class TestLockfileGeneration:
    """Tests for generate_lockfile() and write_lockfile()."""

    def test_generate_lockfile_structure(self, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        manifest_path = tmp_skill_dir / "skill.yaml"
        lock = generate_lockfile(manifest_path, manifest)

        assert isinstance(lock, SkillLock)
        assert lock.asp == "1.0"
        assert lock.skill_id == manifest.id
        assert lock.skill_version == manifest.version
        assert len(lock.manifest_sha256) == 64
        assert lock.generated_at != ""

    def test_generate_lockfile_sha256_matches_file(self, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        manifest_path = tmp_skill_dir / "skill.yaml"
        lock = generate_lockfile(manifest_path, manifest)

        actual = sha256_file(manifest_path)
        assert lock.manifest_sha256 == actual

    def test_write_lockfile_creates_file(self, tmp_path: Path, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        lock = generate_lockfile(tmp_skill_dir / "skill.yaml", manifest)
        lock_path = write_lockfile(lock, tmp_path)

        assert lock_path.exists()
        assert lock_path.name == "skill.lock"

    def test_write_lockfile_is_valid_json(self, tmp_path: Path, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        import json
        manifest = parse_manifest(valid_manifest_dict)
        lock = generate_lockfile(tmp_skill_dir / "skill.yaml", manifest)
        lock_path = write_lockfile(lock, tmp_path)

        with lock_path.open() as f:
            data = json.load(f)

        assert "asp" in data
        assert "skill_id" in data
        assert "manifest_sha256" in data


class TestLockfileRoundtrip:
    """Tests for write/load roundtrip."""

    def test_write_and_load_roundtrip(self, tmp_path: Path, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        lock = generate_lockfile(tmp_skill_dir / "skill.yaml", manifest)
        write_lockfile(lock, tmp_path)

        loaded = load_lockfile(tmp_path / "skill.lock")
        assert loaded.asp == lock.asp
        assert loaded.skill_id == lock.skill_id
        assert loaded.skill_version == lock.skill_version
        assert loaded.manifest_sha256 == lock.manifest_sha256

    def test_load_missing_lockfile_raises(self, tmp_path: Path) -> None:
        with pytest.raises(IntegrityError, match="not found"):
            load_lockfile(tmp_path / "skill.lock")


class TestVerifyLockfile:
    """Tests for verify_lockfile() — integrity checking."""

    def test_verify_passes_on_untampered_file(self, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        manifest_path = tmp_skill_dir / "skill.yaml"
        lock = generate_lockfile(manifest_path, manifest)
        write_lockfile(lock, tmp_skill_dir)

        # Should not raise
        verify_lockfile(manifest_path, tmp_skill_dir / "skill.lock")

    def test_verify_fails_on_tampered_manifest(self, tmp_skill_dir: Path, valid_manifest_dict: dict) -> None:
        manifest = parse_manifest(valid_manifest_dict)
        manifest_path = tmp_skill_dir / "skill.yaml"
        lock = generate_lockfile(manifest_path, manifest)
        write_lockfile(lock, tmp_skill_dir)

        # Tamper with the manifest after lockfile generation
        with manifest_path.open("a", encoding="utf-8") as f:
            f.write("\n# TAMPERED\n")

        with pytest.raises(IntegrityError, match="Integrity check failed"):
            verify_lockfile(manifest_path, tmp_skill_dir / "skill.lock")
