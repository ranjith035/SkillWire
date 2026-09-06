"""
.skill package creation and extraction.

A .skill file is a gzip-compressed tar archive containing:
  - skill.yaml      (required)
  - skill.lock      (required — generated if not present)
  - README.md       (optional)
  - examples/       (optional)
  - tests/          (optional)
"""

from __future__ import annotations

import tarfile
import tempfile
from pathlib import Path
from typing import Any

from asp.core.integrity import generate_lockfile, load_lockfile, verify_lockfile, write_lockfile
from asp.core.manifest import load_manifest
from asp.errors import IntegrityError, PackageError

# Files and directories included in a .skill package
_REQUIRED_FILES = ["skill.yaml", "skill.lock"]
_OPTIONAL_FILES = ["README.md"]
_OPTIONAL_DIRS = ["examples", "tests"]


def pack_skill(skill_dir: Path, output_dir: Path) -> Path:
    """
    Pack a skill directory into a .skill tarball.

    Steps:
    1. Load and validate skill.yaml
    2. Generate skill.lock if not present
    3. Create gzip-compressed tar archive named {name}-{version}.skill

    Returns:
        Path to the created .skill file.

    Raises:
        PackageError: if skill.yaml is invalid or packing fails.
    """
    skill_dir = skill_dir.resolve()
    manifest_path = skill_dir / "skill.yaml"

    if not manifest_path.exists():
        raise PackageError(
            f"skill.yaml not found in {skill_dir}",
            hint="Run 'asp init' to create a new skill or cd into a skill directory.",
        )

    # Load and validate
    manifest = load_manifest(manifest_path)

    # Generate skill.lock if not present or stale
    lock_path = skill_dir / "skill.lock"
    lock = generate_lockfile(manifest_path, manifest)
    write_lockfile(lock, skill_dir)

    # Build output path
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{manifest.name}-{manifest.version}.skill"
    output_path = output_dir / filename

    # Build tar archive
    try:
        with tarfile.open(output_path, "w:gz") as tar:
            # Required files
            for fname in _REQUIRED_FILES:
                fpath = skill_dir / fname
                if fpath.exists():
                    tar.add(fpath, arcname=fname)

            # Optional files
            for fname in _OPTIONAL_FILES:
                fpath = skill_dir / fname
                if fpath.exists():
                    tar.add(fpath, arcname=fname)

            # Optional directories
            for dname in _OPTIONAL_DIRS:
                dpath = skill_dir / dname
                if dpath.exists() and dpath.is_dir():
                    tar.add(dpath, arcname=dname)
    except Exception as e:
        # Clean up partial output
        if output_path.exists():
            output_path.unlink()
        raise PackageError(f"Failed to create package: {e}") from e

    return output_path


def unpack_skill(skill_path: Path, dest_dir: Path) -> Path:
    """
    Unpack a .skill tarball to dest_dir, verifying integrity first.

    Steps:
    1. Extract to a temporary directory
    2. Verify skill.lock integrity
    3. Move to final destination

    Returns:
        Path to the extracted skill directory.

    Raises:
        PackageError: if the archive is invalid.
        IntegrityError: if the integrity check fails.
    """
    skill_path = skill_path.resolve()
    if not skill_path.exists():
        raise PackageError(f"Package file not found: {skill_path}")

    if not tarfile.is_tarfile(skill_path):
        raise PackageError(
            f"{skill_path.name} is not a valid .skill package.",
            hint="Ensure the file is a valid .skill archive created by 'asp pack'.",
        )

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Extract to temp dir first for integrity verification
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)

        try:
            with tarfile.open(skill_path, "r:gz") as tar:
                # Security: reject paths that escape the destination
                for member in tar.getmembers():
                    member_path = Path(member.name)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise PackageError(
                            f"Suspicious path in package: {member.name}",
                            hint="This package may be malicious. Do not install it.",
                        )
                tar.extractall(tmp_dir)
        except tarfile.TarError as e:
            raise PackageError(f"Failed to extract package: {e}") from e

        # Verify integrity
        manifest_path = tmp_dir / "skill.yaml"
        lock_path = tmp_dir / "skill.lock"

        if not manifest_path.exists():
            raise PackageError("Package is missing skill.yaml.")
        if not lock_path.exists():
            raise PackageError("Package is missing skill.lock.")

        verify_lockfile(manifest_path, lock_path)

        # Load manifest to get skill name for destination directory
        manifest = load_manifest(manifest_path)
        skill_dest = dest_dir / f"{manifest.name}-{manifest.version}"

        # Move extracted files to final destination
        if skill_dest.exists():
            import shutil
            shutil.rmtree(skill_dest)

        import shutil
        shutil.copytree(tmp_dir, skill_dest)

    return skill_dest


def inspect_package(skill_path: Path) -> dict[str, Any]:
    """
    Inspect a .skill package and return metadata without fully extracting it.

    Returns a dict with keys: name, version, id, description, files, size_bytes.
    """
    skill_path = skill_path.resolve()

    if not skill_path.exists():
        raise PackageError(f"Package not found: {skill_path}")

    if not tarfile.is_tarfile(skill_path):
        raise PackageError(f"{skill_path.name} is not a valid .skill package.")

    size_bytes = skill_path.stat().st_size
    files: list[str] = []
    manifest_content: str = ""

    with tarfile.open(skill_path, "r:gz") as tar:
        files = [m.name for m in tar.getmembers()]
        try:
            manifest_member = tar.getmember("skill.yaml")
            f = tar.extractfile(manifest_member)
            if f:
                manifest_content = f.read().decode("utf-8")
        except KeyError:
            raise PackageError("Package is missing skill.yaml.")

    import yaml
    raw = yaml.safe_load(manifest_content)

    return {
        "name": raw.get("name", "unknown"),
        "version": raw.get("version", "unknown"),
        "id": raw.get("id", "unknown"),
        "description": raw.get("description", ""),
        "files": files,
        "size_bytes": size_bytes,
    }
