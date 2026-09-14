"""Supabase JWT verification and role dependencies (DECISIONS #7, #9).

HS256 with the project's JWT secret for now; JWKS verification is added in M4
when the service goes live.
"""

import uuid
from dataclasses import dataclass
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from chops_buddy.db.base import get_session
from chops_buddy.db.models import Profile
from chops_buddy.settings import settings

AUDIENCE = "authenticated"


@dataclass(frozen=True)
class Claims:
    user_id: uuid.UUID
    email: str | None


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def claims_from_request(request: Request) -> Claims:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("missing_bearer_token")
    if not settings.supabase_jwt_secret:
        raise _unauthorized("auth_not_configured")
    try:
        payload: dict[str, Any] = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
            token, settings.supabase_jwt_secret, algorithms=["HS256"], audience=AUDIENCE
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized("invalid_token") from exc
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise _unauthorized("invalid_token") from exc
    return Claims(user_id=user_id, email=payload.get("email"))


ClaimsDep = Annotated[Claims, Depends(claims_from_request)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def current_profile(claims: ClaimsDep, session: SessionDep) -> Profile:
    profile = await session.get(Profile, claims.user_id)
    if profile is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="no_profile")
    return profile


ProfileDep = Annotated[Profile, Depends(current_profile)]


async def current_teacher(profile: ProfileDep) -> Profile:
    if profile.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="teacher_only")
    return profile


async def current_student_profile(profile: ProfileDep) -> Profile:
    if profile.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="student_only")
    return profile


TeacherDep = Annotated[Profile, Depends(current_teacher)]
StudentProfileDep = Annotated[Profile, Depends(current_student_profile)]
