"""Demo data: one school, two teachers, six students, assignments, and N days of
practice driven through the real engine so the states are genuine.

Deterministic (fixed ids, seeded pseudo-random self-reports) and idempotent: a
second run finds the demo school and does nothing. The teacher and student
profiles use fixed ids that do not exist in Supabase Auth, so nobody can sign in
as them; they exist to make the teacher screens and history worth looking at.

    python -m chops_buddy.seed [--days 30] [--reset]
"""

import argparse
import asyncio
import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from chops_buddy.db.base import SessionFactory
from chops_buddy.db.models import (
    Contact,
    Lesson,
    LogEntry,
    PracticeSession,
    Prescription,
    Profile,
    School,
    SchoolMembership,
    Student,
    Target,
    TargetStateRow,
    Term,
)
from chops_buddy.engine import compose as engine_compose
from chops_buddy.engine import state as engine_state
from chops_buddy.engine.models import EngineError, TargetState
from chops_buddy.engine.models import LogEntry as EngineLogEntry
from chops_buddy.engine.models import Prescription as EnginePrescription
from chops_buddy.engine.models import Student as EngineStudent

DEMO_SCHOOL_NAME = "Demo Conservatorium"
NS = uuid.UUID("6f8f4b7e-2a4e-4e4e-9c1a-0c3a2d1e5f00")


def fixed(name: str) -> uuid.UUID:
    return uuid.uuid5(NS, name)


TEACHERS = [("t1", "Ms Ada Reyes", "ada@example.com"), ("t2", "Mr Sam Okafor", "sam@example.com")]

STUDENTS: list[tuple[str, str, str, str, str]] = [
    # key, teacher, name, level, family
    ("s1", "t1", "Priya N", "beginner", "wind"),
    ("s2", "t1", "Leo K", "intermediate", "brass"),
    ("s3", "t1", "Mia T", "advanced", "wind"),
    ("s4", "t2", "Noah B", "beginner", "keyboard"),
    ("s5", "t2", "Zoe L", "intermediate", "strings"),
    ("s6", "t2", "Ethan W", "intermediate", "voice"),
]

BARS = [f"b{i}" for i in range(1, 9)]
ASSIGNMENTS: dict[str, list[tuple[str, str, int, list[str]]]] = {
    "s1": [
        ("scale", "C major, one octave", 90, ["oct1"]),
        ("repertoire", "Hot Cross Buns", 90, BARS[:4]),
    ],
    "s2": [
        ("scale", "Bb major, two octaves", 100, ["oct1", "oct2"]),
        ("technique", "Lip slurs", 80, ["a", "b", "c", "d"]),
        ("repertoire", "Hymn to Joy", 96, BARS),
    ],
    "s3": [
        ("scale", "Chromatic, full range", 120, ["oct1", "oct2", "oct3"]),
        ("technique", "Altissimo study", 100, BARS[:6]),
        ("repertoire", "Creston Sonata, opening", 132, BARS),
    ],
    "s4": [
        ("scale", "C major hands together", 80, ["asc", "desc"]),
        ("repertoire", "Minuet in G", 96, BARS),
    ],
    "s5": [
        ("scale", "G major, two octaves", 100, ["oct1", "oct2"]),
        ("technique", "Spiccato", 100, ["a", "b", "c", "d"]),
        ("repertoire", "Bach Bourrée", 108, BARS),
    ],
    "s6": [
        ("scale", "Five-note warmup", 80, ["1", "2", "3", "4", "5"]),
        ("repertoire", "Caro mio ben", 66, BARS),
    ],
}


async def _exists(session: AsyncSession) -> School | None:
    return (
        await session.execute(select(School).where(School.name == DEMO_SCHOOL_NAME))
    ).scalar_one_or_none()


async def reset(session: AsyncSession) -> None:
    school = await _exists(session)
    if school is None:
        return
    student_ids = [fixed(k) for k, *_ in STUDENTS]
    await session.execute(delete(Student).where(Student.id.in_(student_ids)))  # cascades
    await session.execute(delete(School).where(School.id == school.id))
    await session.execute(
        delete(Profile).where(
            Profile.id.in_(
                [fixed(k) for k, *_ in TEACHERS] + [fixed(f"p-{k}") for k, *_ in STUDENTS]
            )
        )
    )
    await session.flush()


