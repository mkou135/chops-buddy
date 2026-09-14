"""Tests for docs/ENGINE_SPEC.md §3. Each test is named in the spec table (DoD A2)."""

import pytest
from pydantic import ValidationError

from chops_buddy.engine.models import Level, Target, TargetKind
from chops_buddy.engine.params import (
    initial_tempo,
    isolation_fragment,
    round4,
    rung,
    tempo_floor,
    threshold,
)


def make_target(
    tempo: int = 120,
    n_units: int = 8,
    *,
    start_tempo: int | None = None,
    threshold_override: int | None = None,
    phrases: list[tuple[int, int]] | None = None,
) -> Target:
    return Target(
        id="t",
        kind=TargetKind.repertoire,
        title="t",
        target_tempo=tempo,
        units=[f"u{i}" for i in range(n_units)],
        start_tempo=start_tempo,
        threshold_override=threshold_override,
        phrases=phrases,
    )


def test_round4_rounds_down_to_multiple_of_4_floored_at_30() -> None:
    assert round4(72.0) == 72
    assert round4(73.9) == 72
    assert round4(75) == 72
    assert round4(31) == 30
    assert round4(10) == 30


def test_threshold_by_level_and_override() -> None:
    assert threshold(Level.beginner, make_target()) == 3
    assert threshold(Level.intermediate, make_target()) == 5
    assert threshold(Level.advanced, make_target()) == 7
    assert threshold(Level.beginner, make_target(threshold_override=6)) == 6


def test_rung_is_ten_percent_min_4() -> None:
    assert rung(make_target(120)) == 12
    assert rung(make_target(200)) == 20
    assert rung(make_target(30)) == 4  # 10% would be 3


def test_tempo_floor_is_half_target() -> None:
    assert tempo_floor(make_target(120)) == 60
    assert tempo_floor(make_target(130)) == 64  # round4(65)
    assert tempo_floor(make_target(40)) == 30  # never below 30


def test_initial_tempo_default_and_override() -> None:
    assert initial_tempo(make_target(120)) == 72  # round4(72)
    assert initial_tempo(make_target(120, start_tempo=90)) == 90
    assert initial_tempo(make_target(120, start_tempo=40)) == 60  # clamped to floor
    assert initial_tempo(make_target(50)) == 30  # round4(30)


def test_isolation_window_and_phrase_override() -> None:
    # 4 units centred on the break: [break-2, break+2), clipped.
    assert isolation_fragment(make_target(n_units=8), 5) == (3, 7)
    assert isolation_fragment(make_target(n_units=8), 0) == (0, 2)
    assert isolation_fragment(make_target(n_units=8), 7) == (5, 8)
    # Teacher phrases win.
    phrased = make_target(n_units=8, phrases=[(0, 3), (3, 8)])
    assert isolation_fragment(phrased, 5) == (3, 8)
    assert isolation_fragment(phrased, 1) == (0, 3)


def test_target_requires_units() -> None:
    with pytest.raises(ValidationError):
        Target(id="t", kind=TargetKind.scale, title="t", target_tempo=100, units=[])


def test_phrases_must_cover_units_without_gaps_or_overlap() -> None:
    with pytest.raises(ValidationError):
        make_target(n_units=8, phrases=[(0, 3), (4, 8)])  # gap
    with pytest.raises(ValidationError):
        make_target(n_units=8, phrases=[(0, 4), (3, 8)])  # overlap
    with pytest.raises(ValidationError):
        make_target(n_units=8, phrases=[(0, 8), (8, 9)])  # beyond n
