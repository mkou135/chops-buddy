"""M6 CRM: schools, membership, terms, lessons, attendance, contacts (DoD A14, A9)."""

import uuid

from httpx import AsyncClient

from chops_buddy.db.models import Profile, Student
from tests.api.conftest import bearer


async def make_school(
    client: AsyncClient, teacher: Profile, name: str = "Northside Primary"
) -> str:
    r = await client.post(
        "/teacher/schools", json={"name": name, "suburb": "Brunswick"}, headers=bearer(teacher.id)
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# --- schools and membership -----------------------------------------------------


async def test_create_school_makes_creator_a_member(client: AsyncClient, teacher: Profile) -> None:
    sid = await make_school(client, teacher)
    r = await client.get("/teacher/schools", headers=bearer(teacher.id))
    assert [s["id"] for s in r.json()] == [sid]
    assert r.json()[0]["name"] == "Northside Primary"


async def test_non_member_cannot_see_school_or_its_students(
    client: AsyncClient, teacher: Profile, other_teacher: Profile
) -> None:
    sid = await make_school(client, teacher)
    r = await client.get(f"/teacher/schools/{sid}/students", headers=bearer(other_teacher.id))
    assert r.status_code == 403
    r = await client.get("/teacher/schools", headers=bearer(other_teacher.id))
    assert r.json() == []


async def test_join_school_grants_roster_read_but_not_ownership(
    client: AsyncClient, teacher: Profile, other_teacher: Profile, student: Student
) -> None:
    sid = await make_school(client, teacher)
    r = await client.patch(
        f"/teacher/students/{student.id}", json={"school_id": sid}, headers=bearer(teacher.id)
    )
    assert r.status_code == 200 and r.json()["school_id"] == sid
    r = await client.post(f"/teacher/schools/{sid}/join", headers=bearer(other_teacher.id))
    assert r.status_code == 204
    r = await client.get(f"/teacher/schools/{sid}/students", headers=bearer(other_teacher.id))
    assert r.status_code == 200
    assert [s["display_name"] for s in r.json()] == ["Sam"]
    # Membership does not let the other teacher assign to, or open, the student.
    r = await client.get(f"/teacher/students/{student.id}", headers=bearer(other_teacher.id))
    assert r.status_code == 403


async def test_student_can_only_be_placed_in_a_school_the_teacher_belongs_to(
    client: AsyncClient, teacher: Profile, other_teacher: Profile
) -> None:
    sid = await make_school(client, other_teacher, "Elsewhere College")
    body = {
        "display_name": "Kim",
        "level": "beginner",
        "instrument_family": "brass",
        "school_id": sid,
    }
    r = await client.post("/teacher/students", json=body, headers=bearer(teacher.id))
    assert r.status_code == 403


# --- terms ------------------------------------------------------------------------------


async def test_terms_are_school_scoped(
    client: AsyncClient, teacher: Profile, other_teacher: Profile
) -> None:
    sid = await make_school(client, teacher)
    body = {"name": "Term 4 2026", "starts_on": "2026-10-05", "ends_on": "2026-12-18"}
    r = await client.post(f"/teacher/schools/{sid}/terms", json=body, headers=bearer(teacher.id))
    assert r.status_code == 201 and r.json()["name"] == "Term 4 2026"
    r = await client.get(f"/teacher/schools/{sid}/terms", headers=bearer(teacher.id))
    assert len(r.json()) == 1
    r = await client.post(
        f"/teacher/schools/{sid}/terms", json=body, headers=bearer(other_teacher.id)
    )
    assert r.status_code == 403


async def test_term_dates_must_be_ordered(client: AsyncClient, teacher: Profile) -> None:
    sid = await make_school(client, teacher)
    body = {"name": "Bad", "starts_on": "2026-12-18", "ends_on": "2026-10-05"}
    r = await client.post(f"/teacher/schools/{sid}/terms", json=body, headers=bearer(teacher.id))
    assert r.status_code == 422


# --- lessons and attendance -----------------------------------------------------------


async def test_schedule_lesson_mark_attendance_and_add_notes(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    body = {"scheduled_at": "2026-10-06T15:30:00+11:00", "duration_minutes": 30}
    r = await client.post(
        f"/teacher/students/{student.id}/lessons", json=body, headers=bearer(teacher.id)
    )
    assert r.status_code == 201, r.text
    lesson = r.json()
    assert lesson["status"] == "scheduled" and lesson["attendance"] is None

    r = await client.patch(
        f"/teacher/lessons/{lesson['id']}",
        json={"status": "completed", "notes": "Worked bars 5-8 slowly. Reed was soft."},
        headers=bearer(teacher.id),
    )
    assert r.status_code == 200 and r.json()["status"] == "completed"

    r = await client.put(
        f"/teacher/lessons/{lesson['id']}/attendance",
        json={"status": "present", "note": "on time"},
        headers=bearer(teacher.id),
    )
    assert r.status_code == 200 and r.json()["attendance"] == {
        "status": "present",
        "note": "on time",
    }

    r = await client.get(f"/teacher/students/{student.id}/lessons", headers=bearer(teacher.id))
    assert [lesson_["id"] for lesson_ in r.json()] == [lesson["id"]]
    assert r.json()[0]["notes"].startswith("Worked bars")


async def test_lesson_in_a_term_must_fall_within_it(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    sid = await make_school(client, teacher)
    await client.patch(
        f"/teacher/students/{student.id}", json={"school_id": sid}, headers=bearer(teacher.id)
    )
    term = (
        await client.post(
            f"/teacher/schools/{sid}/terms",
            json={"name": "T4", "starts_on": "2026-10-05", "ends_on": "2026-12-18"},
            headers=bearer(teacher.id),
        )
    ).json()
    body = {
        "scheduled_at": "2027-01-06T15:30:00+11:00",
        "duration_minutes": 30,
        "term_id": term["id"],
    }
    r = await client.post(
        f"/teacher/students/{student.id}/lessons", json=body, headers=bearer(teacher.id)
    )
    assert r.status_code == 422
    body["scheduled_at"] = "2026-10-06T15:30:00+11:00"
    r = await client.post(
        f"/teacher/students/{student.id}/lessons", json=body, headers=bearer(teacher.id)
    )
    assert r.status_code == 201


async def test_other_teacher_cannot_touch_lessons(
    client: AsyncClient, teacher: Profile, other_teacher: Profile, student: Student
) -> None:
    body = {"scheduled_at": "2026-10-06T15:30:00+11:00", "duration_minutes": 30}
    r = await client.post(
        f"/teacher/students/{student.id}/lessons", json=body, headers=bearer(other_teacher.id)
    )
    assert r.status_code == 403
    lesson = (
        await client.post(
            f"/teacher/students/{student.id}/lessons", json=body, headers=bearer(teacher.id)
        )
    ).json()
    r = await client.put(
        f"/teacher/lessons/{lesson['id']}/attendance",
        json={"status": "absent"},
        headers=bearer(other_teacher.id),
    )
    assert r.status_code == 403
    r = await client.patch(
        f"/teacher/lessons/{lesson['id']}",
        json={"status": "cancelled"},
        headers=bearer(other_teacher.id),
    )
    assert r.status_code == 403


async def test_teacher_schedule_lists_lessons_across_students(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    for day in (6, 7):
        await client.post(
            f"/teacher/students/{student.id}/lessons",
            json={"scheduled_at": f"2026-10-0{day}T15:30:00+11:00", "duration_minutes": 30},
            headers=bearer(teacher.id),
        )
    r = await client.get(
        "/teacher/lessons?from=2026-10-01&to=2026-10-31", headers=bearer(teacher.id)
    )
    assert r.status_code == 200 and len(r.json()) == 2
    assert r.json()[0]["student_display_name"] == "Sam"
    r = await client.get(
        "/teacher/lessons?from=2026-11-01&to=2026-11-30", headers=bearer(teacher.id)
    )
    assert r.json() == []


# --- contacts -----------------------------------------------------------------------------


async def test_contacts_crud_and_primary(
    client: AsyncClient, teacher: Profile, other_teacher: Profile, student: Student
) -> None:
    body = {
        "name": "Priya Nair",
        "relationship": "mother",
        "phone": "0400 000 000",
        "email": "priya@example.com",
        "is_primary": True,
    }
    r = await client.post(
        f"/teacher/students/{student.id}/contacts", json=body, headers=bearer(teacher.id)
    )
    assert r.status_code == 201 and r.json()["is_primary"] is True
    cid = r.json()["id"]
    second = {**body, "name": "Arun Nair", "relationship": "father", "is_primary": True}
    r = await client.post(
        f"/teacher/students/{student.id}/contacts", json=second, headers=bearer(teacher.id)
    )
    assert r.status_code == 201
    r = await client.get(f"/teacher/students/{student.id}/contacts", headers=bearer(teacher.id))
    primaries = [c["name"] for c in r.json() if c["is_primary"]]
    assert primaries == ["Arun Nair"]  # only one primary at a time
    r = await client.delete(f"/teacher/contacts/{cid}", headers=bearer(other_teacher.id))
    assert r.status_code == 403
    r = await client.delete(f"/teacher/contacts/{cid}", headers=bearer(teacher.id))
    assert r.status_code == 204
    r = await client.get(f"/teacher/students/{student.id}/contacts", headers=bearer(teacher.id))
    assert [c["name"] for c in r.json()] == ["Arun Nair"]


async def test_unknown_ids_are_404_not_500(client: AsyncClient, teacher: Profile) -> None:
    ghost = uuid.uuid4()
    r = await client.get(f"/teacher/schools/{ghost}/terms", headers=bearer(teacher.id))
    assert r.status_code in (403, 404)
    r = await client.patch(
        f"/teacher/lessons/{ghost}", json={"status": "cancelled"}, headers=bearer(teacher.id)
    )
    assert r.status_code == 404
