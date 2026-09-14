"""Session composer. docs/ENGINE_SPEC.md §5 (E-50 to E-57) and §7 (E-70, E-71).

Scaffold: signatures and the exact instruction templates from E-57.
"""

from collections.abc import Callable

from chops_buddy.engine.models import SessionPlan, Student, Target, TargetState

DURATIONS = (10, 20, 30)

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


def fragment_label(target: Target, fragment: tuple[int, int]) -> str:
    """E-57: "the whole passage" or "units {first}–{last}" using unit labels."""
    raise NotImplementedError("E-57")


def compose(
    student: Student,
    targets: list[tuple[Target, TargetState]],
    duration_minutes: int,
    prescription_id: Callable[[str], str],
) -> SessionPlan:
    """Build the next session.

    `prescription_id(target_id)` is supplied by the caller (E-02) so the engine
    never generates ids. Raises EngineError("nothing_to_practise") per E-56.
    """
    raise NotImplementedError("§5")


def plan_hash(plan: SessionPlan) -> str:
    """E-70: SHA-256 over canonical JSON of the segment list, excluding ids/timestamps."""
    raise NotImplementedError("E-70")
