"""ORM round-trips, including engine shapes stored as JSONB (DECISIONS #16)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chops_buddy.db.models import Profile, Student, Target, TargetStateRow
from chops_buddy.engine.models import InstrumentFamily, Level, Mode, TargetKind, TargetState
from chops_buddy.engine.models import Target as EngineTarget
from chops_buddy.engine.state import initial_state


async def test_target_state_round_trips_through_jsonb(session: AsyncSession) -> None:
    teacher = Profile(id=uuid.uuid4(), role="teacher", display_name="T", email="t@x.io")
    student = Student(
        teacher_id=teacher.id,
        display_name="S",
        level=Level.intermediate,
        instrument_family=InstrumentFamily.wind,
    )
    target = Target(
        student=student,
        kind=TargetKind.repertoire,
        title="Minuet",
        target_tempo=120,
        units=[f"b{i}" for i in range(1, 9)],
        position=0,
        created_by=teacher.id,
    )
    state = initial_state(target.to_engine())
    target.state_row = TargetStateRow(state=state.model_dump())
    session.add_all([teacher, student, target])
    await session.flush()
    session.expunge_all()

    loaded = (await session.execute(select(Target).where(Target.id == target.id))).scalar_one()
    assert loaded.state_row is not None
    restored = TargetState.model_validate(loaded.state_row.state)
    assert restored == state
    assert restored.mode is Mode.working and restored.tempo == 72
    assert loaded.to_engine() == EngineTarget(
        id=str(target.id),
        kind=TargetKind.repertoire,
        title="Minuet",
        target_tempo=120,
        units=[f"b{i}" for i in range(1, 9)],
    )
