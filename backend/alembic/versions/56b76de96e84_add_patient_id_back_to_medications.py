"""add patient_id back to medications

Revision ID: 56b76de96e84
Revises: ee7a225fc085
Create Date: 2026-08-20 04:10:00.000000

`medications` has had no patient linkage since migration 5c905c544fa2
dropped it, meaning there was no way to know whose medication a row
was - the dashboard's active-medications list and the (until now empty)
medications router could only ever return nothing or everyone's rows
mixed together. Adds patient_id back as a real FK.

Any pre-existing medication rows have no way to be attributed to a real
patient (there was never a column to infer it from) - they're deleted
rather than guessed at, since a wrong guess would silently show one
patient someone else's medication list, which is worse than the row not
existing. These are demo/seed rows, not real user data (per README's
own "no hardcoded/mock data" rule, orphaned mock rows shouldn't be kept
around anyway) - seed_demo_data.py has been updated to create properly
patient_id-scoped ones going forward.
"""
from typing import Sequence, Union

from alembic import op


revision: str = '56b76de96e84'
down_revision: Union[str, Sequence[str], None] = 'ee7a225fc085'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE medications ADD COLUMN IF NOT EXISTS patient_id UUID REFERENCES users(id)")
    op.execute("DELETE FROM medications WHERE patient_id IS NULL")
    op.execute("ALTER TABLE medications ALTER COLUMN patient_id SET NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_medications_patient_id ON medications (patient_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_medications_patient_id")
    op.execute("ALTER TABLE medications DROP COLUMN IF EXISTS patient_id")
