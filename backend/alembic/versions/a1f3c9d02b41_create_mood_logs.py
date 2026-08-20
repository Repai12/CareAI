"""create mood_logs

Revision ID: a1f3c9d02b41
Revises: 23cef9385926
Create Date: 2026-08-20 07:00:00.000000

Module 1 Mood Tracking (README Features table) - never built, no table
existed at all. IF NOT EXISTS throughout, same reasoning as every prior
migration in this chain: app/main.py's Base.metadata.create_all() can
create this table empty before this migration ever runs.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a1f3c9d02b41'
down_revision: Union[str, Sequence[str], None] = '23cef9385926'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            mood VARCHAR NOT NULL,
            note TEXT,
            logged_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_mood_logs_patient_id ON mood_logs (patient_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_mood_logs_patient_id")
    op.execute("DROP TABLE IF EXISTS mood_logs")
