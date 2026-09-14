"""Derived parameters. docs/ENGINE_SPEC.md §3 (E-10 to E-14)."""

import math

from chops_buddy.engine.models import Fragment, Level, Target

THRESHOLD_BY_LEVEL: dict[Level, int] = {
    Level.beginner: 3,
    Level.intermediate: 5,
    Level.advanced: 7,
}

MIN_TEMPO = 30
MIN_RUNG = 4
ISOLATION_WINDOW = 4


def round4(bpm: float) -> int:
    """Round down to a multiple of 4, floored at 30 (spec §3 preamble)."""
    return max(MIN_TEMPO, (math.floor(bpm) // 4) * 4)


def threshold(level: Level, target: Target) -> int:
    """E-10."""
    if target.threshold_override is not None:
        return target.threshold_override
    return THRESHOLD_BY_LEVEL[level]


def rung(target: Target) -> int:
    """E-11."""
    return max(MIN_RUNG, (math.floor(0.10 * target.target_tempo) // 4) * 4)


def tempo_floor(target: Target) -> int:
    """E-12."""
    return round4(0.50 * target.target_tempo)


def initial_tempo(target: Target) -> int:
    """E-13."""
    tempo = target.start_tempo if target.start_tempo is not None else round4(0.60 * target.target_tempo)
    return max(tempo_floor(target), tempo)


def isolation_fragment(target: Target, break_unit: int) -> Fragment:
    """E-14."""
    if target.phrases is not None:
        for start, end in target.phrases:
            if start <= break_unit < end:
                return (start, end)
    n = len(target.units)
    half = ISOLATION_WINDOW // 2
    start = max(0, break_unit - half)
    end = min(n, break_unit + half)
    return (start, end)
