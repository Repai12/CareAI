"""create companion_messages

Revision ID: a7c19e5b3d02
Revises: f2b8177e4a63
Create Date: 2026-08-20 09:00:00.000000

Dual-Persona AI Companion (README Features table, Module 3) - never
existed. IF NOT EXISTS, same reasoning as every prior migration in this
chain.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a7c19e5b3d02'
down_revision: Union[str, Sequence[str], None] = 'f2b8177e4a63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS companion_messages (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            persona TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_companion_messages_patient_persona "
        "ON companion_messages (patient_id, persona, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_companion_messages_patient_persona")
    op.execute("DROP TABLE IF EXISTS companion_messages")
