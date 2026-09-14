"""Tests for docs/ENGINE_SPEC.md §4.3 (transitions on pass)."""

from chops_buddy.engine.models import Level, Mode, Target, TargetState
from chops_buddy.engine.state import apply, initial_state
from tests.engine.conftest import entry
from tests.engine.helpers import prescription_for

LEVEL = Level.intermediate  # threshold 5; walkthrough target: rung 12, floor 60, start 72


def step(state: TargetState, target: Target, **kw: object) -> TargetState:
    p = prescription_for(state, target, LEVEL)
    return apply(state, target, LEVEL, p, entry("p", **kw))  # type: ignore[arg-type]


def test_working_climbs_one_rung(walkthrough_target: Target) -> None:
    s = initial_state(walkthrough_target)
    s = step(s, walkthrough_target, tempo_used=72, best=5)
    assert (s.mode, s.tempo, s.fails_here) == (Mode.working, 84, 0)
    # Capped at target tempo.
    s = s.model_copy(update={"tempo": 116})
    s = step(s, walkthrough_target, tempo_used=116, best=5)
    assert s.tempo == 120


def test_isolating_folds_back(walkthrough_target: Target) -> None:
    s = initial_state(walkthrough_target).model_copy(
        update={"mode": Mode.isolating, "tempo": 60, "fragment": (3, 7), "fails_here": 1}
    )
    s = step(s, walkthrough_target, tempo_used=60, best=5)
    assert (s.mode, s.fragment, s.tempo, s.fails_here) == (Mode.working, (0, 8), 60, 0)


def test_chaining_prepends_one_unit_then_resumes(walkthrough_target: Target) -> None:
    s = initial_state(walkthrough_target).model_copy(
        update={
            "mode": Mode.chaining,
            "tempo": 60,
            "chain_base": (0, 8),
            "chain_len": 1,
            "fragment": (7, 8),
        }
    )
    s = step(s, walkthrough_target, tempo_used=60, best=5)
    assert (s.mode, s.chain_len, s.fragment) == (Mode.chaining, 2, (6, 8))
    s = s.model_copy(update={"chain_len": 7, "fragment": (1, 8)})
    s = step(s, walkthrough_target, tempo_used=60, best=5)
    assert (s.mode, s.fragment, s.tempo) == (Mode.working, (0, 8), 60)


def test_mastery_requires_ease_or_two_streak(walkthrough_target: Target) -> None:
    at_target = initial_state(walkthrough_target).model_copy(update={"tempo": 120})
    # Hard but correct: streak 1, reissued.
    s = step(at_target, walkthrough_target, tempo_used=120, best=5, difficulty=4)
    assert (s.mode, s.mastery_streak, s.tempo) == (Mode.working, 1, 120)
    # Second time, still hard: mastered by streak.
    s = step(s, walkthrough_target, tempo_used=120, best=5, difficulty=5)
    assert s.mode == Mode.mastered
    # Easy first time: mastered immediately.
    s = step(at_target, walkthrough_target, tempo_used=120, best=5, difficulty=3)
    assert s.mode == Mode.mastered
