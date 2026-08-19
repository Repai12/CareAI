"""create medication_logs and visit_notes

Revision ID: 23cef9385926
Revises: 56b76de96e84
Create Date: 2026-08-20 05:00:00.000000

These two tables (README S8.3 doctor visit notes, S8.4 medicine
adherence tracker) never existed - the original create-application-
tables migration explicitly skipped them with a comment claiming they
"already exist in NeonDB" (see the note at the bottom of migration
5c905c544fa2's history), which wasn't true for a fresh database, and the
two dead router files that assumed they existed (app/medication_logs.py,
app/visit_notes.py) imported model classes that were never defined
anywhere either. Created from scratch here, matching the real request/
response shapes those routers (now rewritten with real auth) actually
need.

Written with IF NOT EXISTS throughout, same reasoning as the
users/care_links migrations before this one: app/main.py's
Base.metadata.create_all() can create these tables empty before this
migration ever runs (it happened while testing this exact migration -
a `python -c "from app.main import app"` sanity check beat
`alembic upgrade head` to creating them), and a plain CREATE TABLE
would then fail with "relation already exists".
"""
from typing import Sequence, Union

from alembic import op


revision: str = '23cef9385926'
down_revision: Union[str, Sequence[str], None] = '56b76de96e84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS medication_logs (
            id UUID PRIMARY KEY,
            medication_id UUID NOT NULL REFERENCES medications(id),
            patient_id UUID NOT NULL REFERENCES users(id),
            scheduled_at TIMESTAMP NOT NULL,
            taken_at TIMESTAMP,
            status VARCHAR NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_medication_logs_medication_id ON medication_logs (medication_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_medication_logs_patient_id ON medication_logs (patient_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS visit_notes (
            id UUID PRIMARY KEY,
            patient_id UUID NOT NULL REFERENCES users(id),
            patient_name VARCHAR NOT NULL,
            doctor_id UUID NOT NULL REFERENCES users(id),
            doctor_name VARCHAR NOT NULL,
            appointment_id UUID REFERENCES appointments(id),
            visit_date DATE NOT NULL,
            notes TEXT NOT NULL,
            prescription TEXT,
            status VARCHAR NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_visit_notes_patient_id ON visit_notes (patient_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_visit_notes_doctor_id ON visit_notes (doctor_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_visit_notes_doctor_id")
    op.execute("DROP INDEX IF EXISTS ix_visit_notes_patient_id")
    op.execute("DROP TABLE IF EXISTS visit_notes")
    op.execute("DROP INDEX IF EXISTS ix_medication_logs_patient_id")
    op.execute("DROP INDEX IF EXISTS ix_medication_logs_medication_id")
    op.execute("DROP TABLE IF EXISTS medication_logs")
