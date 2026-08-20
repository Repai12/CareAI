"""add ai_summary to visit_notes

Revision ID: d84e6a17c930
Revises: a1f3c9d02b41
Create Date: 2026-08-20 07:30:00.000000

AI Prescription Summarizer (README Features table, Module 3) - cached
plain-English explanation of a visit note's notes/prescription, generated
on demand and stored here so repeat views don't burn a new Groq call
every time (mirrors HealthReport.ai_summary's caching in models/vitals.py).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd84e6a17c930'
down_revision: Union[str, Sequence[str], None] = 'a1f3c9d02b41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE visit_notes ADD COLUMN IF NOT EXISTS ai_summary TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE visit_notes DROP COLUMN IF EXISTS ai_summary")
