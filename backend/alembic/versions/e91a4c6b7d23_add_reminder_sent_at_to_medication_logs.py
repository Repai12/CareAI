"""add reminder_sent_at to medication_logs

Revision ID: e91a4c6b7d23
Revises: d7b2e5f4a891
Create Date: 2026-08-21 02:00:00.000000

The Medicine Reminder & Adherence Tracker (README S8.4) had no way to
tell whether a due-now reminder notification had already been sent for
a given scheduled dose - needed so the new scheduled job (see
services/medication_reminder_service.py) doesn't re-notify the same
pending dose on every tick.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e91a4c6b7d23'
down_revision: Union[str, Sequence[str], None] = 'd7b2e5f4a891'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE medication_logs ADD COLUMN IF NOT EXISTS reminder_sent_at TIMESTAMP")


def downgrade() -> None:
    op.execute("ALTER TABLE medication_logs DROP COLUMN IF EXISTS reminder_sent_at")
