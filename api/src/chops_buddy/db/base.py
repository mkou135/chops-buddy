"""Engine and session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from chops_buddy.settings import settings

# Supabase's transaction-mode pooler (Supavisor) does not support prepared statements,
# so asyncpg's statement cache must be off. Harmless against a direct connection.
ASYNCPG_POOLER_ARGS: dict[str, object] = {"statement_cache_size": 0}


def make_engine(url: str | None = None) -> AsyncEngine:
    return create_async_engine(url or settings.database_url, connect_args=ASYNCPG_POOLER_ARGS)


engine = make_engine()
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, committed on success."""
    async with SessionFactory() as session:
        yield session
        await session.commit()