async def seed(session: AsyncSession, days: int = 30, rng_seed: int = 7) -> dict[str, Any]:
    if await _exists(session) is not None:
        return {"skipped": True, "students": len(STUDENTS), "days": days}
    rng = random.Random(rng_seed)
    now = datetime.now(UTC)

    school = School(id=fixed("school"), name=DEMO_SCHOOL_NAME, suburb="Brunswick")
    session.add(school)
    for key, name, email in TEACHERS:
        session.add(Profile(id=fixed(key), role="teacher", display_name=name, email=email))
    await session.flush()
    for key, *_ in TEACHERS:
        session.add(SchoolMembership(teacher_id=fixed(key), school_id=school.id))
    term = Term(
        id=fixed("term"),
        school_id=school.id,
        name="Term 4",
        starts_on=(now - timedelta(days=days)).date(),
        ends_on=(now + timedelta(days=60)).date(),
    )
    session.add(term)

    students: list[Student] = []
    for key, tkey, name, level, family in STUDENTS:
        session.add(
            Profile(
                id=fixed(f"p-{key}"), role="student", display_name=name, email=f"{key}@example.com"
            )
        )
        await session.flush()
        st = Student(
            id=fixed(key),
            teacher_id=fixed(tkey),
            school_id=school.id,
            profile_id=fixed(f"p-{key}"),
            display_name=name,
            level=level,
            instrument_family=family,
        )  # type: ignore[arg-type]
        session.add(st)
        students.append(st)
        await session.flush()  # contacts reference the student by id, not by relationship
        session.add(
            Contact(
                student_id=st.id,
                name=f"Parent of {name.split()[0]}",
                relationship_="parent",
                phone="0400 000 000",
                email=f"parent-{key}@example.com",
                is_primary=True,
            )
        )
    await session.flush()

    for st in students:
        key = next(k for k, *_ in STUDENTS if fixed(k) == st.id)
        for position, (kind, title, tempo, units) in enumerate(ASSIGNMENTS[key]):
            t = Target(
                id=fixed(f"{key}-{position}"),
                student_id=st.id,
                kind=kind,
                title=title,
                target_tempo=tempo,
                units=units,
                position=position,
                created_by=st.teacher_id,
            )  # type: ignore[arg-type]
            session.add(t)
            await session.flush()
            t.state_row = TargetStateRow(
                state=engine_state.initial_state(t.to_engine()).model_dump()
            )
        # a weekly lesson through the window
        for week in range(days // 7):
            when = now - timedelta(days=days - 7 * week - 1)
            session.add(
                Lesson(
                    student_id=st.id,
                    teacher_id=st.teacher_id,
                    term_id=term.id,
                    scheduled_at=when,
                    duration_minutes=30,
                    status="completed",
                    notes=f"Week {week + 1}: worked {ASSIGNMENTS[key][-1][1]}.",
                    attendance=None,
                )
            )
    await session.flush()

    sessions = 0
    logs = 0
    for day in range(days, 0, -1):
        when = now - timedelta(days=day)
        for st in students:
            if rng.random() < 0.3:  # about 70% of days practised
                continue
            targets = (
                (
                    await session.execute(
                        select(Target)
                        .where(Target.student_id == st.id, Target.is_active.is_(True))
                        .order_by(Target.position)
                    )
                )
                .scalars()
                .all()
            )
            pairs = [
                (t.to_engine(), TargetState.model_validate(t.state_row.state))
                for t in targets
                if t.state_row
            ]
            estudent = EngineStudent(level=st.level, instrument_family=st.instrument_family)
            duration = rng.choice([10, 20, 30])
            try:
                plan = engine_compose.compose(
                    estudent, pairs, duration, lambda _tid: str(uuid.uuid4())
                )
            except EngineError:
                continue
            row = PracticeSession(
                student_id=st.id,
                duration_minutes=duration,
                plan=plan.model_dump(mode="json"),
                plan_hash=plan.plan_hash,
                source="engine",
                created_at=when,
                completed_at=when + timedelta(minutes=duration),
            )
            by_target = {t.id: t for t in targets}
            for pos, seg in enumerate(plan.segments):
                p = seg.prescription
                if p is None:
                    continue
                pres = Prescription(
                    id=uuid.UUID(p.id),
                    target_id=uuid.UUID(p.target_id),
                    position=pos,
                    snapshot=p.model_dump(mode="json"),
                    created_at=when,
                )
                row.prescriptions.append(pres)
            session.add(row)
            await session.flush()
            sessions += 1
            for pres in row.prescriptions:
                t = by_target[pres.target_id]
                assert t.state_row is not None
                before = TargetState.model_validate(t.state_row.state)
                ep = EnginePrescription.model_validate(pres.snapshot)
                # Self-report: usually passes, sometimes fails with a break point.
                # Felt difficulty tracks how far below target the tempo is.
                passed = rng.random() < 0.6
                best = (
                    ep.threshold + rng.randint(0, 2) if passed else rng.randint(0, ep.threshold - 1)
                )
                break_unit = None
                if not passed and rng.random() < 0.7:
                    lo, hi = ep.fragment
                    break_unit = rng.randrange(lo, hi)
                difficulty = (
                    2
                    if passed and ep.tempo < t.target_tempo
                    else (3 if passed else 4 + int(rng.random() < 0.4))
                )
                entry = EngineLogEntry(
                    prescription_id=str(pres.id),
                    tempo_used=ep.tempo,
                    best_consecutive=min(best, 50),
                    break_unit=break_unit,
                    felt_difficulty=min(difficulty, 5),
                    free_text=rng.choice(
                        [
                            None,
                            None,
                            "felt ok",
                            "kept slipping at the end",
                            "reed was soft today",
                            "easier than yesterday",
                        ]
                    ),
                )
                try:
                    after = engine_state.apply(before, t.to_engine(), st.level, ep, entry)  # type: ignore[arg-type]
                except EngineError:
                    continue
                t.state_row.state = after.model_dump()
                t.state_row.version += 1
                session.add(
                    LogEntry(
                        prescription_id=pres.id,
                        student_id=st.id,
                        tempo_used=entry.tempo_used,
                        best_consecutive=entry.best_consecutive,
                        break_unit=entry.break_unit,
                        felt_difficulty=entry.felt_difficulty,
                        free_text=entry.free_text,
                        state_after=after.model_dump(),
                        created_at=when + timedelta(minutes=duration),
                    )
                )
                logs += 1
            await session.flush()
    return {
        "skipped": False,
        "students": len(STUDENTS),
        "days": days,
        "sessions": sessions,
        "logs": logs,
    }


async def _main(days: int, do_reset: bool) -> None:
    async with SessionFactory() as session:
        if do_reset:
            await reset(session)
        summary = await seed(session, days=days)
        await session.commit()
    print(summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--reset", action="store_true", help="delete the demo data first")
    args = parser.parse_args()
    asyncio.run(_main(args.days, args.reset))
