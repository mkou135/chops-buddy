"""Per-target state machine. docs/ENGINE_SPEC.md §4 (E-20 to E-47, E-60 to E-63).

Scaffold: signatures only. `apply` is the single entry point; it must be a
pure function of (state, target, level, prescription, entry).
"""

from chops_buddy.engine.models import (
    Level,
    LogEntry,
    Prescription,
    Target,
    TargetState,
)


def initial_state(target: Target) -> TargetState:
    """§4.1 initial state."""
    raise NotImplementedError("§4.1")


def is_pass(entry: LogEntry, prescription: Prescription) -> bool:
    """E-20."""
    raise NotImplementedError("E-20")


def apply(
    state: TargetState,
    target: Target,
    level: Level,
    prescription: Prescription,
    entry: LogEntry,
) -> TargetState:
    """Validate the entry (E-21, E-60, E-61), judge it (E-20), and return the
    next state (E-30 to E-47). Raises EngineError on rejection; never mutates
    the input state.
    """
    raise NotImplementedError("§4.3/§4.4")
