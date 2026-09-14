"""Session composer. docs/ENGINE_SPEC.md §5 (E-50 to E-57) and §7 (E-70, E-71)."""

import hashlib
import json
from collections.abc import Callable

from chops_buddy.engine.models import (
    EngineError,
    Fragment,
    InstrumentFamily,
    Mode,
    Prescription,
    Segment,
    SessionPlan,
    Student,
    Target,
    TargetState,
)
from chops_buddy.engine.params import threshold

DURATIONS = (10, 20, 30)
KIND_ORDER = ("long_tones", "scale", "technique", "repertoire")  # E-50
LONG_TONE_FAMILIES = {InstrumentFamily.wind, InstrumentFamily.brass, InstrumentFamily.voice}  # E-51
MIN_SEGMENT_MINUTES = 2  # E-54
ESCALATION_WEIGHT = 2  # E-54

# E-53: share of session minutes by kind.
KIND_SHARE: dict[str, float] = {
    "long_tones": 0.15,
    "scale": 0.25,
    "technique": 0.20,
    "repertoire": 0.40,
}

# E-57: exact strings are part of the spec.
TEMPLATE_WORKING = (
    "Play {fragment_label} at {tempo} BPM. Goal: {threshold} correct in a row. "
    "A mistake resets the count."
)
TEMPLATE_ISOLATING = (
    "Isolate {fragment_label} at {tempo} BPM. Goal: {threshold} correct in a row, "
    "then it goes back into context."
)
TEMPLATE_CHAINING = (
    "Build from the end: play the last {chain_len} unit(s) ({fragment_label}) at {tempo} BPM. "
    "Goal: {threshold} correct in a row, then add the unit before."
)
TEMPLATE_LONG_TONES = (
    "Long tones: sustain each note of {scale_title}, 8 counts each, at 60 BPM. "
    "Listen for a steady centre."
)

Pair = tuple[Target, TargetState]


def fragment_label(target: Target, fragment: Fragment) -> str:
    """E-57: "the whole passage" or "units {first}–{last}" using unit labels."""
    start, end = fragment
    if (start, end) == (0, len(target.units)):
        return "the whole passage"
    return f"units {target.units[start]}–{target.units[end - 1]}"


def _instruction(target: Target, state: TargetState, thr: int) -> str:
    label = fragment_label(target, state.fragment)
    if state.mode is Mode.isolating:
        return TEMPLATE_ISOLATING.format(fragment_label=label, tempo=state.tempo, threshold=thr)
    if state.mode is Mode.chaining:
        return TEMPLATE_CHAINING.format(
            chain_len=state.chain_len, fragment_label=label, tempo=state.tempo, threshold=thr
        )
    return TEMPLATE_WORKING.format(fragment_label=label, tempo=state.tempo, threshold=thr)


def _weight(state: TargetState) -> int:
    return ESCALATION_WEIGHT if state.mode in (Mode.isolating, Mode.chaining) else 1


def _allocate(
    by_kind: dict[str, list[Pair]], long_tones: bool, duration: int
) -> dict[str, list[int]]:
    """E-53/E-54: minutes per segment, keyed by kind, in kind order. Floors everywhere;
    the session remainder goes to the last segment."""
    present = [k for k in KIND_ORDER if (k == "long_tones" and long_tones) or by_kind.get(k)]
    share_total = sum(KIND_SHARE[k] for k in present)
    out: dict[str, list[int]] = {}
    for kind in present:
        kind_minutes = int(duration * KIND_SHARE[kind] / share_total)
        if kind == "long_tones":
            out[kind] = [max(MIN_SEGMENT_MINUTES, kind_minutes)]
            continue
        weights = [_weight(s) for _, s in by_kind[kind]]
        total_w = sum(weights)
        out[kind] = [kind_minutes * w // total_w for w in weights]
    last_kind = present[-1]
    allocated = sum(sum(v) for v in out.values())
    out[last_kind][-1] += duration - allocated
    return out


def compose(
    student: Student,
    targets: list[Pair],
    duration_minutes: int,
    prescription_id: Callable[[str], str],
) -> SessionPlan:
    """Build the next session.

    `prescription_id(target_id)` is supplied by the caller (E-02) so the engine
    never generates ids. Raises EngineError("nothing_to_practise") per E-56.
    """
    long_tones = student.instrument_family in LONG_TONE_FAMILIES
    by_kind: dict[str, list[Pair]] = {k: [] for k in KIND_ORDER[1:]}
    for target, state in targets:
        if state.mode is not Mode.mastered:  # E-52
            by_kind[target.kind.value].append((target, state))
    if not long_tones and not any(by_kind.values()):
        raise EngineError("nothing_to_practise", "no eligible targets and no long tones")  # E-56

    deferred: list[str] = []
    while True:  # E-55
        minutes = _allocate(by_kind, long_tones, duration_minutes)
        short = [k for k in KIND_ORDER[1:] if by_kind[k] and min(minutes[k]) < MIN_SEGMENT_MINUTES]
        if not short:
            break
        victim, _ = by_kind[short[-1]].pop()
        deferred.append(victim.id)

    segments: list[Segment] = []
    if long_tones:
        scales = by_kind["scale"]
        scale_title = scales[0][0].title if scales else "C major"
        segments.append(
            Segment(
                kind="long_tones",
                target_id=None,
                prescription=None,
                minutes=minutes["long_tones"][0],
                instruction=TEMPLATE_LONG_TONES.format(scale_title=scale_title),
            )
        )
    for kind in KIND_ORDER[1:]:
        for (target, state), mins in zip(by_kind[kind], minutes.get(kind, []), strict=True):
            thr = threshold(student.level, target)
            prescription = Prescription(
                id=prescription_id(target.id),
                target_id=target.id,
                mode=state.mode,
                fragment=state.fragment,
                tempo=state.tempo,
                threshold=thr,
                minutes=mins,
                instruction=_instruction(target, state, thr),
            )
            segments.append(
                Segment(
                    kind=kind,  # type: ignore[arg-type]
                    target_id=target.id,
                    prescription=prescription,
                    minutes=mins,
                    instruction=prescription.instruction,
                )
            )
    plan = SessionPlan(segments=segments, deferred=deferred, plan_hash="")
    return plan.model_copy(update={"plan_hash": plan_hash(plan)})


def plan_hash(plan: SessionPlan) -> str:
    """E-70: SHA-256 over canonical JSON of the segment list, excluding ids/timestamps."""
    rows = [
        {
            "kind": s.kind,
            "target_id": s.target_id,
            "mode": s.prescription.mode.value if s.prescription else None,
            "fragment": list(s.prescription.fragment) if s.prescription else None,
            "tempo": s.prescription.tempo if s.prescription else None,
            "threshold": s.prescription.threshold if s.prescription else None,
            "minutes": s.minutes,
            "instruction": s.instruction,
        }
        for s in plan.segments
    ]
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
