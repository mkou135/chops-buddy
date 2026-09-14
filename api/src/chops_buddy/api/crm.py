"""CRM services (M6): schools, membership, terms, lessons, attendance, contacts.

Authorisation model (DECISIONS #29): school membership grants read of that school's
roster; ownership (students.teacher_id) gates everything else.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from chops_buddy.api import schemas
from chops_buddy.api.services import forbidden, owned_student
from chops_buddy.db.models import (
    Attendance,
    Contact,
    Lesson,
    Profile,
    School,
    SchoolMembership,
    Student,
    Term,
)


def not_found(what: str) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{what}_not_found")


# --- schools -----------------------------------------------------------------------------


async def is_member(session: AsyncSession, teacher: Profile, school_id: uuid.UUID) -> bool:
    row = await session.get(SchoolMembership, (teacher.id, school_id))
    return row is not None


async def member_school(session: AsyncSession, teacher: Profile, school_id: uuid.UUID) -> School:
    school = await session.get(School, school_id)
    if school is None or not await is_member(session, teacher, school_id):
        raise forbidden()
    return school


async def create_school(
    session: AsyncSession, teacher: Profile, body: schemas.SchoolCreate
) -> School:
    school = School(name=body.name, suburb=body.suburb)
    session.add(school)
    await session.flush()
    session.add(SchoolMembership(teacher_id=teacher.id, school_id=school.id))
    await session.flush()
    return school


async def my_schools(session: AsyncSession, teacher: Profile) -> list[School]:
    rows = await session.execute(
        select(School)
        .join(SchoolMembership, SchoolMembership.school_id == School.id)
        .where(SchoolMembership.teacher_id == teacher.id)
        .order_by(School.name)
    )
    return list(rows.scalars())


async def join_school(session: AsyncSession, teacher: Profile, school_id: uuid.UUID) -> None:
    if await session.get(School, school_id) is None:
        raise not_found("school")
    if not await is_member(session, teacher, school_id):
        session.add(SchoolMembership(teacher_id=teacher.id, school_id=school_id))
        await session.flush()


async def school_students(
    session: AsyncSession, teacher: Profile, school_id: uuid.UUID
) -> list[Student]:
    await member_school(session, teacher, school_id)
    rows = await session.execute(
        select(Student)
        .where(Student.school_id == school_id, Student.is_active.is_(True))
        .order_by(Student.display_name)
    )
    return list(rows.scalars())


async def assert_can_place_in_school(
    session: AsyncSession, teacher: Profile, school_id: uuid.UUID | None
) -> None:
    if school_id is not None and not await is_member(session, teacher, school_id):
        raise forbidden("not_a_member_of_school")


async def update_student(
    session: AsyncSession, teacher: Profile, student_id: uuid.UUID, body: schemas.StudentUpdate
) -> Student:
    student = await owned_student(session, teacher, student_id)
    if "school_id" in body.model_fields_set:
        await assert_can_place_in_school(session, teacher, body.school_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    await session.flush()
    return student


# --- terms -------------------------------------------------------------------------------


async def create_term(
    session: AsyncSession, teacher: Profile, school_id: uuid.UUID, body: schemas.TermCreate
) -> Term:
    await member_school(session, teacher, school_id)
    if body.starts_on >= body.ends_on:
        raise HTTPException(422, detail="term_dates_not_ordered")
    term = Term(school_id=school_id, name=body.name, starts_on=body.starts_on, ends_on=body.ends_on)
    session.add(term)
    await session.flush()
    return term


async def list_terms(session: AsyncSession, teacher: Profile, school_id: uuid.UUID) -> list[Term]:
    await member_school(session, teacher, school_id)
    rows = await session.execute(
        select(Term).where(Term.school_id == school_id).order_by(Term.starts_on)
    )
    return list(rows.scalars())


# --- lessons -----------------------------------------------------------------------------


def lesson_out(lesson: Lesson, student_name: str) -> schemas.LessonOut:
    att = lesson.attendance
    return schemas.LessonOut(
        id=lesson.id,
        student_id=lesson.student_id,
        student_display_name=student_name,
        term_id=lesson.term_id,
        scheduled_at=lesson.scheduled_at,
        duration_minutes=lesson.duration_minutes,
        status=lesson.status,
        notes=lesson.notes,
        attendance=schemas.AttendanceIn(status=att.status, note=att.note) if att else None,  # type: ignore[arg-type]
    )


async def _check_term(
    session: AsyncSession, student: Student, term_id: uuid.UUID | None, on: date
) -> None:
    if term_id is None:
        return
    term = await session.get(Term, term_id)
    if term is None or term.school_id != student.school_id:
        raise HTTPException(422, detail="term_not_in_students_school")
    if not term.starts_on <= on <= term.ends_on:
        raise HTTPException(422, detail="lesson_outside_term")


async def create_lesson(
    session: AsyncSession, teacher: Profile, student_id: uuid.UUID, body: schemas.LessonCreate
) -> schemas.LessonOut:
    student = await owned_student(session, teacher, student_id)
    await _check_term(session, student, body.term_id, body.scheduled_at.date())
    lesson = Lesson(
        student_id=student.id,
        teacher_id=teacher.id,
        term_id=body.term_id,
        scheduled_at=body.scheduled_at,
        duration_minutes=body.duration_minutes,
        status="scheduled",
        notes=body.notes,
        attendance=None,  # set explicitly so no lazy load runs on the fresh row
    )
    session.add(lesson)
    await session.flush()
    return lesson_out(lesson, student.display_name)


async def owned_lesson(
    session: AsyncSession, teacher: Profile, lesson_id: uuid.UUID
) -> tuple[Lesson, Student]:
    lesson = await session.get(Lesson, lesson_id)
    if lesson is None:
        raise not_found("lesson")
    student = await session.get(Student, lesson.student_id)
    if student is None or student.teacher_id != teacher.id:
        raise forbidden()
    return lesson, student


async def update_lesson(
    session: AsyncSession, teacher: Profile, lesson_id: uuid.UUID, body: schemas.LessonUpdate
) -> schemas.LessonOut:
    lesson, student = await owned_lesson(session, teacher, lesson_id)
    changes = body.model_dump(exclude_unset=True)
    when = changes.get("scheduled_at", lesson.scheduled_at)
    await _check_term(session, student, lesson.term_id, when.date())
    for field, value in changes.items():
        setattr(lesson, field, value)
    await session.flush()
    return lesson_out(lesson, student.display_name)


async def set_attendance(
    session: AsyncSession, teacher: Profile, lesson_id: uuid.UUID, body: schemas.AttendanceIn
) -> schemas.LessonOut:
    lesson, student = await owned_lesson(session, teacher, lesson_id)
    if lesson.attendance is None:
        lesson.attendance = Attendance(status=body.status, note=body.note)
    else:
        lesson.attendance.status = body.status
        lesson.attendance.note = body.note
    await session.flush()
    return lesson_out(lesson, student.display_name)


async def student_lessons(
    session: AsyncSession, teacher: Profile, student_id: uuid.UUID
) -> list[schemas.LessonOut]:
    student = await owned_student(session, teacher, student_id)
    rows = await session.execute(
        select(Lesson).where(Lesson.student_id == student.id).order_by(Lesson.scheduled_at.desc())
    )
    return [lesson_out(lesson, student.display_name) for lesson in rows.scalars()]


async def teacher_schedule(
    session: AsyncSession, teacher: Profile, from_: date, to: date
) -> list[schemas.LessonOut]:
    rows = await session.execute(
        select(Lesson, Student.display_name)
        .join(Student, Student.id == Lesson.student_id)
        .where(
            Lesson.teacher_id == teacher.id,
            # Inclusive calendar range, generous at both ends so any timezone's day is covered.
            Lesson.scheduled_at
            >= datetime.combine(from_, time.min, tzinfo=UTC) - timedelta(hours=14),
            Lesson.scheduled_at
            < datetime.combine(to + timedelta(days=1), time.min, tzinfo=UTC) + timedelta(hours=12),
        )
        .order_by(Lesson.scheduled_at)
    )
    return [lesson_out(lesson, name) for lesson, name in rows.all()]


# --- contacts ----------------------------------------------------------------------------


def contact_out(c: Contact) -> schemas.ContactOut:
    return schemas.ContactOut(
        id=c.id,
        student_id=c.student_id,
        name=c.name,
        relationship=c.relationship_,
        phone=c.phone,
        email=c.email,
        is_primary=c.is_primary,
    )


async def create_contact(
    session: AsyncSession, teacher: Profile, student_id: uuid.UUID, body: schemas.ContactCreate
) -> Contact:
    student = await owned_student(session, teacher, student_id)
    if body.is_primary:
        await session.execute(
            update(Contact).where(Contact.student_id == student.id).values(is_primary=False)
        )
    contact = Contact(
        student_id=student.id,
        name=body.name,
        relationship_=body.relationship,
        phone=body.phone,
        email=body.email,
        is_primary=body.is_primary,
    )
    session.add(contact)
    await session.flush()
    return contact


async def list_contacts(
    session: AsyncSession, teacher: Profile, student_id: uuid.UUID
) -> list[Contact]:
    student = await owned_student(session, teacher, student_id)
    rows = await session.execute(
        select(Contact)
        .where(Contact.student_id == student.id)
        .order_by(Contact.is_primary.desc(), Contact.name)
    )
    return list(rows.scalars())


async def delete_contact(session: AsyncSession, teacher: Profile, contact_id: uuid.UUID) -> None:
    contact = await session.get(Contact, contact_id)
    if contact is None:
        raise not_found("contact")
    await owned_student(session, teacher, contact.student_id)
    await session.delete(contact)
    await session.flush()
