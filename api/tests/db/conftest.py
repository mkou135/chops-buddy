"""Database fixtures.

A throwaway Postgres for the test session: `CB_TEST_DATABASE_URL` if set (CI service
container), else an embedded Postgres via pgserver (DECISIONS #17). Migrations are
applied once per session with the real alembic CLI, exactly as CI and deploys do.
"""

import os
import subprocess
import sys
import tempfile
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

API_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    url = os.environ.get("CB_TEST_DATABASE_URL")
    if url:
        yield url
        return
    import pgserver

    with tempfile.TemporaryDirectory() as tmp:
        server = pgserver.get_server(tmp)  # pyright: ignore[reportPrivateImportUsage]
        sockdir = server.get_uri().split("host=")[1]
        yield f"postgresql+asyncpg://postgres@/postgres?host={sockdir}"
        server.cleanup()


@pytest.fixture(scope="session")
def migrated(database_url: str) -> str:
    env = {**os.environ, "CB_DATABASE_URL": database_url}
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=API_DIR, env=env, check=True
    )
    return database_url


@pytest.fixture
async def session(migrated: str) -> AsyncIterator[AsyncSession]:
    """One transaction per test, rolled back at the end."""
    engine = create_async_engine(migrated)
    async with engine.connect() as conn:
        await conn.begin()
        factory = async_sessionmaker(
            conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with factory() as s:
            yield s
        await conn.rollback()
    await engine.dispose()
