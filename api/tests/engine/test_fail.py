"""Tests for docs/ENGINE_SPEC.md §4.4 (transitions on fail)."""

import pytest

from chops_buddy.engine.models import EngineError, Level, Mode, Target, TargetState
from chops_buddy.engine.state import apply, initial_state
from tests.engine.conftest import entry
from tests.engine.helpers import prescription_for

LEVEL = Level.intermediate  # threshold 5; walkthrough target: rung 12, floor 60, start 72


def step(state: TargetState, target: Target, **kw: object) -> TargetState:
    p = prescription_for(state, target, LEVEL)
    return apply(state, target, LEVEL, p, entry("p", **kw))  # type: ignore[arg-type]


def at_floor(target: Target, **update: object) -> TargetState:
    return initial_state(target).model_copy(update={"tempo": 60, **update})


def test_fail_increments_and_resets_streak(walkthrough_target: Target) -> None:
    s = at_floor(walkthrough_target, mastery_streak=1)
    s = s.model_copy(update={"mode": Mode.isolating, "fragment": (3, 7)})
    s = step(s, walkthrough_target, tempo_used=60, best=2)
    assert (s.fails_here, s.mastery_streak) == (1, 0)


def test_working_above_floor_halves(walkthrough_target: Target) -> None:
    s = initial_state(walkthrough_target).model_copy(update={"tempo": 84})
    s = step(s, walkthrough_target, tempo_used=84, best=3)
    assert (s.mode, s.tempo, s.fails_here) == (Mode.working, 60, 0)  # max(60, round4(42))
    s = initial_state(walkthrough_target).model_copy(update={"tempo": 96})
    s = step(s, walkthrough_target, tempo_used=96, best=0)
    assert s.tempo == 60  # max(60, round4(48)=48)


def test_working_at_floor_with_break_isolates(walkthrough_target: Target) -> None:
    s = step(at_floor(walkthrough_target), walkthrough_target, tempo_used=60, best=2, break_unit=5)
    assert (s.mode, s.fragment, s.tempo, s.fails_here) == (Mode.isolating, (3, 7), 60, 0)


def test_working_at_floor_without_break_chains(walkthrough_target: Target) -> None:
    s = step(at_floor(walkthrough_target), walkthrough_target, tempo_used=60, best=2)
    assert (s.mode, s.chain_base, s.chain_len, s.fragment, s.tempo) == (
        Mode.chaining,
        (0, 8),
        1,
        (7, 8),
        60,
    )


def test_isolating_two_fails_chains_fragment(walkthrough_target: Target) -> None:
    s = at_floor(walkthrough_target, mode=Mode.isolating, fragment=(3, 7))
    s = step(s, walkthrough_target, tempo_used=60, best=1)
    assert (s.mode, s.fails_here, s.fragment) == (Mode.isolating, 1, (3, 7))  # reissued
    s = step(s, walkthrough_target, tempo_used=60, best=1)
    assert (s.mode, s.chain_base, s.chain_len, s.fragment, s.fails_here) == (
        Mode.chaining,
        (3, 7),
        1,
        (6, 7),
        0,
    )


def test_chaining_fail_reissues(walkthrough_target: Target) -> None:
    s = at_floor(
        walkthrough_target, mode=Mode.chaining, chain_base=(0, 8), chain_len=3, fragment=(5, 8)
    )
    s = step(s, walkthrough_target, tempo_used=60, best=2)
    assert (s.mode, s.chain_len, s.fragment, s.fails_here) == (Mode.chaining, 3, (5, 8), 1)


def test_chain_of_isolated_fragment_folds_back(walkthrough_target: Target) -> None:
    s = at_floor(
        walkthrough_target, mode=Mode.chaining, chain_base=(3, 7), chain_len=3, fragment=(4, 7)
    )
    s = step(s, walkthrough_target, tempo_used=60, best=5)
    assert (s.mode, s.fragment, s.tempo) == (Mode.working, (0, 8), 60)


def test_mastered_accepts_no_entries(walkthrough_target: Target) -> None:
    s = initial_state(walkthrough_target).model_copy(update={"mode": Mode.mastered, "tempo": 120})
    with pytest.raises(EngineError) as exc:
        step(s, walkthrough_target, tempo_used=120, best=5)
    assert exc.value.code == "target_mastered"
