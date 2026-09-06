"""ASP exception hierarchy."""

from typing import Optional


class ASPError(Exception):
    """Base exception for all ASP errors."""

    def __init__(self, message: str, hint: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        if self.hint:
            return f"{self.message}\n  Hint: {self.hint}"
        return self.message


class ManifestError(ASPError):
    """Raised when skill.yaml is missing, unreadable, or malformed YAML."""


class ValidationError(ASPError):
    """Raised when a skill manifest fails JSON Schema or semantic validation."""

    def __init__(self, message: str, errors: Optional[list[str]] = None, hint: Optional[str] = None) -> None:
        super().__init__(message, hint)
        self.errors: list[str] = errors or []

    def __str__(self) -> str:
        parts = [self.message]
        for err in self.errors:
            parts.append(f"  • {err}")
        if self.hint:
            parts.append(f"  Hint: {self.hint}")
        return "\n".join(parts)


class PackageError(ASPError):
    """Raised when a .skill package cannot be created or read."""


class IntegrityError(ASPError):
    """Raised when a package's SHA-256 checksum does not match skill.lock."""


class ResolverError(ASPError):
    """Raised when dependency resolution fails (conflict, cycle, not found)."""


class RegistryError(ASPError):
    """Raised when communication with a registry fails."""


class SkillNotFoundError(RegistryError):
    """Raised when a specific skill or version cannot be found in the registry."""

    def __init__(self, skill_id: str, version: Optional[str] = None) -> None:
        self.skill_id = skill_id
        self.version = version
        if version:
            msg = f"Skill '{skill_id}@{version}' not found in registry."
        else:
            msg = f"Skill '{skill_id}' not found in registry."
        super().__init__(msg, hint="Check the skill ID and version, or try: asp search <name>")
