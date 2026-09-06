"""Pytest fixtures shared across all test modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def valid_manifest_dict() -> dict[str, Any]:
    """A complete, valid skill manifest as a Python dict."""
    return {
        "asp": "1.0",
        "id": "io.github.test.code-review",
        "name": "code-review",
        "version": "1.0.0",
        "description": "Reviews source code for bugs and security issues.",
        "instructions": (
            "You are an expert code reviewer. Analyze the provided code "
            "for bugs, security vulnerabilities, and style issues."
        ),
        "authors": [{"name": "Test Author", "url": "https://github.com/testauthor"}],
        "license": "MIT",
        "inputs": [
            {
                "name": "code",
                "type": "string",
                "description": "Source code to review",
                "required": True,
            },
            {
                "name": "language",
                "type": "string",
                "description": "Programming language",
                "required": False,
                "default": "auto",
            },
        ],
        "outputs": [
            {
                "name": "review",
                "type": "string",
                "description": "Structured review findings",
            }
        ],
        "capabilities": {
            "required": ["text_generation", "instruction_following"],
            "optional": ["reasoning"],
        },
        "permissions": {
            "network": False,
            "filesystem": False,
            "code_execution": False,
        },
        "metadata": {
            "tags": ["code-quality", "security"],
            "category": "engineering",
            "created_at": "2025-01-15",
            "asp_compatible": ">=1.0.0",
        },
    }


@pytest.fixture
def minimal_manifest_dict() -> dict[str, Any]:
    """A minimal valid skill manifest with only required fields."""
    return {
        "asp": "1.0",
        "id": "io.github.test.minimal-skill",
        "name": "minimal-skill",
        "version": "0.1.0",
        "description": "A minimal skill with only required fields.",
        "instructions": "You are a helpful assistant. Answer the user's question.",
    }


@pytest.fixture
def invalid_manifest_dict() -> dict[str, Any]:
    """An invalid manifest missing required fields."""
    return {
        "name": "broken-skill",
        "version": "not-a-semver",
        # Missing: asp, id, description, instructions
    }


@pytest.fixture
def tmp_skill_dir(tmp_path: Path, valid_manifest_dict: dict[str, Any]) -> Path:
    """Create a temp directory with a valid skill.yaml."""
    manifest_path = tmp_path / "skill.yaml"
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.dump(valid_manifest_dict, f, default_flow_style=False, sort_keys=False)
    return tmp_path


@pytest.fixture
def tmp_minimal_skill_dir(tmp_path: Path, minimal_manifest_dict: dict[str, Any]) -> Path:
    """Create a temp directory with a minimal skill.yaml."""
    manifest_path = tmp_path / "skill.yaml"
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.dump(minimal_manifest_dict, f, default_flow_style=False, sort_keys=False)
    return tmp_path
