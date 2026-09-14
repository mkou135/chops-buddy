"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-50 not implemented")
def test_segment_order_fixed() -> None:
    """E-50: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-51 not implemented")
def test_long_tones_by_instrument_family() -> None:
    """E-51: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-52 not implemented")
def test_mastered_excluded() -> None:
    """E-52: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-53 not implemented")
def test_kind_allocation_and_redistribution() -> None:
    """E-53: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-54 not implemented")
def test_within_kind_weights_and_sum() -> None:
    """E-54: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-55 not implemented")
def test_drops_targets_when_too_short() -> None:
    """E-55: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-56 not implemented")
def test_nothing_to_practise_error() -> None:
    """E-56: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-57 not implemented")
def test_instruction_templates() -> None:
    """E-57: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
