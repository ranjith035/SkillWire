"""
Integrity verification via SHA-256 checksums and skill.lock management.

The skill.lock file records the exact state of a skill package at pack time,
enabling deterministic, tamper-evident distribution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from asp.errors import IntegrityError


@dataclass
class DependencyLockEntry:
    """Locked dependency record."""

    id: str
    resolved_version: str
    sha256: str
    source: str


@dataclass
class SkillLock:
    """
    Contents of skill.lock — the integrity manifest for a packaged skill.

    Generated at pack time; verified at install time.
    """

    asp: str = "1.0"
    skill_id: str = ""
    skill_version: str = ""
    manifest_sha256: str = ""
    generated_at: str = ""
    dependencies: list[DependencyLockEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "asp": self.asp,
            "skill_id": self.skill_id,
            "skill_version": self.skill_version,
            "manifest_sha256": self.manifest_sha256,
            "generated_at": self.generated_at,
            "dependencies": [asdict(d) for d in self.dependencies],
        }


def sha256_file(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_string(content: str) -> str:
    """Compute the SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_lockfile(manifest_path: Path, manifest: Any) -> SkillLock:
    """
    Generate a SkillLock from a loaded manifest and its file on disk.

    Args:
        manifest_path: Path to the skill.yaml file.
        manifest: A SkillManifest instance.

    Returns:
        A populated SkillLock ready to write.
    """
    manifest_hash = sha256_file(manifest_path)
    now = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

    return SkillLock(
        asp="1.0",
        skill_id=manifest.id,
        skill_version=manifest.version,
        manifest_sha256=manifest_hash,
        generated_at=now,
        dependencies=[],  # Populated by resolver during install
    )


def write_lockfile(lock: SkillLock, dest_dir: Path) -> Path:
    """
    Write a SkillLock as skill.lock JSON to dest_dir.

    Returns the path to the written file.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    lock_path = dest_dir / "skill.lock"
    with lock_path.open("w", encoding="utf-8") as f:
        json.dump(lock.to_dict(), f, indent=2)
        f.write("\n")
    return lock_path


def load_lockfile(lock_path: Path) -> SkillLock:
    """
    Load and parse a skill.lock file.

    Raises:
        IntegrityError: if the file is missing or malformed.
    """
    if not lock_path.exists():
        raise IntegrityError(
            f"skill.lock not found at {lock_path}",
            hint="Run 'asp pack' to regenerate the lockfile.",
        )

    try:
        with lock_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise IntegrityError(f"skill.lock is malformed JSON: {e}") from e

    deps = [
        DependencyLockEntry(
            id=d["id"],
            resolved_version=d["resolved_version"],
            sha256=d["sha256"],
            source=d["source"],
        )
        for d in data.get("dependencies", [])
    ]

    return SkillLock(
        asp=data.get("asp", "1.0"),
        skill_id=data.get("skill_id", ""),
        skill_version=data.get("skill_version", ""),
        manifest_sha256=data.get("manifest_sha256", ""),
        generated_at=data.get("generated_at", ""),
        dependencies=deps,
    )


def verify_lockfile(manifest_path: Path, lock_path: Path) -> None:
    """
    Verify that the manifest file matches the recorded SHA-256 in skill.lock.

    Raises:
        IntegrityError: if the manifest has been tampered with.
    """
    lock = load_lockfile(lock_path)
    actual_hash = sha256_file(manifest_path)

    if actual_hash != lock.manifest_sha256:
        raise IntegrityError(
            f"Integrity check failed for {manifest_path.name}.\n"
            f"  Expected SHA-256: {lock.manifest_sha256}\n"
            f"  Actual SHA-256:   {actual_hash}",
            hint="The manifest has been modified since it was packed. Re-pack with 'asp pack'.",
        )
