"""Tests for docs/ENGINE_SPEC.md rules. Each test is named in the spec table (DoD A2)."""

import pytest


@pytest.mark.xfail(strict=True, reason="E-20 not implemented")
def test_pass_requires_tempo_and_threshold() -> None:
    """E-20: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError


@pytest.mark.xfail(strict=True, reason="E-21 not implemented")
def test_stale_prescription_rejected() -> None:
    """E-21: see docs/ENGINE_SPEC.md."""
    raise NotImplementedError
