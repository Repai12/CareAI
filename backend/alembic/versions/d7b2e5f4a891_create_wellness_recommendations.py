"""create wellness_recommendations

Revision ID: d7b2e5f4a891
Revises: c3f8a1d9e654
Create Date: 2026-08-21 01:00:00.000000

Module 2 Wellness Recommendation Engine (README Features table, listed
separately from "nutrition planner") - never built. IF NOT EXISTS, same
reasoning as every prior migration in this chain.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd7b2e5f4a891'
down_revision: Union[str, Sequence[str], None] = 'c3f8a1d9e654'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS wellness_recommendations (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            based_on_summary TEXT NOT NULL,
            recommendations TEXT NOT NULL,
            created_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_wellness_recommendations_patient_id ON wellness_recommendations (patient_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_wellness_recommendations_patient_id")
    op.execute("DROP TABLE IF EXISTS wellness_recommendations")
