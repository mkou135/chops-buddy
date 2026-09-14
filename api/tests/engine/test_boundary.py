"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-01 not implemented")
def test_engine_imports_only_stdlib_and_pydantic() -> None:
    """E-01: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-02 not implemented")
def test_engine_has_no_io_clock_or_random() -> None:
    """E-02: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
