"""
Registry abstractions for skill discovery and distribution.

Registries are the mechanism by which skills are found and downloaded.
Three registry types are supported in the MVP:
- GitRegistry: GitHub/GitLab repositories (git clone or archive download)
- FileSystemRegistry: local directory of skill directories
- InstalledSkillsDB: tracks installed skills in ~/.asp/
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from asp.errors import RegistryError, SkillNotFoundError


@dataclass
class SkillRecord:
    """Metadata about a skill available in a registry."""

    id: str
    name: str
    version: str
    description: str
    source_url: str
    sha256: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    author: str = ""


class Registry(ABC):
    """Abstract base class for skill registries."""

    @abstractmethod
    def search(self, query: str) -> list[SkillRecord]:
        """Search for skills by name/tag/description."""
        ...

    @abstractmethod
    def get(self, skill_id: str, version: Optional[str] = None) -> SkillRecord:
        """Get metadata for a specific skill."""
        ...

    @abstractmethod
    def download(self, record: SkillRecord, dest: Path) -> Path:
        """Download skill source to dest directory. Returns path to skill directory."""
        ...

    @abstractmethod
    def list_versions(self, skill_id: str) -> list[str]:
        """List all available versions of a skill."""
        ...


class GitRegistry(Registry):
    """
    Git-native registry supporting GitHub, GitLab, and any Git remote.

    Source formats:
    - github:owner/repo
    - github:owner/repo@1.2.0
    - github:owner/repo#branch
    - https://github.com/owner/repo
    - git+https://github.com/owner/repo
    """

    def __init__(self, base_url: str = "https://github.com") -> None:
        self.base_url = base_url.rstrip("/")

    def parse_source(self, source: str) -> tuple[str, str, Optional[str]]:
        """
        Parse a source string into (owner, repo, version_or_ref).

        Returns ('owner', 'repo', '1.2.0') or ('owner', 'repo', None).
        """
        source = source.strip()

        # github:owner/repo@version or github:owner/repo#ref
        if source.startswith("github:"):
            rest = source[len("github:"):]
            ref: Optional[str] = None
            if "@" in rest:
                path, ref = rest.rsplit("@", 1)
            elif "#" in rest:
                path, ref = rest.rsplit("#", 1)
            else:
                path = rest
            parts = path.split("/")
            if len(parts) != 2:
                raise RegistryError(
                    f"Invalid GitHub source: '{source}'. Expected 'github:owner/repo'.",
                )
            return parts[0], parts[1], ref

        # https://github.com/owner/repo[@version]
        match = re.match(r"https?://github\.com/([^/]+)/([^/@#]+)(?:[@#](.+))?", source)
        if match:
            return match.group(1), match.group(2).removesuffix(".git"), match.group(3)

        # git+https://...
        match = re.match(r"git\+https?://github\.com/([^/]+)/([^/@#.]+)", source)
        if match:
            return match.group(1), match.group(2), None

        raise RegistryError(
            f"Cannot parse source '{source}'. "
            "Supported formats: github:owner/repo, github:owner/repo@version, "
            "https://github.com/owner/repo",
        )

    def _build_clone_url(self, owner: str, repo: str) -> str:
        return f"{self.base_url}/{owner}/{repo}.git"

    def _git_available(self) -> bool:
        return shutil.which("git") is not None

    def search(self, query: str) -> list[SkillRecord]:
        """Git registry doesn't support full-text search in MVP."""
        return []

    def get(self, skill_id: str, version: Optional[str] = None) -> SkillRecord:
        """Build a SkillRecord from a source string (skill_id here is the github: URL)."""
        owner, repo, ref = self.parse_source(skill_id)
        url = f"https://github.com/{owner}/{repo}"
        return SkillRecord(
            id=skill_id,
            name=repo,
            version=ref or "latest",
            description=f"Skill from {url}",
            source_url=url,
        )

    def download(self, record: SkillRecord, dest: Path) -> Path:
        """
        Download the skill to dest using git clone.

        Falls back to GitHub archive download if git is not available.
        Returns path to the downloaded skill directory.
        """
        owner, repo, ref = self.parse_source(record.source_url or record.id)
        dest.mkdir(parents=True, exist_ok=True)
        skill_dir = dest / repo

        if skill_dir.exists():
            shutil.rmtree(skill_dir)

        if self._git_available():
            self._clone_with_git(owner, repo, ref, skill_dir)
        else:
            self._download_archive(owner, repo, ref, dest, skill_dir)

        return skill_dir

    def _clone_with_git(
        self, owner: str, repo: str, ref: Optional[str], dest: Path
    ) -> None:
        """Clone repository using git."""
        clone_url = self._build_clone_url(owner, repo)
        cmd = ["git", "clone", "--depth=1"]
        if ref:
            cmd += ["--branch", ref]
        cmd += [clone_url, str(dest)]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RegistryError(
                f"git clone failed: {result.stderr.strip()}",
                hint=f"Check that '{owner}/{repo}' exists and is public.",
            )

    def _download_archive(
        self, owner: str, repo: str, ref: Optional[str], dest: Path, skill_dir: Path
    ) -> None:
        """Download repository as a zip archive (fallback when git not available)."""
        try:
            import httpx
        except ImportError:
            raise RegistryError("Neither git nor httpx is available. Install git or httpx.")

        branch = ref or "main"
        url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"

        with tempfile.TemporaryDirectory() as tmp_str:
            tmp = Path(tmp_str)
            zip_path = tmp / f"{repo}.zip"

            try:
                with httpx.Client(follow_redirects=True, timeout=60) as client:
                    r = client.get(url)
                    r.raise_for_status()
                    zip_path.write_bytes(r.content)
            except httpx.HTTPError as e:
                raise RegistryError(f"Failed to download {url}: {e}") from e

            import zipfile
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp)

            # GitHub archives extract to '{repo}-{branch}/'
            extracted = tmp / f"{repo}-{branch}"
            if not extracted.exists():
                # Try to find the extracted directory
                candidates = [p for p in tmp.iterdir() if p.is_dir() and p.name.startswith(repo)]
                if not candidates:
                    raise RegistryError("Could not find extracted archive directory.")
                extracted = candidates[0]

            shutil.copytree(extracted, skill_dir)

    def list_versions(self, skill_id: str) -> list[str]:
        """List semver git tags for a repository."""
        try:
            owner, repo, _ = self.parse_source(skill_id)
        except RegistryError:
            return []

        if not self._git_available():
            return []

        url = self._build_clone_url(owner, repo)
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", "--refs", url],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            return []

        if result.returncode != 0:
            return []

        versions = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                ref = parts[1].replace("refs/tags/", "").strip().lstrip("v")
                try:
                    import semver as sv
                    sv.Version.parse(ref)
                    versions.append(ref)
                except ValueError:
                    pass

        return sorted(versions)


