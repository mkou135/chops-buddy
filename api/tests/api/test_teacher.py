"""Teacher routes: roster, assignment, state visibility, tenant isolation (DoD A9)."""

from httpx import AsyncClient

from chops_buddy.db.models import Profile, Student
from tests.api.conftest import TARGET_BODY, bearer


async def test_create_and_list_own_students(client: AsyncClient, teacher: Profile) -> None:
    body = {"display_name": "Kim", "level": "beginner", "instrument_family": "brass"}
    r = await client.post("/teacher/students", json=body, headers=bearer(teacher.id))
    assert r.status_code == 201
    created = r.json()
    assert created["display_name"] == "Kim" and created["teacher_id"] == str(teacher.id)

    r = await client.get("/teacher/students", headers=bearer(teacher.id))
    assert r.status_code == 200
    assert [s["display_name"] for s in r.json()] == ["Kim"]


async def test_teacher_cannot_see_other_teachers_student(
    client: AsyncClient, teacher: Profile, other_student: Student
) -> None:
    r = await client.get(f"/teacher/students/{other_student.id}", headers=bearer(teacher.id))
    assert r.status_code == 403
    r = await client.post(
        f"/teacher/students/{other_student.id}/targets",
        json=TARGET_BODY,
        headers=bearer(teacher.id),
    )
    assert r.status_code == 403
    r = await client.get("/teacher/students", headers=bearer(teacher.id))
    assert r.json() == []


async def test_assign_target_creates_initial_state(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    r = await client.post(
        f"/teacher/students/{student.id}/targets", json=TARGET_BODY, headers=bearer(teacher.id)
    )
    assert r.status_code == 201
    target = r.json()
    assert target["title"] == "Minuet, bars 1-8"
    assert target["state"]["mode"] == "working" and target["state"]["tempo"] == 72

    r = await client.get(f"/teacher/students/{student.id}", headers=bearer(teacher.id))
    assert r.status_code == 200
    detail = r.json()
    assert detail["display_name"] == "Sam"
    assert [t["id"] for t in detail["targets"]] == [target["id"]]


async def test_assign_rejects_engine_invalid_target(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    bad = {**TARGET_BODY, "units": []}
    r = await client.post(
        f"/teacher/students/{student.id}/targets", json=bad, headers=bearer(teacher.id)
    )
    assert r.status_code == 422


async def test_deactivate_target_removes_it_from_active_list(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    r = await client.post(
        f"/teacher/students/{student.id}/targets", json=TARGET_BODY, headers=bearer(teacher.id)
    )
    tid = r.json()["id"]
    r = await client.delete(f"/teacher/targets/{tid}", headers=bearer(teacher.id))
    assert r.status_code == 204
    r = await client.get(f"/teacher/students/{student.id}", headers=bearer(teacher.id))
    assert r.json()["targets"] == []


async def test_deactivate_other_teachers_target_is_403(
    client: AsyncClient, teacher: Profile, other_teacher: Profile, other_student: Student
) -> None:
    r = await client.post(
        f"/teacher/students/{other_student.id}/targets",
        json=TARGET_BODY,
        headers=bearer(other_teacher.id),
    )
    tid = r.json()["id"]
    r = await client.delete(f"/teacher/targets/{tid}", headers=bearer(teacher.id))
    assert r.status_code == 403
