"""practice_sessions.llm_report

Revision ID: b1c2d3e4f5a6
Revises: d4d61a9f9269
Create Date: 2026-09-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "d4d61a9f9269"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "practice_sessions",
        sa.Column("llm_report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("practice_sessions", "llm_report")
