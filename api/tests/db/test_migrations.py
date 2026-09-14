"""DoD A10: migrations apply from an empty database."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

EXPECTED_TABLES = {
    "profiles",
    "schools",
    "school_memberships",
    "students",
    "targets",
    "target_states",
    "practice_sessions",
    "prescriptions",
    "log_entries",
}


async def test_migrations_create_all_tables(session: AsyncSession) -> None:
    rows = await session.execute(
        text("select table_name from information_schema.tables where table_schema = 'public'")
    )
    tables = {r[0] for r in rows}
    assert tables >= EXPECTED_TABLES
    assert "alembic_version" in tables


async def test_targets_units_must_be_non_empty(session: AsyncSession) -> None:
    from sqlalchemy.exc import DBAPIError

    await session.execute(
        text(
            "insert into profiles (id, role, display_name, email) "
            "values ('00000000-0000-0000-0000-000000000001', 'teacher', 'T', 't@x.io')"
        )
    )
    await session.execute(
        text(
            "insert into students (id, teacher_id, display_name, level, instrument_family) "
            "values ('00000000-0000-0000-0000-000000000002', "
            "'00000000-0000-0000-0000-000000000001', 'S', 'beginner', 'wind')"
        )
    )
    import pytest

    with pytest.raises(DBAPIError):
        await session.execute(
            text(
                "insert into targets (student_id, kind, title, target_tempo, units, position, "
                "created_by) values ('00000000-0000-0000-0000-000000000002', 'scale', 'C', 100, "
                "'[]'::jsonb, 0, '00000000-0000-0000-0000-000000000001')"
            )
        )