class FileSystemRegistry(Registry):
    """
    Local filesystem registry for development and testing.

    Scans a directory for subdirectories containing skill.yaml files.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _discover(self) -> list[SkillRecord]:
        """Discover all skills in the root directory."""
        records = []
        for candidate in self.root.rglob("skill.yaml"):
            try:
                import yaml
                with candidate.open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict) and "id" in data:
                    records.append(
                        SkillRecord(
                            id=data.get("id", ""),
                            name=data.get("name", ""),
                            version=data.get("version", ""),
                            description=data.get("description", ""),
                            source_url=str(candidate.parent),
                            tags=data.get("metadata", {}).get("tags", []),
                        )
                    )
            except Exception:
                pass
        return records

    def search(self, query: str) -> list[SkillRecord]:
        query_lower = query.lower()
        return [
            r for r in self._discover()
            if query_lower in r.name.lower() or query_lower in r.description.lower()
        ]

    def get(self, skill_id: str, version: Optional[str] = None) -> SkillRecord:
        resolved_path = None
        try:
            if Path(skill_id).exists():
                resolved_path = Path(skill_id).resolve()
        except Exception:
            pass

        for record in self._discover():
            matches_id = record.id == skill_id
            matches_name = record.name == skill_id
            matches_path = False
            if resolved_path:
                rec_path = Path(record.source_url).resolve()
                matches_path = rec_path == resolved_path or (rec_path / "skill.yaml") == resolved_path

            if matches_id or matches_name or matches_path:
                if version is None or record.version == version:
                    return record
        raise SkillNotFoundError(skill_id, version)

    def download(self, record: SkillRecord, dest: Path) -> Path:
        """Copy the skill directory to dest."""
        source = Path(record.source_url)
        if not source.exists():
            raise RegistryError(f"Skill source directory not found: {source}")
        dest_path = dest / source.name
        if dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(source, dest_path)
        return dest_path

    def list_versions(self, skill_id: str) -> list[str]:
        return [r.version for r in self._discover() if r.id == skill_id]


class InstalledSkillsDB:
    """
    Tracks installed skills in ~/.asp/skills/.

    The database is a simple JSON file at ~/.asp/installed.json.
    Skills are stored as directories under ~/.asp/skills/{skill-id}/
    """

    def __init__(self, asp_home: Optional[Path] = None) -> None:
        self.asp_home = (asp_home or Path.home() / ".asp").resolve()
        self.skills_dir = self.asp_home / "skills"
        self.db_path = self.asp_home / "installed.json"

    def _load_db(self) -> list[dict]:
        if not self.db_path.exists():
            return []
        try:
            with self.db_path.open(encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_db(self, records: list[dict]) -> None:
        self.asp_home.mkdir(parents=True, exist_ok=True)
        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
            f.write("\n")

    def list_installed(self) -> list[dict]:
        """Return all installed skill records."""
        return self._load_db()

    def is_installed(self, skill_id: str) -> bool:
        """Return True if the skill is installed."""
        return any(r["id"] == skill_id for r in self._load_db())

    def install(self, manifest: Any, source_url: str, sha256: str) -> None:
        """Record a newly installed skill."""
        records = self._load_db()
        # Remove existing record for this skill
        records = [r for r in records if r["id"] != manifest.id]
        records.append(
            {
                "id": manifest.id,
                "name": manifest.name,
                "version": manifest.version,
                "description": manifest.description,
                "source_url": source_url,
                "sha256": sha256,
                "installed_at": datetime.now(tz=timezone.utc).isoformat(),
                "tags": manifest.metadata.tags,
            }
        )
        self._save_db(records)

    def uninstall(self, skill_id: str) -> None:
        """Remove a skill record and its files."""
        records = [r for r in self._load_db() if r["id"] != skill_id]
        self._save_db(records)
        skill_dir = self.get_skill_dir(skill_id)
        if skill_dir and skill_dir.exists():
            shutil.rmtree(skill_dir)

    def get_skill_dir(self, skill_id: str) -> Optional[Path]:
        """Return the directory where a skill is installed, or None."""
        # Normalize skill_id to a safe directory name
        safe_name = skill_id.replace("/", "_").replace(":", "_")
        candidate = self.skills_dir / safe_name
        if candidate.exists():
            return candidate
        # Try finding by record
        for record in self._load_db():
            if record["id"] == skill_id:
                name_dir = self.skills_dir / record["name"]
                if name_dir.exists():
                    return name_dir
        return None

    def get_installed_manifest_path(self, skill_id: str) -> Optional[Path]:
        """Return path to skill.yaml for an installed skill."""
        skill_dir = self.get_skill_dir(skill_id)
        if skill_dir:
            candidate = skill_dir / "skill.yaml"
            if candidate.exists():
                return candidate
        return None


def parse_source(source: str) -> Registry:
    """
    Parse a source string and return the appropriate Registry instance.

    Examples:
    - 'github:user/repo' -> GitRegistry
    - '/absolute/path'   -> FileSystemRegistry
    - './relative/path'  -> FileSystemRegistry
    """
    source = source.strip()

    if source.startswith("github:") or "github.com" in source or source.startswith("git+"):
        return GitRegistry()

    # Local path
    path = Path(source).resolve()
    if path.exists():
        root = path if path.is_dir() else path.parent
        return FileSystemRegistry(root)

    # Default: assume GitHub
    return GitRegistry()
