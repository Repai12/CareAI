"""create activity_logs

Revision ID: c3f8a1d9e654
Revises: b5e0f61c9d47
Create Date: 2026-08-21 00:00:00.000000

Module 1 Activity Tracking (README Features table: "Activity tracking
with trend dashboards") - never built, no table existed. IF NOT EXISTS,
same reasoning as every prior migration in this chain.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3f8a1d9e654'
down_revision: Union[str, Sequence[str], None] = 'b5e0f61c9d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            activity_type VARCHAR NOT NULL,
            duration_minutes INTEGER NOT NULL,
            note TEXT,
            logged_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_activity_logs_patient_id ON activity_logs (patient_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_activity_logs_patient_id")
    op.execute("DROP TABLE IF EXISTS activity_logs")
