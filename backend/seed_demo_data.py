"""
seed_demo_data.py
------------------
Inserts real demo rows so the Dashboard and Weekly Report have data to
show, without waiting on Member 1/2/3's own CRUD features to be built.
Run once after your .env DATABASE_URL is set:
    python seed_demo_data.py
"""

from datetime import datetime, timedelta

from app.database import SessionLocal, Base, engine
import app.models
from app.models.user import User, UserRole, PatientLink
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment, AppointmentStatus
from app.auth import hash_password, generate_patient_code

Base.metadata.create_all(bind=engine)
db = SessionLocal()

patient = User(name="Abdul Karim", email="patient@demo.com",
               hashed_password=hash_password("password123"), role=UserRole.patient.value)
db.add(patient)
db.flush()
patient.patient_code = generate_patient_code(db)

family = User(name="Nusrat Karim", email="repai1001@gmail.com",
              hashed_password=hash_password("password123"), role=UserRole.family.value)
doctor = User(name="Dr. Farhana Rahman", email="repai1001+doctor@gmail.com",
              hashed_password=hash_password("password123"), role=UserRole.doctor.value)
db.add_all([family, doctor])
db.flush()

db.add_all([
    PatientLink(patient_id=patient.id, viewer_id=family.id, relationship_label="family"),
    PatientLink(patient_id=patient.id, viewer_id=doctor.id, relationship_label="doctor"),
])

db.add_all([
    VitalsLog(patient_id=patient.id, blood_pressure="130/85", sugar_level=110, heart_rate=78, temperature=36.8,
              logged_at=datetime.utcnow() - timedelta(days=2)),
    VitalsLog(patient_id=patient.id, blood_pressure="128/82", sugar_level=105, heart_rate=75, temperature=36.6,
              logged_at=datetime.utcnow() - timedelta(hours=6)),
])

db.add_all([
    Medication(patient_id=patient.id, name="Metformin", dosage="500mg", frequency="Twice daily",
               schedule_time="08:00,20:00", active=True),
    Medication(patient_id=patient.id, name="Amlodipine", dosage="5mg", frequency="Once daily",
               schedule_time="09:00", active=True),
])

db.add(Appointment(
    patient_id=patient.id, doctor_name="Dr. Farhana Rahman",
    scheduled_at=datetime.utcnow() + timedelta(days=3),
    location="BRAC Health Center, Room 4", status=AppointmentStatus.upcoming.value,
))

db.commit()

print("Seed complete.")
print(f"Patient ID: {patient.id}")
print(f"Patient Code (for family/doctor registration): {patient.patient_code}")
print("Login: patient@demo.com / repai1001@gmail.com / repai1001+doctor@gmail.com, password: password123")

db.close()
