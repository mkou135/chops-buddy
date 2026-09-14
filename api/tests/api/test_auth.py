"""DoD A9: 401 without a valid token, 403 across tenants, profile bootstrap."""

import uuid

from httpx import AsyncClient

from chops_buddy.db.models import Profile
from tests.api.conftest import bearer


async def test_no_token_is_401(client: AsyncClient) -> None:
    r = await client.get("/me")
    assert r.status_code == 401


async def test_bad_signature_is_401(client: AsyncClient, teacher: Profile) -> None:
    headers = bearer(teacher.id)
    headers["Authorization"] = headers["Authorization"][:-4] + "xxxx"
    r = await client.get("/me", headers=headers)
    assert r.status_code == 401


async def test_expired_token_is_401(client: AsyncClient, teacher: Profile) -> None:
    r = await client.get("/me", headers=bearer(teacher.id, expired=True))
    assert r.status_code == 401


async def test_me_returns_profile(client: AsyncClient, teacher: Profile) -> None:
    r = await client.get("/me", headers=bearer(teacher.id))
    assert r.status_code == 200
    assert r.json() == {"id": str(teacher.id), "role": "teacher", "display_name": "Teacher A"}


async def test_valid_token_without_profile_is_403(client: AsyncClient) -> None:
    r = await client.get("/me", headers=bearer(uuid.uuid4()))
    assert r.status_code == 403
    assert r.json()["detail"] == "no_profile"


async def test_profile_bootstrap_creates_profile_from_claims(client: AsyncClient) -> None:
    uid = uuid.uuid4()
    r = await client.post(
        "/me/profile",
        json={"role": "teacher", "display_name": "New T"},
        headers=bearer(uid, email="new@x.io"),
    )
    assert r.status_code == 201
    assert r.json() == {"id": str(uid), "role": "teacher", "display_name": "New T"}
    again = await client.post(
        "/me/profile", json={"role": "teacher", "display_name": "Dup"}, headers=bearer(uid)
    )
    assert again.status_code == 409


async def test_student_cannot_use_teacher_routes(client: AsyncClient, student) -> None:  # type: ignore[no-untyped-def]
    r = await client.get("/teacher/students", headers=bearer(student.profile_id))
    assert r.status_code == 403
