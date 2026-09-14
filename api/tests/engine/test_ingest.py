"""Tests for docs/ENGINE_SPEC.md §6 (log ingestion)."""

import pytest
from pydantic import ValidationError

from chops_buddy.engine.models import EngineError, Level, LogEntry, Target, TargetState
from chops_buddy.engine.state import apply, initial_state
from tests.engine.conftest import entry
from tests.engine.helpers import prescription_for

LEVEL = Level.intermediate


def test_field_ranges() -> None:
    with pytest.raises(ValidationError):
        LogEntry(prescription_id="p", tempo_used=10, best_consecutive=5, felt_difficulty=3)
    with pytest.raises(ValidationError):
        LogEntry(prescription_id="p", tempo_used=72, best_consecutive=51, felt_difficulty=3)
    with pytest.raises(ValidationError):
        LogEntry(prescription_id="p", tempo_used=72, best_consecutive=5, felt_difficulty=0)
    with pytest.raises(ValidationError):
        LogEntry(
            prescription_id="p",
            tempo_used=72,
            best_consecutive=5,
            felt_difficulty=3,
            free_text="x" * 501,
        )


def test_break_unit_must_be_in_fragment(walkthrough_target: Target) -> None:
    s = initial_state(walkthrough_target)  # whole fragment (0, 8)
    p = prescription_for(s, walkthrough_target, LEVEL)
    with pytest.raises(EngineError) as exc:
        apply(s, walkthrough_target, LEVEL, p, entry("p", tempo_used=72, best=2, break_unit=8))
    assert exc.value.code == "break_unit_out_of_fragment"
    isolating = s.model_copy(update={"fragment": (3, 7), "tempo": 60})
    p2 = prescription_for(isolating, walkthrough_target, LEVEL)
    with pytest.raises(EngineError):
        apply(
            isolating,
            walkthrough_target,
            LEVEL,
            p2,
            entry("p", tempo_used=60, best=2, break_unit=1),
        )


def test_numbers_trusted_as_given(walkthrough_target: Target) -> None:
    # An implausible report (50 in a row, at double the tempo) still counts as a pass.
    s = initial_state(walkthrough_target)
    p = prescription_for(s, walkthrough_target, LEVEL)
    s2 = apply(s, walkthrough_target, LEVEL, p, entry("p", tempo_used=144, best=50))
    assert s2.tempo == 84


def run(s: TargetState, target: Target, entries: list[tuple[int, int]]) -> TargetState:
    for tempo_used, best in entries:
        p = prescription_for(s, target, LEVEL)
        s = apply(s, target, LEVEL, p, entry("p", tempo_used=tempo_used, best=best))
    return s


def test_apply_is_order_dependent_and_repeatable(walkthrough_target: Target) -> None:
    s0 = initial_state(walkthrough_target)
    a = run(s0, walkthrough_target, [(72, 5), (84, 2)])  # climb then halve → 60
    b = run(s0, walkthrough_target, [(72, 2), (60, 5)])  # halve... → 60, then climb → 72
    assert a.tempo == 60 and b.tempo == 72
    assert run(s0, walkthrough_target, [(72, 5), (84, 2)]) == a
    assert s0 == initial_state(walkthrough_target)  # inputs never mutated
