"""DoD Data: seed script produces one school, two teachers, six students, assignments,
and 30 days of logs, in under 30 seconds (A10). Deterministic and idempotent."""

import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from chops_buddy.db.models import LogEntry, PracticeSession, Profile, School, Student, Target
from chops_buddy.seed import DEMO_SCHOOL_NAME, seed


async def count(session: AsyncSession, model: type) -> int:  # type: ignore[type-arg]
    return int((await session.execute(select(func.count()).select_from(model))).scalar_one())


async def test_seed_creates_the_demo_dataset_quickly(session: AsyncSession) -> None:
    started = time.monotonic()
    summary = await seed(session, days=30)
    elapsed = time.monotonic() - started
    assert elapsed < 30, f"seed took {elapsed:.1f}s"

    assert await count(session, School) == 1
    school = (await session.execute(select(School))).scalar_one()
    assert school.name == DEMO_SCHOOL_NAME
    assert await count(session, Profile) == 2 + 6  # teachers + student profiles
    assert await count(session, Student) == 6
    assert await count(session, Target) >= 12  # at least two per student
    assert await count(session, PracticeSession) >= 6 * 10  # most days practised
    assert await count(session, LogEntry) >= 6 * 10
    assert summary["students"] == 6 and summary["days"] == 30

    # Progress happened: at least one target moved off its initial tempo or mode.
    rows = (await session.execute(select(Target))).scalars().all()
    moved = [
        t
        for t in rows
        if t.state_row and (t.state_row.state["fails_here"] or t.state_row.version > 1)
    ]
    assert moved, "no target state advanced"


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    await seed(session, days=3)
    await seed(session, days=3)
    assert await count(session, School) == 1
    assert await count(session, Student) == 6
