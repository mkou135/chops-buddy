"""Shared fixtures for engine tests.

The walkthrough target from docs/ENGINE_SPEC.md §4.5: 8 units, target tempo 120,
intermediate (threshold 5). Derived: rung 12, floor 60, start 72.
"""

import pytest

from chops_buddy.engine.models import (
    InstrumentFamily,
    Level,
    LogEntry,
    Student,
    Target,
    TargetKind,
)


@pytest.fixture
def intermediate_wind_student() -> Student:
    return Student(level=Level.intermediate, instrument_family=InstrumentFamily.wind)


@pytest.fixture
def walkthrough_target() -> Target:
    return Target(
        id="t1",
        kind=TargetKind.repertoire,
        title="Minuet, bars 1-8",
        target_tempo=120,
        units=[f"b{i}" for i in range(1, 9)],
    )


def entry(
    prescription_id: str,
    *,
    tempo_used: int,
    best: int,
    break_unit: int | None = None,
    difficulty: int = 3,
) -> LogEntry:
    """Terse constructor for log entries in tests."""
    return LogEntry(
        prescription_id=prescription_id,
        tempo_used=tempo_used,
        best_consecutive=best,
        break_unit=break_unit,
        felt_difficulty=difficulty,
    )
