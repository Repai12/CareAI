"""
models/email_log.py
---------------------
OWNED BY MEMBER 4 (Repai) - audit trail for every outbound email, used by
both the Weekly Report (Module 2/4) and, later, the Doctor AI Summary
email (Module 3/7) - `report_type` distinguishes which feature sent it.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipient_email = Column(String, nullable=False)
    report_type = Column(String, nullable=False, default="WEEKLY_REPORT")  # WEEKLY_REPORT / DOCTOR_AI_SUMMARY
    summary_text = Column(Text, nullable=False)
    status = Column(String, default="SENT")  # SENT or FAILED
    sent_at = Column(DateTime, default=datetime.utcnow)
