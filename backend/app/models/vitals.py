"""
models/vitals.py
------------------
OWNED BY MEMBER 1 (Mubasshira) - Vitals Logging System.

This file currently has a minimal working version (built by Member 4 as a
placeholder so the Dashboard has real data to read). Member 1: extend this
freely with your full CRUD fields, validation ranges, and any additional
tables (medical_reports, symptom logs, diet logs) your AI features need -
just keep the class name `VitalsLog` and table name `vitals_logs` so
Member 4's dashboard queries don't break, or coordinate a rename with them.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, Float, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class VitalsLog(Base):
    __tablename__ = "vitals_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    blood_pressure = Column(String, nullable=False)   # e.g. "120/80"
    sugar_level = Column(Float, nullable=False)        # mg/dL
    heart_rate = Column(Float, nullable=False)         # bpm
    temperature = Column(Float, nullable=False)        # Celsius
    logged_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", back_populates="vitals")
