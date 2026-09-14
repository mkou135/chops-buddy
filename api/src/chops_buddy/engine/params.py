"""Derived parameters. docs/ENGINE_SPEC.md §3 (E-10 to E-14).

Scaffold: signatures only. Michael implements each; the tests in
tests/engine/test_params.py are the acceptance criteria.
"""

from chops_buddy.engine.models import Fragment, Level, Target

THRESHOLD_BY_LEVEL: dict[Level, int] = {
    Level.beginner: 3,
    Level.intermediate: 5,
    Level.advanced: 7,
}


def round4(bpm: float) -> int:
    """Round down to a multiple of 4, floored at 30 (spec §3 preamble)."""
    raise NotImplementedError("E-11/E-12/E-13 depend on this")


def threshold(level: Level, target: Target) -> int:
    """E-10."""
    raise NotImplementedError("E-10")


def rung(target: Target) -> int:
    """E-11."""
    raise NotImplementedError("E-11")


def tempo_floor(target: Target) -> int:
    """E-12."""
    raise NotImplementedError("E-12")


def initial_tempo(target: Target) -> int:
    """E-13."""
    raise NotImplementedError("E-13")


def isolation_fragment(target: Target, break_unit: int) -> Fragment:
    """E-14."""
    raise NotImplementedError("E-14")
