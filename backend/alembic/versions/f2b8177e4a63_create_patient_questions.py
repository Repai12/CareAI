"""create patient_questions

Revision ID: f2b8177e4a63
Revises: d84e6a17c930
Create Date: 2026-08-20 08:00:00.000000

AI Patient History Q&A (README Features table, Module 3) - doctor-only
tool, never existed. IF NOT EXISTS, same reasoning as every prior
migration in this chain.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f2b8177e4a63'
down_revision: Union[str, Sequence[str], None] = 'd84e6a17c930'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS patient_questions (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            doctor_id UUID NOT NULL REFERENCES users(id),
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_patient_questions_patient_id ON patient_questions (patient_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_patient_questions_patient_id")
    op.execute("DROP TABLE IF EXISTS patient_questions")
