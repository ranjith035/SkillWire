"""Tests for semver dependency resolution."""

from __future__ import annotations

import pytest

from asp.core.resolver import DependencyResolver


class TestSatisfies:
    """Tests for DependencyResolver.satisfies() — the core range-matching logic."""

    # --- Wildcard ---

    def test_wildcard_matches_any(self) -> None:
        assert DependencyResolver.satisfies("1.0.0", "*") is True
        assert DependencyResolver.satisfies("99.99.99", "*") is True
        assert DependencyResolver.satisfies("0.0.1", "*") is True

    def test_empty_range_matches_any(self) -> None:
        assert DependencyResolver.satisfies("1.0.0", "") is True

    # --- Exact version ---

    def test_exact_match(self) -> None:
        assert DependencyResolver.satisfies("1.2.3", "1.2.3") is True

    def test_exact_no_match(self) -> None:
        assert DependencyResolver.satisfies("1.2.4", "1.2.3") is False

    def test_exact_match_with_prerelease(self) -> None:
        assert DependencyResolver.satisfies("1.0.0-beta.1", "1.0.0-beta.1") is True

    # --- >= operator ---

    def test_gte_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.5.0", ">=1.0.0") is True
        assert DependencyResolver.satisfies("1.0.0", ">=1.0.0") is True

    def test_gte_not_satisfied(self) -> None:
        assert DependencyResolver.satisfies("0.9.9", ">=1.0.0") is False

    # --- < operator ---

    def test_lt_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.9.9", "<2.0.0") is True

    def test_lt_not_satisfied(self) -> None:
        assert DependencyResolver.satisfies("2.0.0", "<2.0.0") is False
        assert DependencyResolver.satisfies("3.0.0", "<2.0.0") is False

    # --- > operator ---

    def test_gt_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.0.1", ">1.0.0") is True

    def test_gt_not_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.0.0", ">1.0.0") is False

    # --- <= operator ---

    def test_lte_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.0.0", "<=1.0.0") is True
        assert DependencyResolver.satisfies("0.9.0", "<=1.0.0") is True

    def test_lte_not_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.0.1", "<=1.0.0") is False

    # --- != operator ---

    def test_neq_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.0.1", "!=1.0.0") is True

    def test_neq_not_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.0.0", "!=1.0.0") is False

    # --- AND (comma-separated) ---

    def test_and_range_satisfied(self) -> None:
        assert DependencyResolver.satisfies("1.5.0", ">=1.0.0,<2.0.0") is True
        assert DependencyResolver.satisfies("1.0.0", ">=1.0.0,<2.0.0") is True
        assert DependencyResolver.satisfies("1.9.9", ">=1.0.0,<2.0.0") is True

    def test_and_range_lower_bound_fails(self) -> None:
        assert DependencyResolver.satisfies("0.9.9", ">=1.0.0,<2.0.0") is False

    def test_and_range_upper_bound_fails(self) -> None:
        assert DependencyResolver.satisfies("2.0.0", ">=1.0.0,<2.0.0") is False

    # --- ^ (caret) ---

    def test_caret_same_major_minor_patch(self) -> None:
        assert DependencyResolver.satisfies("1.2.3", "^1.2.3") is True

    def test_caret_higher_minor(self) -> None:
        assert DependencyResolver.satisfies("1.5.0", "^1.2.3") is True

    def test_caret_higher_patch(self) -> None:
        assert DependencyResolver.satisfies("1.2.5", "^1.2.3") is True

    def test_caret_different_major_fails(self) -> None:
        assert DependencyResolver.satisfies("2.0.0", "^1.2.3") is False

    def test_caret_lower_than_base_fails(self) -> None:
        assert DependencyResolver.satisfies("1.2.2", "^1.2.3") is False

    def test_caret_zero_major(self) -> None:
        # ^0.2.3 → >=0.2.3 <0.3.0
        assert DependencyResolver.satisfies("0.2.5", "^0.2.3") is True
        assert DependencyResolver.satisfies("0.3.0", "^0.2.3") is False

    # --- ~ (tilde) ---

    def test_tilde_same_minor(self) -> None:
        assert DependencyResolver.satisfies("1.2.3", "~1.2.3") is True
        assert DependencyResolver.satisfies("1.2.9", "~1.2.3") is True

    def test_tilde_different_minor_fails(self) -> None:
        assert DependencyResolver.satisfies("1.3.0", "~1.2.3") is False

    def test_tilde_lower_patch_fails(self) -> None:
        assert DependencyResolver.satisfies("1.2.2", "~1.2.3") is False

    # --- Invalid version strings ---

    def test_invalid_version_returns_false(self) -> None:
        assert DependencyResolver.satisfies("not-a-version", ">=1.0.0") is False

    def test_invalid_range_returns_false(self) -> None:
        assert DependencyResolver.satisfies("1.0.0", "not-a-range") is False


class TestDependencyResolver:
    """Tests for DependencyResolver.resolve()."""

    def test_resolve_no_dependencies(self, valid_manifest_dict: dict) -> None:
        from asp.core.manifest import parse_manifest
        manifest = parse_manifest(valid_manifest_dict)
        resolver = DependencyResolver(registry=None)
        result = resolver.resolve(manifest)
        assert result == {}

    def test_resolve_returns_dict(self, valid_manifest_dict: dict) -> None:
        from asp.core.manifest import parse_manifest
        valid_manifest_dict["dependencies"] = [
            {"id": "io.github.test.dep", "version": ">=1.0.0"}
        ]
        manifest = parse_manifest(valid_manifest_dict)
        resolver = DependencyResolver(registry=None)
        result = resolver.resolve(manifest)
        assert isinstance(result, dict)
        assert "io.github.test.dep" in result
