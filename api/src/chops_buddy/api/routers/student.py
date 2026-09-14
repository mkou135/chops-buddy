import uuid

from fastapi import APIRouter, HTTPException, status

from chops_buddy.api import schemas, services
from chops_buddy.api.auth import SessionDep, StudentProfileDep
from chops_buddy.db.models import PracticeSession
from chops_buddy.engine.models import TargetState

router = APIRouter(prefix="/me", tags=["student"])


@router.get("/targets")
async def my_targets(profile: StudentProfileDep, session: SessionDep) -> list[schemas.TargetOut]:
    student = await services.own_student_record(session, profile)
    return [services.target_out(t) for t in await services.active_targets(session, student.id)]


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    body: schemas.SessionCreate, profile: StudentProfileDep, session: SessionDep
) -> schemas.SessionOut:
    student = await services.own_student_record(session, profile)
    row = await services.next_session(session, student, body.duration_minutes)
    return await services.session_out(session, row)


@router.get("/sessions/{session_id}")
async def get_session_by_id(
    session_id: uuid.UUID, profile: StudentProfileDep, session: SessionDep
) -> schemas.SessionOut:
    student = await services.own_student_record(session, profile)
    row = await session.get(PracticeSession, session_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session_not_found")
    if row.student_id != student.id:
        raise services.forbidden()
    return await services.session_out(session, row)


@router.post("/logs", status_code=status.HTTP_201_CREATED)
async def submit_log(
    body: schemas.LogCreate, profile: StudentProfileDep, session: SessionDep
) -> schemas.LogOut:
    student = await services.own_student_record(session, profile)
    log = await services.submit_log(session, student, body)
    return schemas.LogOut(
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


@router.get("/history")
async def my_history(profile: StudentProfileDep, session: SessionDep) -> list[schemas.SessionOut]:
    student = await services.own_student_record(session, profile)
    return await services.history(session, student.id)
