"""create application tables

Revision ID: 5c905c544fa2
Revises:
Create Date: 2026-08-16

Creates the tables owned by Member 2 (medications, appointments) from
scratch, matching the current shape of app/models/medication.py.

NOTE: this migration originally shipped as a set of ALTER statements
transforming an *old* pre-existing shape of these tables (patient_id,
scheduled_at, name, schedule_time, active) into the current shape. That
only worked against the specific dev database it was written against,
which already had those old columns. Against a genuinely fresh/empty
database (e.g. a new teammate's first `alembic upgrade head`, or a new
Neon branch) the ALTERs failed immediately because "appointments" and
"medications" didn't exist yet for op.add_column to target - one of the
root causes of "the app doesn't run on a fresh clone". Rewritten below
to CREATE the tables directly instead, since there is no real production
data in this course project that needs an in-place transform preserved.

env.py's include_object() restricts Alembic to exactly these two tables
plus medication_logs/visit_notes (both still unmigrated - see AUDIT.md);
every other table (users, vitals_logs, notifications, etc.) is created
by app/main.py's Base.metadata.create_all() on startup, which is a
deliberate per-member ownership split, not an oversight - this migration
does not touch those tables.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "5c905c544fa2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """Create medications and appointments from scratch."""

    op.create_table(
        "medications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("medicine_name", sa.String(), nullable=False),
        sa.Column("dosage", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_medications_id", "medications", ["id"], unique=False)

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doctor_name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("patient_name", sa.String(), nullable=False),
        sa.Column("patient_email", sa.String(), nullable=False),
        sa.Column("appointment_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("google_event_id", sa.String(), nullable=True),
    )
    op.create_index("ix_appointments_id", "appointments", ["id"], unique=False)


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    op.drop_index("ix_appointments_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_medications_id", table_name="medications")
    op.drop_table("medications")