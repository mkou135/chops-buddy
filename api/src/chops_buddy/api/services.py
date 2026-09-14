"""Write paths from docs/DATA_MODEL.md §4. The only place the API calls the engine."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chops_buddy.api import schemas
from chops_buddy.db.models import (
    LogEntry,
    PracticeSession,
    Prescription,
    Profile,
    Student,
    Target,
    TargetStateRow,
)
from chops_buddy.engine import compose as engine_compose
from chops_buddy.engine import state as engine_state
from chops_buddy.engine.models import EngineError, TargetState
from chops_buddy.engine.models import LogEntry as EngineLogEntry
from chops_buddy.engine.models import Prescription as EnginePrescription
from chops_buddy.engine.models import Student as EngineStudent
from chops_buddy.llm.proposer import (
    AnthropicProposer,
    ProposalRequest,
    Proposer,
    propose_session,
)
from chops_buddy.settings import settings


def forbidden(detail: str = "forbidden") -> HTTPException:
    return HTTPException(status.HTTP_403_FORBIDDEN, detail=detail)


def engine_error(exc: EngineError) -> HTTPException:
    code = status.HTTP_409_CONFLICT if exc.code == "nothing_to_practise" else 422
    return HTTPException(code, detail=exc.code)


# --- lookups with authorisation -------------------------------------------------


async def owned_student(session: AsyncSession, teacher: Profile, student_id: uuid.UUID) -> Student:
    student = await session.get(Student, student_id)
    if student is None or student.teacher_id != teacher.id:
        raise forbidden()
    return student


async def own_student_record(session: AsyncSession, profile: Profile) -> Student:
    result = await session.execute(select(Student).where(Student.profile_id == profile.id))
    student = result.scalar_one_or_none()
    if student is None:
        raise forbidden("student_not_linked")
    return student


async def active_targets(session: AsyncSession, student_id: uuid.UUID) -> list[Target]:
    result = await session.execute(
        select(Target)
        .where(Target.student_id == student_id, Target.is_active.is_(True))
        .order_by(Target.position, Target.created_at)
    )
    return list(result.scalars())


def target_out(target: Target) -> schemas.TargetOut:
    assert target.state_row is not None
    return schemas.TargetOut(
        id=target.id,
        kind=target.kind,
        title=target.title,
        target_tempo=target.target_tempo,
        units=list(target.units),
        phrases=[(p[0], p[1]) for p in target.phrases] if target.phrases else None,
        start_tempo=target.start_tempo,
        threshold_override=target.threshold_override,
        position=target.position,
        is_active=target.is_active,
        state=TargetState.model_validate(target.state_row.state),
    )


# --- write paths ------------------------------------------------------------------


async def assign_target(
    session: AsyncSession, teacher: Profile, student: Student, body: schemas.TargetCreate
) -> Target:
    existing = await active_targets(session, student.id)
    target = Target(
        student_id=student.id,
        kind=body.kind,
        title=body.title,
        target_tempo=body.target_tempo,
        units=body.units,
        phrases=[list(p) for p in body.phrases] if body.phrases else None,
        start_tempo=body.start_tempo,
        threshold_override=body.threshold_override,
        position=len(existing),
        created_by=teacher.id,
    )
    session.add(target)
    await session.flush()
    initial = engine_state.initial_state(target.to_engine())
    target.state_row = TargetStateRow(state=initial.model_dump())
    await session.flush()
    return target


def make_proposer() -> Proposer | None:
    """The model client, or None when no key is configured (DoD A4). Patched in tests."""
    if not settings.llm_api_key:
        return None
    return AnthropicProposer(settings.llm_api_key, settings.llm_model)


async def _recent_logs(
    session: AsyncSession, student_id: uuid.UUID, limit: int = 12
) -> list[dict[str, Any]]:
    rows = await session.execute(
        select(LogEntry, Prescription.target_id)
        .join(Prescription, Prescription.id == LogEntry.prescription_id)
        .where(LogEntry.student_id == student_id)
        .order_by(LogEntry.created_at.desc())
        .limit(limit)
    )
    out: list[dict[str, Any]] = []
    for log, target_id in rows.all():
        out.append(
            {
                "target_id": str(target_id),
                "tempo_used": log.tempo_used,
                "best_consecutive": log.best_consecutive,
                "break_unit": log.break_unit,
                "felt_difficulty": log.felt_difficulty,
                "free_text": log.free_text,
                "logged_at": log.created_at.isoformat(),
            }
        )
    return list(reversed(out))


async def next_session(
    session: AsyncSession, student: Student, duration_minutes: int
) -> PracticeSession:
    targets = await active_targets(session, student.id)
    pairs = [
        (t.to_engine(), TargetState.model_validate(t.state_row.state))
        for t in targets
        if t.state_row is not None
    ]
    engine_student = EngineStudent(level=student.level, instrument_family=student.instrument_family)

    def mint(target_id: str) -> str:
        return str(uuid.uuid4())

    proposer = make_proposer()
    llm_report: dict[str, Any] | None = None
    try:
        if proposer is None:
            plan = engine_compose.compose(engine_student, pairs, duration_minutes, mint)
            source = "engine"
        else:
            request = ProposalRequest(
                student=engine_student,
                targets=pairs,
                duration_minutes=duration_minutes,
                recent_logs=await _recent_logs(session, student.id),
            )
            outcome = await propose_session(request, proposer, mint)
            plan, source = outcome.plan, outcome.source
            llm_report = {
                "violations": outcome.report.violations,
                "repaired": outcome.report.repaired,
                "coaching_note": outcome.report.coaching_note,
            }
    except EngineError as exc:
        raise engine_error(exc) from exc

    row = PracticeSession(
        student_id=student.id,
        duration_minutes=duration_minutes,
        plan=plan.model_dump(mode="json"),
        plan_hash=plan.plan_hash,
        source=source,
        llm_report=llm_report,
    )
    for position, segment in enumerate(plan.segments):
        if segment.prescription is None:
            continue
        row.prescriptions.append(
            Prescription(
                id=uuid.UUID(segment.prescription.id),
                target_id=uuid.UUID(segment.prescription.target_id),
                position=position,
                snapshot=segment.prescription.model_dump(mode="json"),
            )
        )
    session.add(row)
    await session.flush()
    return row


async def submit_log(session: AsyncSession, student: Student, body: schemas.LogCreate) -> LogEntry:
    prescription = await session.get(
        Prescription, body.prescription_id, options=[selectinload(Prescription.session)]
    )
    if prescription is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="prescription_not_found")
    if prescription.session.student_id != student.id:
        raise forbidden()
    already = await session.execute(
        select(LogEntry.id).where(LogEntry.prescription_id == prescription.id)
    )
    if already.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="already_logged")

    target = await session.get(Target, prescription.target_id)
    assert target is not None and target.state_row is not None
    before = TargetState.model_validate(target.state_row.state)
    entry = EngineLogEntry(
        prescription_id=str(prescription.id),
        tempo_used=body.tempo_used,
        best_consecutive=body.best_consecutive,
        break_unit=body.break_unit,
        felt_difficulty=body.felt_difficulty,
        free_text=body.free_text,
    )
    try:
        after = engine_state.apply(
            before,
            target.to_engine(),
            student.level,
            EnginePrescription.model_validate(prescription.snapshot),
            entry,
        )
    except EngineError as exc:
        raise engine_error(exc) from exc

    target.state_row.state = after.model_dump()
    target.state_row.version += 1
    log = LogEntry(
        prescription_id=prescription.id,
        student_id=student.id,
        tempo_used=body.tempo_used,
        best_consecutive=body.best_consecutive,
        break_unit=body.break_unit,
        felt_difficulty=body.felt_difficulty,
        free_text=body.free_text,
        state_after=after.model_dump(),
    )
    session.add(log)
    await session.flush()
    await _mark_completed_if_done(session, prescription.session)
    return log


async def _mark_completed_if_done(session: AsyncSession, practice: PracticeSession) -> None:
    logged = await session.execute(
        select(LogEntry.prescription_id)
        .join(Prescription, Prescription.id == LogEntry.prescription_id)
        .where(Prescription.session_id == practice.id)
    )
    total = await session.execute(
        select(Prescription.id).where(Prescription.session_id == practice.id)
    )
    if len(logged.all()) == len(total.all()):
        practice.completed_at = datetime.now(UTC)
        await session.flush()


# --- reads --------------------------------------------------------------------------


async def session_out(session: AsyncSession, row: PracticeSession) -> schemas.SessionOut:
    logs = await session.execute(
        select(LogEntry)
        .join(Prescription, Prescription.id == LogEntry.prescription_id)
        .where(Prescription.session_id == row.id)
        .order_by(Prescription.position)
    )
    return schemas.SessionOut(
        id=row.id,
        student_id=row.student_id,
        duration_minutes=row.duration_minutes,
        source=row.source,
        plan=schemas.plan_from_row(row.plan),
        created_at=row.created_at,
        completed_at=row.completed_at,
        llm_report=row.llm_report,
        logs=[
            schemas.LogOut(
                id=log.id,
                prescription_id=log.prescription_id,
                tempo_used=log.tempo_used,
                best_consecutive=log.best_consecutive,
                break_unit=log.break_unit,
                felt_difficulty=log.felt_difficulty,
                free_text=log.free_text,
                state_after=TargetState.model_validate(log.state_after),
                created_at=log.created_at,
            )
            for log in logs.scalars()
        ],
    )


async def history(session: AsyncSession, student_id: uuid.UUID) -> list[schemas.SessionOut]:
    rows = await session.execute(
        select(PracticeSession)
        .where(PracticeSession.student_id == student_id)
        .order_by(PracticeSession.created_at.desc())
    )
    return [await session_out(session, row) for row in rows.scalars()]
