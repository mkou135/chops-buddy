"""Test helpers for the state machine: build the prescription a state implies."""

from chops_buddy.engine.models import Level, Prescription, Target, TargetState
from chops_buddy.engine.params import threshold


def prescription_for(
    state: TargetState, target: Target, level: Level, pid: str = "p"
) -> Prescription:
    return Prescription(
        id=pid,
        target_id=target.id,
        mode=state.mode,
        fragment=state.fragment,
        tempo=state.tempo,
        threshold=threshold(level, target),
        minutes=5,
        instruction="",
    )
