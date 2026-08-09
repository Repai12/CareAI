"""
seed_demo_data.py
------------------
Run this ONCE after your tables exist, so you have real data to demo the
Dashboard and Weekly Report with - WITHOUT waiting for Member-1/2/3's
vitals/medication/appointment features to be merged.

Usage:
    python seed_demo_data.py

This inserts real rows into Postgres (not hardcoded API responses) - it
satisfies "no hardcoded data" because the dashboard still reads live from
the DB; this script is just how the data got there, same as a form would.
"""

from datetime import datetime, timedelta

from app.database import SessionLocal, Base, engine
from app.models import User, UserRole, PatientLink, Vitals, Medication, Appointment, AppointmentStatus
from app.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Create a patient, a family member, and a doctor
patient = User(name="Abdul Karim", email="patient@demo.com",
               hashed_password=hash_password("password123"), role=UserRole.patient)
family = User(name="Nusrat Karim", email="repai1001@gmail.com",
              hashed_password=hash_password("password123"), role=UserRole.family)
doctor = User(name="Dr. Farhana Rahman", email="repai1001+doctor@gmail.com",
              hashed_password=hash_password("password123"), role=UserRole.doctor)

db.add_all([patient, family, doctor])
db.commit()
db.refresh(patient)
db.refresh(family)
db.refresh(doctor)

# 2. Link family + doctor to the patient so they can view the dashboard
db.add_all([
    PatientLink(patient_id=patient.id, viewer_id=family.id, relationship_label="family"),
    PatientLink(patient_id=patient.id, viewer_id=doctor.id, relationship_label="doctor"),
])

# 3. Some vitals history
db.add_all([
    Vitals(patient_id=patient.id, blood_pressure="130/85", sugar_level=110, heart_rate=78, temperature=36.8,
           recorded_at=datetime.utcnow() - timedelta(days=2)),
    Vitals(patient_id=patient.id, blood_pressure="128/82", sugar_level=105, heart_rate=75, temperature=36.6,
           recorded_at=datetime.utcnow() - timedelta(hours=6)),
])

# 4. Active medications
db.add_all([
    Medication(patient_id=patient.id, name="Metformin", dosage="500mg", frequency="Twice daily",
               schedule_time="08:00,20:00", active=True),
    Medication(patient_id=patient.id, name="Amlodipine", dosage="5mg", frequency="Once daily",
               schedule_time="09:00", active=True),
])

# 5. An upcoming appointment
db.add(Appointment(
    patient_id=patient.id, doctor_name="Dr. Farhana Rahman",
    scheduled_at=datetime.utcnow() + timedelta(days=3),
    location="BRAC Health Center, Room 4", status=AppointmentStatus.upcoming,
))

db.commit()
db.close()

print("Seed complete.")
print(f"Patient ID (use this in the dashboard URL): {patient.id}")
print("Login as patient@demo.com / family@demo.com / doctor@demo.com, password: password123")
