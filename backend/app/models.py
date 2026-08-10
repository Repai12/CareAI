from sqlalchemy import Column, Integer, String, Date, Time
from .database import Base


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)

    medicine_name = Column(String, nullable=False)

    dosage = Column(String, nullable=False)

    frequency = Column(String, nullable=False)

    start_date = Column(Date)

    end_date = Column(Date)
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    patient_name = Column(String, nullable=False)
    patient_email = Column(String, nullable=False)

    doctor_name = Column(String, nullable=False)

    appointment_date = Column(Date, nullable=False)

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    reason = Column(String, nullable=True)
    location = Column(String, nullable=True)

    status = Column(String, default="booked")

    google_event_id = Column(String, nullable=True)
