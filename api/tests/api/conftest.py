"""API fixtures: an httpx client bound to the test transaction, and JWT minting."""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from chops_buddy.api.main import app
from chops_buddy.db.base import get_session
from chops_buddy.db.models import Profile, Student
from chops_buddy.engine.models import InstrumentFamily, Level
from chops_buddy.settings import settings

TEST_SECRET = "test-jwt-secret-not-for-production"


def token(user_id: uuid.UUID, email: str = "u@x.io", *, expired: bool = False) -> str:
    now = datetime.now(UTC)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    claims = {"sub": str(user_id), "email": email, "aud": "authenticated", "exp": exp, "iat": now}
    return jwt.encode(claims, TEST_SECRET, algorithm="HS256")


def bearer(user_id: uuid.UUID, **kw: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {token(user_id, **kw)}"}  # type: ignore[arg-type]


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = _override
    settings.supabase_jwt_secret = TEST_SECRET
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def teacher(session: AsyncSession) -> Profile:
    p = Profile(id=uuid.uuid4(), role="teacher", display_name="Teacher A", email="a@x.io")
    session.add(p)
    await session.flush()
    return p


@pytest.fixture
async def other_teacher(session: AsyncSession) -> Profile:
    p = Profile(id=uuid.uuid4(), role="teacher", display_name="Teacher B", email="b@x.io")
    session.add(p)
    await session.flush()
    return p


@pytest.fixture
async def student(session: AsyncSession, teacher: Profile) -> Student:
    """A student of `teacher` who has signed in (profile linked)."""
    profile = Profile(id=uuid.uuid4(), role="student", display_name="Sam", email="s@x.io")
    s = Student(
        teacher_id=teacher.id,
        profile_id=profile.id,
        display_name="Sam",
        level=Level.intermediate,
        instrument_family=InstrumentFamily.wind,
    )
    session.add_all([profile, s])
    await session.flush()
    return s


@pytest.fixture
async def other_student(session: AsyncSession, other_teacher: Profile) -> Student:
    profile = Profile(id=uuid.uuid4(), role="student", display_name="Olly", email="o@x.io")
    s = Student(
        teacher_id=other_teacher.id,
        profile_id=profile.id,
        display_name="Olly",
        level=Level.beginner,
        instrument_family=InstrumentFamily.keyboard,
    )
    session.add_all([profile, s])
    await session.flush()
    return s


TARGET_BODY = {
    "kind": "repertoire",
    "title": "Minuet, bars 1-8",
    "target_tempo": 120,
    "units": [f"b{i}" for i in range(1, 9)],
}
