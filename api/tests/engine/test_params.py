"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-10 not implemented")
def test_threshold_by_level_and_override() -> None:
    """E-10: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-11 not implemented")
def test_rung_is_ten_percent_min_4() -> None:
    """E-11: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-12 not implemented")
def test_tempo_floor_is_half_target() -> None:
    """E-12: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-13 not implemented")
def test_initial_tempo_default_and_override() -> None:
    """E-13: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-14 not implemented")
def test_isolation_window_and_phrase_override() -> None:
    """E-14: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-15 not implemented")
def test_target_requires_units() -> None:
    """E-15: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
