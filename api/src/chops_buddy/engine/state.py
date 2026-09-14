"""Per-target state machine. docs/ENGINE_SPEC.md §4 (E-20 to E-47, E-60 to E-63).

`apply` is the single entry point: a pure function of
(state, target, level, prescription, entry) that returns a new state.
"""

from chops_buddy.engine.models import (
    EngineError,
    Fragment,
    Level,
    LogEntry,
    Mode,
    Prescription,
    Target,
    TargetState,
)
from chops_buddy.engine.params import (
    initial_tempo,
    isolation_fragment,
    round4,
    rung,
    tempo_floor,
    threshold,
)

ISOLATING_FAILS_BEFORE_CHAIN = 2  # E-44
MASTERY_EASE_MAX_DIFFICULTY = 3  # E-33
MASTERY_STREAK_REGARDLESS = 2  # E-33


def initial_state(target: Target) -> TargetState:
    """§4.1 initial state."""
    whole: Fragment = (0, len(target.units))
    return TargetState(
        mode=Mode.working, tempo=initial_tempo(target), fragment=whole, chain_base=whole
    )


def is_pass(entry: LogEntry, prescription: Prescription) -> bool:
    """E-20."""
    return (
        entry.tempo_used >= prescription.tempo and entry.best_consecutive >= prescription.threshold
    )


def _validate(state: TargetState, prescription: Prescription, entry: LogEntry) -> None:
    if state.mode is Mode.mastered:
        raise EngineError("target_mastered", "mastered targets accept no log entries")  # E-47
    if entry.prescription_id != prescription.id or (
        prescription.mode,
        prescription.fragment,
        prescription.tempo,
    ) != (state.mode, state.fragment, state.tempo):
        raise EngineError(
            "stale_prescription", "entry does not match the current prescription"
        )  # E-21
    if entry.break_unit is not None:
        start, end = prescription.fragment
        if not start <= entry.break_unit < end:
            raise EngineError(
                "break_unit_out_of_fragment", "break_unit must lie in the prescribed fragment"
            )  # E-61


def _suffix(base: Fragment, chain_len: int) -> Fragment:
    return (base[1] - chain_len, base[1])


def _on_pass(state: TargetState, target: Target, entry: LogEntry) -> TargetState:
    whole: Fragment = (0, len(target.units))
    if state.mode is Mode.working:
        if state.tempo < target.target_tempo:  # E-30
            return state.model_copy(
                update={
                    "tempo": min(target.target_tempo, state.tempo + rung(target)),
                    "fails_here": 0,
                }
            )
        streak = state.mastery_streak + 1  # E-33
        mastered = (
            entry.felt_difficulty <= MASTERY_EASE_MAX_DIFFICULTY
            or streak >= MASTERY_STREAK_REGARDLESS
        )
        return state.model_copy(
            update={
                "mode": Mode.mastered if mastered else Mode.working,
                "mastery_streak": streak,
                "fails_here": 0,
            }
        )
    if state.mode is Mode.isolating:  # E-31
        return state.model_copy(update={"mode": Mode.working, "fragment": whole, "fails_here": 0})
    # chaining: E-32, E-46
    chain_len = state.chain_len + 1
    if chain_len >= state.chain_base[1] - state.chain_base[0]:
        return state.model_copy(
            update={
                "mode": Mode.working,
                "fragment": whole,
                "chain_base": whole,
                "chain_len": 0,
                "fails_here": 0,
            }
        )
    return state.model_copy(
        update={
            "chain_len": chain_len,
            "fragment": _suffix(state.chain_base, chain_len),
            "fails_here": 0,
        }
    )


def _start_chain(state: TargetState, base: Fragment) -> TargetState:
    return state.model_copy(
        update={
            "mode": Mode.chaining,
            "chain_base": base,
            "chain_len": 1,
            "fragment": _suffix(base, 1),
            "fails_here": 0,
        }
    )


def _on_fail(state: TargetState, target: Target, entry: LogEntry) -> TargetState:
    state = state.model_copy(
        update={"fails_here": state.fails_here + 1, "mastery_streak": 0}
    )  # E-40
    floor = tempo_floor(target)
    if state.mode is Mode.working:
        if state.tempo > floor:  # E-41
            return state.model_copy(
                update={"tempo": max(floor, round4(state.tempo / 2)), "fails_here": 0}
            )
        if entry.break_unit is not None:  # E-42
            return state.model_copy(
                update={
                    "mode": Mode.isolating,
                    "fragment": isolation_fragment(target, entry.break_unit),
                    "fails_here": 0,
                }
            )
        return _start_chain(state, state.fragment)  # E-43
    if state.mode is Mode.isolating:
        if state.fails_here >= ISOLATING_FAILS_BEFORE_CHAIN:  # E-44
            return _start_chain(state, state.fragment)
        return state
    return state  # chaining: E-45 reissue


def apply(
    state: TargetState,
    target: Target,
    level: Level,
    prescription: Prescription,
    entry: LogEntry,
) -> TargetState:
    """Validate the entry (E-21, E-47, E-61), judge it (E-20), and return the
    next state (E-30 to E-46). Raises EngineError on rejection; never mutates
    the input state.
    """
    _validate(state, prescription, entry)
    expected = prescription.model_copy(update={"threshold": threshold(level, target)})
    if is_pass(entry, expected):
        return _on_pass(state, target, entry)
    return _on_fail(state, target, entry)
