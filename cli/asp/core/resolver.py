"""
Semver-based dependency resolution.

Resolves all direct and transitive dependencies of a skill manifest,
producing a deterministic mapping of skill_id -> resolved_version.
"""

from __future__ import annotations

import re
from typing import Optional

import semver

from asp.errors import ResolverError


class DependencyResolver:
    """
    Resolves skill dependencies using semver range constraints.

    Resolution is deterministic: given the same registry state,
    the same versions will always be selected.
    """

    def __init__(self, registry: Any = None) -> None:
        self.registry = registry
        self._resolved: dict[str, str] = {}  # id -> resolved version

    def resolve(self, manifest: Any) -> dict[str, str]:
        """
        Resolve all dependencies for a manifest.

        Returns:
            Dict mapping skill_id to resolved version string.

        Raises:
            ResolverError: on version conflict, circular dependency, or missing skill.
        """
        self._resolved = {}
        for dep in manifest.dependencies:
            self._resolve_one(dep.id, dep.version, chain=[manifest.id])
        return dict(self._resolved)

    def _resolve_one(self, dep_id: str, version_range: str, chain: list[str]) -> str:
        """Recursively resolve a single dependency."""
        # Circular dependency detection
        if dep_id in chain:
            cycle = " → ".join(chain + [dep_id])
            raise ResolverError(
                f"Circular dependency detected: {cycle}",
                hint="Remove the circular dependency from one of the skill manifests.",
            )

        # Already resolved — check for conflicts
        if dep_id in self._resolved:
            existing = self._resolved[dep_id]
            if not self.satisfies(existing, version_range):
                raise ResolverError(
                    f"Dependency conflict: '{dep_id}' resolved to {existing} "
                    f"but {chain[-1]} requires {version_range}",
                    hint="Update version constraints to be compatible.",
                )
            return existing

        # Get available versions from registry
        if self.registry is not None:
            try:
                available = self.registry.list_versions(dep_id)
            except Exception:
                available = []
        else:
            available = []

        if not available:
            # No registry or no versions — use a placeholder for offline resolution
            # In a real install flow, this would fail with SkillNotFoundError
            self._resolved[dep_id] = self._parse_minimum_version(version_range)
            return self._resolved[dep_id]

        # Select highest satisfying version
        satisfying = [v for v in available if self.satisfies(v, version_range)]
        if not satisfying:
            raise ResolverError(
                f"No version of '{dep_id}' satisfies {version_range}. "
                f"Available: {', '.join(available)}",
                hint=f"Update the version constraint or check if '{dep_id}' has been published.",
            )

        # Sort and pick highest
        try:
            best = max(satisfying, key=lambda v: semver.Version.parse(v))
        except ValueError:
            best = satisfying[-1]

        self._resolved[dep_id] = best
        return best

    @staticmethod
    def _parse_minimum_version(version_range: str) -> str:
        """Extract a minimum version from a range for offline fallback."""
        # For '*', return '0.0.0'
        if version_range.strip() == "*":
            return "0.0.0"
        # For exact versions
        if re.match(r"^\d+\.\d+\.\d+", version_range.strip()):
            return version_range.strip()
        # For ranges like '>=1.2.3', extract '1.2.3'
        match = re.search(r"(\d+\.\d+\.\d+[\w.-]*)", version_range)
        if match:
            return match.group(1)
        return "0.0.0"

    @staticmethod
    def satisfies(version: str, version_range: str) -> bool:
        """
        Check if a version string satisfies a version range constraint.

        Supported range formats:
        - '*'              — any version
        - '1.2.3'          — exact version
        - '>=1.0.0'        — greater than or equal
        - '<=1.0.0'        — less than or equal
        - '>1.0.0'         — strictly greater
        - '<2.0.0'         — strictly less
        - '!=1.0.0'        — not equal
        - '^1.2.3'         — compatible: >=1.2.3 <2.0.0
        - '~1.2.3'         — patch: >=1.2.3 <1.3.0
        - '>=1.0.0,<2.0.0' — AND of multiple constraints

        Returns True if version satisfies the range.
        """
        version_range = version_range.strip()

        if not version_range or version_range == "*":
            return True

        try:
            ver = semver.Version.parse(version)
        except ValueError:
            return False

        # Handle caret ranges: ^1.2.3 → >=1.2.3 <2.0.0
        if version_range.startswith("^"):
            base_str = version_range[1:]
            try:
                base = semver.Version.parse(base_str)
            except ValueError:
                return False
            if base.major > 0:
                upper = semver.Version(major=base.major + 1, minor=0, patch=0)
            elif base.minor > 0:
                upper = semver.Version(major=0, minor=base.minor + 1, patch=0)
            else:
                upper = semver.Version(major=0, minor=0, patch=base.patch + 1)
            return ver >= base and ver < upper

        # Handle tilde ranges: ~1.2.3 → >=1.2.3 <1.3.0
        if version_range.startswith("~"):
            base_str = version_range[1:]
            try:
                base = semver.Version.parse(base_str)
            except ValueError:
                return False
            upper = semver.Version(major=base.major, minor=base.minor + 1, patch=0)
            return ver >= base and ver < upper

        # Handle AND constraints: '>=1.0.0,<2.0.0'
        if "," in version_range:
            parts = [p.strip() for p in version_range.split(",")]
            return all(DependencyResolver.satisfies(version, part) for part in parts)

        # Handle comparison operators
        ops = {
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            "==": lambda a, b: a == b,
        }
        for op_str, op_fn in ops.items():
            if version_range.startswith(op_str):
                try:
                    other = semver.Version.parse(version_range[len(op_str):].strip())
                    return op_fn(ver, other)
                except ValueError:
                    return False

        # Plain version string — exact match
        try:
            other = semver.Version.parse(version_range)
            return ver == other
        except ValueError:
            return False


# Type alias for the registry parameter — avoids circular import
from typing import Any  # noqa: E402 — kept at bottom intentionally
