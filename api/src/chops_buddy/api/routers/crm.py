import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from chops_buddy.api import crm, schemas
from chops_buddy.api.auth import SessionDep, TeacherDep

router = APIRouter(prefix="/teacher", tags=["crm"])


# --- schools


@router.post("/schools", status_code=status.HTTP_201_CREATED)
async def create_school(
    body: schemas.SchoolCreate, teacher: TeacherDep, session: SessionDep
) -> schemas.SchoolOut:
    return schemas.SchoolOut.model_validate(await crm.create_school(session, teacher, body))


@router.get("/schools")
async def list_schools(teacher: TeacherDep, session: SessionDep) -> list[schemas.SchoolOut]:
    return [schemas.SchoolOut.model_validate(s) for s in await crm.my_schools(session, teacher)]


@router.post("/schools/{school_id}/join", status_code=status.HTTP_204_NO_CONTENT)
async def join_school(school_id: uuid.UUID, teacher: TeacherDep, session: SessionDep) -> Response:
    await crm.join_school(session, teacher, school_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/schools/{school_id}/students")
async def school_students(
    school_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> list[schemas.StudentOut]:
    return [
        schemas.StudentOut.model_validate(s)
        for s in await crm.school_students(session, teacher, school_id)
    ]


# --- terms


@router.post("/schools/{school_id}/terms", status_code=status.HTTP_201_CREATED)
async def create_term(
    school_id: uuid.UUID, body: schemas.TermCreate, teacher: TeacherDep, session: SessionDep
) -> schemas.TermOut:
    return schemas.TermOut.model_validate(await crm.create_term(session, teacher, school_id, body))


@router.get("/schools/{school_id}/terms")
async def list_terms(
    school_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> list[schemas.TermOut]:
    return [
        schemas.TermOut.model_validate(t) for t in await crm.list_terms(session, teacher, school_id)
    ]


# --- students (update) and lessons


@router.patch("/students/{student_id}")
async def update_student(
    student_id: uuid.UUID, body: schemas.StudentUpdate, teacher: TeacherDep, session: SessionDep
) -> schemas.StudentOut:
    return schemas.StudentOut.model_validate(
        await crm.update_student(session, teacher, student_id, body)
    )


@router.post("/students/{student_id}/lessons", status_code=status.HTTP_201_CREATED)
async def create_lesson(
    student_id: uuid.UUID, body: schemas.LessonCreate, teacher: TeacherDep, session: SessionDep
) -> schemas.LessonOut:
    return await crm.create_lesson(session, teacher, student_id, body)


@router.get("/students/{student_id}/lessons")
async def student_lessons(
    student_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> list[schemas.LessonOut]:
    return await crm.student_lessons(session, teacher, student_id)


@router.get("/lessons")
async def teacher_schedule(
    teacher: TeacherDep,
    session: SessionDep,
    from_: Annotated[date, Query(alias="from")],
    to: Annotated[date, Query()],
) -> list[schemas.LessonOut]:
    return await crm.teacher_schedule(session, teacher, from_, to)


@router.patch("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: uuid.UUID, body: schemas.LessonUpdate, teacher: TeacherDep, session: SessionDep
) -> schemas.LessonOut:
    return await crm.update_lesson(session, teacher, lesson_id, body)


@router.put("/lessons/{lesson_id}/attendance")
async def set_attendance(
    lesson_id: uuid.UUID, body: schemas.AttendanceIn, teacher: TeacherDep, session: SessionDep
) -> schemas.LessonOut:
    return await crm.set_attendance(session, teacher, lesson_id, body)


# --- contacts


@router.post("/students/{student_id}/contacts", status_code=status.HTTP_201_CREATED)
async def create_contact(
    student_id: uuid.UUID, body: schemas.ContactCreate, teacher: TeacherDep, session: SessionDep
) -> schemas.ContactOut:
    return crm.contact_out(await crm.create_contact(session, teacher, student_id, body))


@router.get("/students/{student_id}/contacts")
async def list_contacts(
    student_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> list[schemas.ContactOut]:
    return [crm.contact_out(c) for c in await crm.list_contacts(session, teacher, student_id)]


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: uuid.UUID, teacher: TeacherDep, session: SessionDep
) -> Response:
    await crm.delete_contact(session, teacher, contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
