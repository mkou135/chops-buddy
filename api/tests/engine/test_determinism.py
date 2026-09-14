"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-03 not implemented")
def test_plan_is_byte_identical_across_100_runs() -> None:
    """E-03: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-70 not implemented")
def test_plan_hash_excludes_ids_and_timestamps() -> None:
    """E-70: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-71 not implemented")
def test_equal_hash_means_equal_visible_plan() -> None:
    """E-71: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
