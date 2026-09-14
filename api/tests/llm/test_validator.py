"""Validator rules for LLM proposals (DoD: LLM layer, A5).

The proposal can only choose minutes, deferrals, and words. Everything the engine
owns (mode, tempo, fragment, threshold) comes from state, so those cannot be
changed by construction; the validator checks what the proposal *can* get wrong.
"""

from chops_buddy.engine.models import (
    InstrumentFamily,
    Level,
    Mode,
    Student,
    Target,
    TargetKind,
    TargetState,
)
from chops_buddy.engine.state import initial_state
from chops_buddy.llm.proposal import Proposal, ProposedSegment
from chops_buddy.llm.validator import LONG_TONES_ID, validate

WIND = Student(level=Level.intermediate, instrument_family=InstrumentFamily.wind)
KEYS = Student(level=Level.intermediate, instrument_family=InstrumentFamily.keyboard)


def target(tid: str, kind: TargetKind) -> Target:
    return Target(id=tid, kind=kind, title=tid, target_tempo=120, units=list("abcdefgh"))


def pair(t: Target, mode: Mode = Mode.working) -> tuple[Target, TargetState]:
    s = initial_state(t)
    if mode is Mode.isolating:
        s = s.model_copy(update={"mode": mode, "fragment": (3, 7), "tempo": 60})
    return (t, s)


def pid(tid: str) -> str:
    return f"p-{tid}"


def proposal(*segs: tuple[str, int], deferred: list[str] | None = None) -> Proposal:
    return Proposal(
        segments=[ProposedSegment(target_id=t, minutes=m) for t, m in segs],
        deferred=deferred or [],
        rationale="because",
        coaching_note="Keep the count honest.",
    )


SCALE, TECH, REP = (
    target("s1", TargetKind.scale),
    target("t1", TargetKind.technique),
    target("r1", TargetKind.repertoire),
)


def test_legal_proposal_becomes_plan_with_engine_prescriptions() -> None:
    pairs = [pair(SCALE), pair(REP)]
    result = validate(KEYS, pairs, 20, proposal(("s1", 8), ("r1", 12)), pid)
    assert result.violations == [] and result.repaired is False
    segs = result.plan.segments
    assert [(s.target_id, s.minutes) for s in segs] == [("s1", 8), ("r1", 12)]
    assert segs[1].prescription is not None and segs[1].prescription.tempo == 72
    assert segs[1].prescription.id == "p-r1"


def test_unknown_target_is_rejected_and_repaired_to_engine_plan() -> None:
    pairs = [pair(SCALE)]
    result = validate(KEYS, pairs, 10, proposal(("s1", 5), ("ghost", 5)), pid)
    assert "unassigned_target" in result.violations
    assert result.repaired is True
    assert [s.target_id for s in result.plan.segments] == ["s1"]


def test_wrong_kind_order_is_repaired_by_sorting() -> None:
    pairs = [pair(SCALE), pair(REP)]
    result = validate(KEYS, pairs, 20, proposal(("r1", 12), ("s1", 8)), pid)
    assert result.violations == ["wrong_segment_order"]
    assert [s.target_id for s in result.plan.segments] == ["s1", "r1"]
    assert [s.minutes for s in result.plan.segments] == [8, 12]  # minutes kept


def test_minutes_must_sum_to_duration() -> None:
    pairs = [pair(SCALE), pair(REP)]
    result = validate(KEYS, pairs, 20, proposal(("s1", 5), ("r1", 5)), pid)
    assert "minutes_sum" in result.violations
    assert sum(s.minutes for s in result.plan.segments) == 20


def test_segment_under_two_minutes_is_a_violation() -> None:
    pairs = [pair(SCALE), pair(REP)]
    result = validate(KEYS, pairs, 20, proposal(("s1", 1), ("r1", 19)), pid)
    assert "segment_too_short" in result.violations


def test_escalating_target_cannot_be_deferred() -> None:
    pairs = [pair(SCALE), pair(REP, Mode.isolating)]
    result = validate(KEYS, pairs, 20, proposal(("s1", 20), deferred=["r1"]), pid)
    assert "skipped_escalation" in result.violations
    assert "r1" in [s.target_id for s in result.plan.segments]


def test_working_target_may_be_deferred_with_reason() -> None:
    pairs = [pair(SCALE), pair(TECH), pair(REP)]
    result = validate(KEYS, pairs, 10, proposal(("s1", 4), ("r1", 6), deferred=["t1"]), pid)
    assert result.violations == []
    assert result.plan.deferred == ["t1"]


def test_target_neither_scheduled_nor_deferred_is_a_violation() -> None:
    pairs = [pair(SCALE), pair(REP)]
    result = validate(KEYS, pairs, 20, proposal(("s1", 20)), pid)
    assert "target_unaccounted" in result.violations


def test_long_tones_required_for_wind_and_forbidden_for_keys() -> None:
    pairs = [pair(SCALE)]
    r = validate(WIND, pairs, 10, proposal(("s1", 10)), pid)
    assert "long_tones_rule" in r.violations
    assert r.plan.segments[0].kind == "long_tones"
    r = validate(KEYS, pairs, 10, proposal((LONG_TONES_ID, 3), ("s1", 7)), pid)
    assert "long_tones_rule" in r.violations
    assert all(s.kind != "long_tones" for s in r.plan.segments)


def test_deferring_everything_falls_back_to_engine() -> None:
    pairs = [pair(SCALE)]
    r = validate(KEYS, pairs, 10, proposal(deferred=["s1"]), pid)
    assert "nothing_scheduled" in r.violations and r.repaired
    assert [s.target_id for s in r.plan.segments] == ["s1"]


def test_gamification_words_in_coaching_note_are_a_violation() -> None:
    pairs = [pair(SCALE)]
    p = proposal(("s1", 10)).model_copy(update={"coaching_note": "Keep your streak alive!"})
    r = validate(KEYS, pairs, 10, p, pid)
    assert "gamification_language" in r.violations
    assert r.plan.segments[0].instruction.startswith("Play")  # engine template, note dropped


def test_plan_hash_matches_engine_when_proposal_equals_engine_allocation() -> None:
    from chops_buddy.engine.compose import compose

    pairs = [pair(SCALE), pair(REP)]
    engine_plan = compose(KEYS, pairs, 30, pid)
    mins = [(s.target_id or "", s.minutes) for s in engine_plan.segments]
    r = validate(KEYS, pairs, 30, proposal(*mins), pid)
    assert r.plan.plan_hash == engine_plan.plan_hash
