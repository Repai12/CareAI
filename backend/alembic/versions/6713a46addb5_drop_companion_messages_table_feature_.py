"""drop companion_messages table (feature removed)

Revision ID: 6713a46addb5
Revises: e91a4c6b7d23
Create Date: 2026-08-22 02:48:16.838956

The Dual-Persona AI Companion feature (routers/companion.py,
models/companion.py, the companion_reply() function that had been added
into Member 1's groq_health_service.py, and the frontend /companion
page) was removed at the user's request - its ownership was ambiguous
(no assigned owner in the team's file-ownership table, backing AI logic
landed in a file owned by a different member than the one who committed
the feature) and the team decided they don't need it.

Written as a new forward migration rather than editing/deleting
a7c19e5b3d02 (the original "create companion_messages" migration) -
that migration has very likely already been applied against the shared
team database, and rewriting an already-applied migration's history is
exactly the kind of thing that breaks alembic for every other teammate
who's already past that revision. Standard practice: never edit a
migration once it may have run for real; add a new one that undoes it.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '6713a46addb5'
down_revision: Union[str, Sequence[str], None] = 'e91a4c6b7d23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_companion_messages_patient_persona")
    op.execute("DROP TABLE IF EXISTS companion_messages")


def downgrade() -> None:
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
