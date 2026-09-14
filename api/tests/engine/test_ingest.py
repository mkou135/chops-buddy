"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-60 not implemented")
def test_field_ranges() -> None:
    """E-60: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-61 not implemented")
def test_break_unit_must_be_in_fragment() -> None:
    """E-61: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-62 not implemented")
def test_numbers_trusted_as_given() -> None:
    """E-62: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-63 not implemented")
def test_apply_is_order_dependent_and_repeatable() -> None:
    """E-63: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
