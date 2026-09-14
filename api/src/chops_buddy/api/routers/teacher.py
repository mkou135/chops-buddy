import uuid

from fastapi import APIRouter, Response, status
from sqlalchemy import select

from chops_buddy.api import crm, schemas, services
from chops_buddy.api.auth import SessionDep, TeacherDep
from chops_buddy.db.models import Student, Target

router = APIRouter(prefix="/teacher", tags=["teacher"])


@router.post("/students", status_code=status.HTTP_201_CREATED)
async def create_student(
    body: schemas.StudentCreate, teacher: TeacherDep, session: SessionDep
) -> schemas.StudentOut:
    await crm.assert_can_place_in_school(session, teacher, body.school_id)
    student = Student(
        teacher_id=teacher.id,
        school_id=body.school_id,
        display_name=body.display_name,
        level=body.level,
        instrument_family=body.instrument_family,
    )
    session.add(student)
    await session.flush()
    return schemas.StudentOut.model_validate(student)


@router.get("/students")
async def list_students(teacher: TeacherDep, session: SessionDep) -> list[schemas.StudentOut]:
    rows = await session.execute(
        select(Student).where(Student.teacher_id == teacher.id).order_by(Student.display_name)
    )
    return [schemas.StudentOut.model_validate(s) for s in rows.scalars()]


@router.get("/students/{student_id}")
async def get_student(
    student_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> schemas.StudentDetail:
    student = await services.owned_student(session, teacher, student_id)
    targets = await services.active_targets(session, student.id)
    base = schemas.StudentOut.model_validate(student)
    return schemas.StudentDetail(
        **base.model_dump(), targets=[services.target_out(t) for t in targets]
    )


@router.post("/students/{student_id}/targets", status_code=status.HTTP_201_CREATED)
async def assign_target(
    student_id: uuid.UUID, body: schemas.TargetCreate, teacher: TeacherDep, session: SessionDep
) -> schemas.TargetOut:
    student = await services.owned_student(session, teacher, student_id)
    target = await services.assign_target(session, teacher, student, body)
    return services.target_out(target)


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_target(
    target_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> Response:
    target = await session.get(Target, target_id)
    if target is None:
        raise services.forbidden()
    await services.owned_student(session, teacher, target.student_id)
    target.is_active = False
    await session.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/students/{student_id}/history")
async def student_history(
    student_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> list[schemas.SessionOut]:
    student = await services.owned_student(session, teacher, student_id)
    return await services.history(session, student.id)
