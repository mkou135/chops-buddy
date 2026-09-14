"""Tests for docs/ENGINE_SPEC.md §5 (session composer)."""

import pytest

from chops_buddy.engine.compose import compose, fragment_label
from chops_buddy.engine.models import (
    EngineError,
    InstrumentFamily,
    Level,
    Mode,
    SessionPlan,
    Student,
    Target,
    TargetKind,
    TargetState,
)
from chops_buddy.engine.state import initial_state


def target(tid: str, kind: TargetKind, n: int = 8, tempo: int = 120) -> Target:
    return Target(
        id=tid,
        kind=kind,
        title=f"Title {tid}",
        target_tempo=tempo,
        units=[f"b{i}" for i in range(1, n + 1)],
    )


def pair(t: Target, mode: Mode = Mode.working) -> tuple[Target, TargetState]:
    s = initial_state(t)
    if mode is Mode.isolating:
        s = s.model_copy(update={"mode": mode, "fragment": (3, 7), "tempo": 60})
    elif mode is Mode.chaining:
        s = s.model_copy(update={"mode": mode, "chain_len": 2, "fragment": (6, 8), "tempo": 60})
    elif mode is Mode.mastered:
        s = s.model_copy(update={"mode": mode, "tempo": 120})
    return (t, s)


def pid(target_id: str) -> str:
    return f"p-{target_id}"


WIND = Student(level=Level.intermediate, instrument_family=InstrumentFamily.wind)
KEYS = Student(level=Level.intermediate, instrument_family=InstrumentFamily.keyboard)


def plan(
    student: Student, pairs: list[tuple[Target, TargetState]], minutes: int = 30
) -> SessionPlan:
    return compose(student, pairs, minutes, pid)


def test_segment_order_fixed() -> None:
    pairs = [
        pair(target("r1", TargetKind.repertoire)),
        pair(target("t1", TargetKind.technique)),
        pair(target("s2", TargetKind.scale)),
        pair(target("s1", TargetKind.scale)),
    ]
    kinds_and_ids = [(seg.kind, seg.target_id) for seg in plan(WIND, pairs).segments]
    assert kinds_and_ids == [
        ("long_tones", None),
        ("scale", "s2"),
        ("scale", "s1"),
        ("technique", "t1"),
        ("repertoire", "r1"),
    ]


def test_long_tones_by_instrument_family() -> None:
    pairs = [pair(target("s1", TargetKind.scale))]
    for family in (InstrumentFamily.wind, InstrumentFamily.brass, InstrumentFamily.voice):
        student = Student(level=Level.beginner, instrument_family=family)
        first = plan(student, pairs).segments[0]
        assert first.kind == "long_tones"
        assert "Title s1" in first.instruction
    for family in (
        InstrumentFamily.strings,
        InstrumentFamily.keyboard,
        InstrumentFamily.percussion,
    ):
        student = Student(level=Level.beginner, instrument_family=family)
        assert all(seg.kind != "long_tones" for seg in plan(student, pairs).segments)
    # No scale assigned: C major is named.
    only_rep = [pair(target("r1", TargetKind.repertoire))]
    assert "C major" in plan(WIND, only_rep).segments[0].instruction


def test_mastered_excluded() -> None:
    pairs = [
        pair(target("s1", TargetKind.scale)),
        pair(target("s2", TargetKind.scale), Mode.mastered),
    ]
    ids = [seg.target_id for seg in plan(KEYS, pairs).segments]
    assert ids == ["s1"]


def test_kind_allocation_and_redistribution() -> None:
    # All four kinds present, 20 minutes: 15/25/20/40 % → 3/5/4/8.
    pairs = [
        pair(target("s1", TargetKind.scale)),
        pair(target("t1", TargetKind.technique)),
        pair(target("r1", TargetKind.repertoire)),
    ]
    minutes = [seg.minutes for seg in plan(WIND, pairs, 20).segments]
    assert minutes == [3, 5, 4, 8]
    # No technique, no long tones (keyboard): scales and repertoire share 25:40 of 30.
    pairs = [pair(target("s1", TargetKind.scale)), pair(target("r1", TargetKind.repertoire))]
    minutes = [seg.minutes for seg in plan(KEYS, pairs, 30).segments]
    assert minutes == [11, 19]  # 30 × 25/65 = 11.5 → 11, remainder to last


def test_within_kind_weights_and_sum() -> None:
    # Two repertoire targets, one working (weight 1) and one isolating (weight 2).
    # Keyboard, 30 minutes: all 30 go to repertoire.
    pairs = [
        pair(target("r1", TargetKind.repertoire)),
        pair(target("r2", TargetKind.repertoire), Mode.isolating),
    ]
    segs = plan(KEYS, pairs, 30).segments
    assert [(s.target_id, s.minutes) for s in segs] == [("r1", 10), ("r2", 20)]
    for duration in (10, 20, 30):
        assert sum(s.minutes for s in plan(WIND, pairs, duration).segments) == duration


def test_drops_targets_when_too_short() -> None:
    # 10-minute keyboard session, five scales: 10 minutes for scales, 2 each, all fit.
    five = [pair(target(f"s{i}", TargetKind.scale)) for i in range(5)]
    result = plan(KEYS, five, 10)
    assert [s.minutes for s in result.segments] == [2, 2, 2, 2, 2]
    assert result.deferred == []
    # Six scales cannot fit; the last-assigned one is deferred.
    six = five + [pair(target("s5", TargetKind.scale))]
    result = plan(KEYS, six, 10)
    assert [s.target_id for s in result.segments] == ["s0", "s1", "s2", "s3", "s4"]
    assert result.deferred == ["s5"]
    assert sum(s.minutes for s in result.segments) == 10


def test_nothing_to_practise_error() -> None:
    with pytest.raises(EngineError) as exc:
        plan(KEYS, [], 20)
    assert exc.value.code == "nothing_to_practise"
    with pytest.raises(EngineError):
        plan(KEYS, [pair(target("s1", TargetKind.scale), Mode.mastered)], 20)
    # Wind with nothing assigned still gets long tones only.
    only = plan(WIND, [], 10).segments
    assert [s.kind for s in only] == ["long_tones"] and only[0].minutes == 10


def test_instruction_templates() -> None:
    t = target("r1", TargetKind.repertoire)
    working = plan(KEYS, [pair(t)]).segments[0]
    assert working.instruction == (
        "Play the whole passage at 72 BPM. Goal: 5 correct in a row. A mistake resets the count."
    )
    isolating = plan(KEYS, [pair(t, Mode.isolating)]).segments[0]
    assert isolating.instruction == (
        "Isolate units b4–b7 at 60 BPM. Goal: 5 correct in a row, then it goes back into context."
    )
    chaining = plan(KEYS, [pair(t, Mode.chaining)]).segments[0]
    assert chaining.instruction == (
        "Build from the end: play the last 2 unit(s) (units b7–b8) at 60 BPM. "
        "Goal: 5 correct in a row, then add the unit before."
    )
    assert fragment_label(t, (0, 8)) == "the whole passage"
    assert fragment_label(t, (2, 3)) == "units b3–b3"
    for word in ("streak", "points", "badge"):
        assert (
            word not in (working.instruction + isolating.instruction + chaining.instruction).lower()
        )


def test_prescription_ids_come_from_caller() -> None:
    seg = plan(KEYS, [pair(target("r1", TargetKind.repertoire))]).segments[0]
    assert seg.prescription is not None and seg.prescription.id == "p-r1"
