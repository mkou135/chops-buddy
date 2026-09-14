"""Deterministic validator for proposals (DoD: LLM layer, A5).

Turns a Proposal into a SessionPlan built from engine prescriptions, recording every
rule the proposal broke and repairing where a repair is well-defined. Anything that
cannot be repaired locally falls back to the engine's own plan (E-56 territory).
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from chops_buddy.engine import compose as engine_compose
from chops_buddy.engine.models import (
    Mode,
    Prescription,
    Segment,
    SessionPlan,
    Student,
    Target,
    TargetState,
)
from chops_buddy.engine.params import threshold
from chops_buddy.llm.proposal import Proposal

LONG_TONES_ID = "long_tones"
GAMIFICATION_WORDS = ("streak", "points", "badge", "leaderboard", "xp", "level up")
Pair = tuple[Target, TargetState]


@dataclass
class ValidationResult:
    plan: SessionPlan
    violations: list[str] = field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    repaired: bool = False
    coaching_note: str | None = None
    rationale: str | None = None

    @property
    def legal(self) -> bool:
        return not self.violations


def _engine_plan(
    student: Student, pairs: list[Pair], duration: int, pid: Callable[[str], str]
) -> SessionPlan:
    return engine_compose.compose(student, pairs, duration, pid)


def validate(
    student: Student,
    pairs: list[Pair],
    duration_minutes: int,
    proposal: Proposal,
    prescription_id: Callable[[str], str],
) -> ValidationResult:
    violations: list[str] = []
    active = {t.id: (t, s) for t, s in pairs if s.mode is not Mode.mastered}
    wants_long_tones = student.instrument_family in engine_compose.LONG_TONE_FAMILIES

    # Words first: they never affect the plan, only whether we pass them through.
    note = proposal.coaching_note
    if any(re.search(rf"\b{re.escape(w)}\b", note.lower()) for w in GAMIFICATION_WORDS):
        violations.append("gamification_language")
        note = ""

    scheduled: list[tuple[str, int]] = []
    seen: set[str] = set()
    for seg in proposal.segments:
        if seg.target_id == LONG_TONES_ID:
            if not wants_long_tones:
                violations.append("long_tones_rule")
                continue
        elif seg.target_id not in active:
            violations.append("unassigned_target")
            continue
        if seg.target_id in seen:
            violations.append("duplicate_target")
            continue
        seen.add(seg.target_id)
        scheduled.append((seg.target_id, seg.minutes))

    if wants_long_tones and LONG_TONES_ID not in seen:
        violations.append("long_tones_rule")
        scheduled.insert(0, (LONG_TONES_ID, 0))
        seen.add(LONG_TONES_ID)

    deferred = [d for d in proposal.deferred if d in active and d not in seen]
    for tid in deferred:
        if active[tid][1].mode in (Mode.isolating, Mode.chaining):
            violations.append("skipped_escalation")
    unaccounted = [tid for tid in active if tid not in seen and tid not in deferred]
    if unaccounted:
        violations.append("target_unaccounted")

    real_targets = [tid for tid, _ in scheduled if tid != LONG_TONES_ID]
    if not real_targets and active:
        violations.append("nothing_scheduled")

    # Unrepairable locally: fall back to the engine plan wholesale.
    fatal = {
        "unassigned_target",
        "skipped_escalation",
        "target_unaccounted",
        "nothing_scheduled",
        "duplicate_target",
    }
    if fatal & set(violations):
        plan = _engine_plan(student, pairs, duration_minutes, prescription_id)
        return ValidationResult(
            plan=plan,
            violations=violations,
            repaired=True,
            coaching_note=note or None,
            rationale=proposal.rationale,
        )

    # Order: fixed kind order (E-50), assignment order within kind.
    def sort_key(item: tuple[str, int]) -> tuple[int, int]:
        tid = item[0]
        if tid == LONG_TONES_ID:
            return (0, 0)
        kind_rank = engine_compose.KIND_ORDER.index(active[tid][0].kind.value)
        assignment_rank = [t.id for t, _ in pairs].index(tid)
        return (kind_rank, assignment_rank)

    ordered = sorted(scheduled, key=sort_key)
    repaired = False
    if ordered != scheduled:
        violations.append("wrong_segment_order")
        repaired = True

    minutes = [m for _, m in ordered]
    if sum(minutes) != duration_minutes or any(
        m < engine_compose.MIN_SEGMENT_MINUTES for m in minutes
    ):
        if sum(minutes) != duration_minutes:
            violations.append("minutes_sum")
        if any(m < engine_compose.MIN_SEGMENT_MINUTES for m in minutes):
            violations.append("segment_too_short")
        # Repair: engine allocation over the same set of scheduled targets.
        subset = [active[tid] for tid, _ in ordered if tid != LONG_TONES_ID]
        engine_plan = _engine_plan(student, subset, duration_minutes, prescription_id)
        engine_minutes = {s.target_id or LONG_TONES_ID: s.minutes for s in engine_plan.segments}
        ordered = [(tid, engine_minutes.get(tid, 0)) for tid, _ in ordered]
        ordered = [(tid, m) for tid, m in ordered if m > 0]
        repaired = True

    segments: list[Segment] = []
    for tid, mins in ordered:
        if tid == LONG_TONES_ID:
            scales = [t for t, _ in pairs if t.kind.value == "scale" and t.id in active]
            title = scales[0].title if scales else "C major"
            segments.append(
                Segment(
                    kind="long_tones",
                    target_id=None,
                    prescription=None,
                    minutes=mins,
                    instruction=engine_compose.TEMPLATE_LONG_TONES.format(scale_title=title),
                )
            )
            continue
        target, state = active[tid]
        thr = threshold(student.level, target)
        prescription = Prescription(
            id=prescription_id(tid),
            target_id=tid,
            mode=state.mode,
            fragment=state.fragment,
            tempo=state.tempo,
            threshold=thr,
            minutes=mins,
            instruction=engine_compose._instruction(target, state, thr),  # pyright: ignore[reportPrivateUsage]
        )
        segments.append(
            Segment(
                kind=target.kind.value,
                target_id=tid,
                prescription=prescription,
                minutes=mins,
                instruction=prescription.instruction,
            )  # type: ignore[arg-type]
        )

    plan = SessionPlan(segments=segments, deferred=deferred, plan_hash="")
    plan = plan.model_copy(update={"plan_hash": engine_compose.plan_hash(plan)})
    return ValidationResult(
        plan=plan,
        violations=violations,
        repaired=repaired,
        coaching_note=note or None,
        rationale=proposal.rationale,
    )
