"""Student routes: assignments, next session, logging, history, isolation (DoD A4, A9)."""

import uuid

from httpx import AsyncClient

from chops_buddy.db.models import Profile, Student
from chops_buddy.settings import settings
from tests.api.conftest import TARGET_BODY, bearer


async def assign(client: AsyncClient, teacher: Profile, student: Student) -> str:
    r = await client.post(
        f"/teacher/students/{student.id}/targets", json=TARGET_BODY, headers=bearer(teacher.id)
    )
    assert r.status_code == 201
    return r.json()["id"]


def as_student(student: Student) -> dict[str, str]:
    assert student.profile_id is not None
    return bearer(student.profile_id)


async def test_list_my_targets(client: AsyncClient, teacher: Profile, student: Student) -> None:
    tid = await assign(client, teacher, student)
    r = await client.get("/me/targets", headers=as_student(student))
    assert r.status_code == 200
    assert [t["id"] for t in r.json()] == [tid]


async def test_next_session_with_llm_absent_comes_from_engine(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    settings.llm_api_key = None
    await assign(client, teacher, student)
    r = await client.post(
        "/me/sessions", json={"duration_minutes": 20}, headers=as_student(student)
    )
    assert r.status_code == 201
    body = r.json()
    assert body["source"] == "engine"
    kinds = [s["kind"] for s in body["plan"]["segments"]]
    assert kinds == ["long_tones", "repertoire"]  # wind student
    assert sum(s["minutes"] for s in body["plan"]["segments"]) == 20
    assert body["plan"]["segments"][1]["prescription"]["id"]
    assert len(body["plan"]["plan_hash"]) == 64


async def test_next_session_with_nothing_assigned_is_409(
    client: AsyncClient, other_student: Student
) -> None:
    r = await client.post(
        "/me/sessions", json={"duration_minutes": 10}, headers=as_student(other_student)
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "nothing_to_practise"


async def test_log_advances_state_and_appears_in_history(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    await assign(client, teacher, student)
    r = await client.post(
        "/me/sessions", json={"duration_minutes": 20}, headers=as_student(student)
    )
    session_id = r.json()["id"]
    pid = r.json()["plan"]["segments"][1]["prescription"]["id"]

    r = await client.post(
        "/me/logs",
        json={
            "prescription_id": pid,
            "tempo_used": 72,
            "best_consecutive": 5,
            "felt_difficulty": 3,
            "free_text": "felt good",
        },
        headers=as_student(student),
    )
    assert r.status_code == 201
    assert r.json()["state_after"]["tempo"] == 84  # E-30

    r = await client.get("/me/targets", headers=as_student(student))
    assert r.json()[0]["state"]["tempo"] == 84

    r = await client.get("/me/history", headers=as_student(student))
    assert r.status_code == 200
    history = r.json()
    assert [s["id"] for s in history] == [session_id]
    assert history[0]["completed_at"] is not None  # every prescription logged
    assert history[0]["logs"][0]["free_text"] == "felt good"

    # The same prescription cannot be logged twice.
    r = await client.post(
        "/me/logs",
        json={
            "prescription_id": pid,
            "tempo_used": 72,
            "best_consecutive": 5,
            "felt_difficulty": 3,
        },
        headers=as_student(student),
    )
    assert r.status_code == 409


async def test_engine_rejection_is_422_with_code(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    await assign(client, teacher, student)
    r = await client.post(
        "/me/sessions", json={"duration_minutes": 20}, headers=as_student(student)
    )
    pid = r.json()["plan"]["segments"][1]["prescription"]["id"]
    r = await client.post(
        "/me/logs",
        json={
            "prescription_id": pid,
            "tempo_used": 72,
            "best_consecutive": 2,
            "break_unit": 8,
            "felt_difficulty": 4,
        },
        headers=as_student(student),
    )
    assert r.status_code == 422
    assert r.json()["detail"] == "break_unit_out_of_fragment"


async def test_student_cannot_read_or_log_another_students_session(
    client: AsyncClient, teacher: Profile, student: Student, other_student: Student
) -> None:
    await assign(client, teacher, student)
    r = await client.post(
        "/me/sessions", json={"duration_minutes": 10}, headers=as_student(student)
    )
    session_id = r.json()["id"]
    pid = r.json()["plan"]["segments"][1]["prescription"]["id"]

    r = await client.get(f"/me/sessions/{session_id}", headers=as_student(other_student))
    assert r.status_code == 403
    r = await client.post(
        "/me/logs",
        json={
            "prescription_id": pid,
            "tempo_used": 72,
            "best_consecutive": 5,
            "felt_difficulty": 3,
        },
        headers=as_student(other_student),
    )
    assert r.status_code == 403
    r = await client.get(f"/me/sessions/{session_id}", headers=as_student(student))
    assert r.status_code == 200


async def test_unknown_prescription_is_404(client: AsyncClient, student: Student) -> None:
    r = await client.post(
        "/me/logs",
        json={
            "prescription_id": str(uuid.uuid4()),
            "tempo_used": 72,
            "best_consecutive": 5,
            "felt_difficulty": 3,
        },
        headers=as_student(student),
    )
    assert r.status_code == 404


async def test_teacher_sees_student_history(
    client: AsyncClient, teacher: Profile, student: Student
) -> None:
    await assign(client, teacher, student)
    await client.post("/me/sessions", json={"duration_minutes": 10}, headers=as_student(student))
    r = await client.get(f"/teacher/students/{student.id}/history", headers=bearer(teacher.id))
    assert r.status_code == 200 and len(r.json()) == 1
