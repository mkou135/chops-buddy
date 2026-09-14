from fastapi import FastAPI

from chops_buddy.settings import settings

app = FastAPI(title="Chops Buddy API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "commit": settings.commit_sha}
