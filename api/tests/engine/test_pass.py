"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-30 not implemented")
def test_working_climbs_one_rung() -> None:
    """E-30: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-31 not implemented")
def test_isolating_folds_back() -> None:
    """E-31: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-32 not implemented")
def test_chaining_prepends_one_unit_then_resumes() -> None:
    """E-32: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-33 not implemented")
def test_mastery_requires_ease_or_two_streak() -> None:
    """E-33: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
