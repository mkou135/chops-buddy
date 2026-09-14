from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from chops_buddy.api import schemas
from chops_buddy.api.auth import ClaimsDep, ProfileDep, SessionDep
from chops_buddy.api.routers import crm, student, teacher
from chops_buddy.db.models import Profile
from chops_buddy.settings import settings

app = FastAPI(title="Chops Buddy API", version="0.1.0")


class _CORS(CORSMiddleware):
    """Reads the origin list from settings at request time so tests can change it."""

    def __init__(self, app: object) -> None:  # type: ignore[override]
        super().__init__(
            app,  # type: ignore[arg-type]
            allow_origins=[],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=False,
        )

    def is_allowed_origin(self, origin: str) -> bool:
        return origin in settings.cors_origins


app.add_middleware(_CORS)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(crm.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "commit": settings.commit_sha}


@app.get("/me")
async def me(profile: ProfileDep) -> schemas.ProfileOut:
    return schemas.ProfileOut(id=profile.id, role=profile.role, display_name=profile.display_name)


@app.post("/me/profile", status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: schemas.ProfileCreate, claims: ClaimsDep, session: SessionDep
) -> schemas.ProfileOut:
    """First-login bootstrap: create the profile row for the authenticated user.

    The caller chooses their own role. Acceptable for v0.1; a student is harmless
    without a linked students row and a teacher only ever sees students they create.
    """
    if await session.get(Profile, claims.user_id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="profile_exists")
    profile = Profile(
        id=claims.user_id,
        role=body.role,
        display_name=body.display_name,
        email=claims.email or "",
    )
    session.add(profile)
    await session.flush()
    return schemas.ProfileOut(id=profile.id, role=profile.role, display_name=profile.display_name)
