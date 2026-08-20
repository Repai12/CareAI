"""create chat_messages

Revision ID: b5e0f61c9d47
Revises: a7c19e5b3d02
Create Date: 2026-08-20 10:00:00.000000

Family Chat over WebSockets (README Features table, Module 3, named
explicitly in the Tech Stack table) - never existed. IF NOT EXISTS, same
reasoning as every prior migration in this chain.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b5e0f61c9d47'
down_revision: Union[str, Sequence[str], None] = 'a7c19e5b3d02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            sender_id UUID NOT NULL REFERENCES users(id),
            sender_name TEXT NOT NULL,
            sender_role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_patient_created "
        "ON chat_messages (patient_id, created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_patient_created")
    op.execute("DROP TABLE IF EXISTS chat_messages")
