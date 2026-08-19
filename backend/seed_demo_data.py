"""
seed_demo_data.py
------------------
Inserts real demo rows so the Dashboard and Weekly Report have data to
show, without waiting on every module's own CRUD features to be built.

SAFE TO RUN ONCE against an empty/fresh database:
    python seed_demo_data.py

NOT SAFE TO RE-RUN against a database that already has this demo data -
`users.email` is unique, so a second run would previously crash halfway
through with an IntegrityError. This script now checks for the demo
patient first and exits cleanly instead, per the team's workflow rule
that seed scripts must never be re-run blindly against existing data.
"""

from datetime import datetime, timedelta

from app.database import SessionLocal, Base, engine
import app.models  # noqa: F401 - registers every model with Base before create_all
from app.models.user import User, UserRole, PatientLink
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment
from app.auth import hash_password, generate_patient_code

DEMO_PATIENT_EMAIL = "patient@demo.com"

Base.metadata.create_all(bind=engine)
db = SessionLocal()

existing = db.query(User).filter(User.email == DEMO_PATIENT_EMAIL).first()
if existing:
    print(f"Demo data already present (found {DEMO_PATIENT_EMAIL}) - skipping.")
    print("Delete these rows manually first if you want to reseed.")
    db.close()
    raise SystemExit(0)

patient = User(name="Abdul Karim", email=DEMO_PATIENT_EMAIL,
               hashed_password=hash_password("password123"), role=UserRole.patient.value)
db.add(patient)
db.flush()
patient.patient_code = generate_patient_code(db)

family = User(name="Nusrat Karim", email="family@demo.com",
              hashed_password=hash_password("password123"), role=UserRole.family.value)
doctor = User(name="Dr. Farhana Rahman", email="doctor@demo.com",
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

# Medication/Appointment have no patient linkage in the current schema
# (see models/medication.py) - these rows are demo content only, not
# scoped to the demo patient above.
db.add_all([
    Medication(medicine_name="Metformin", dosage="500mg", frequency="Twice daily",
               start_date=datetime.utcnow().date(), end_date=None),
    Medication(medicine_name="Amlodipine", dosage="5mg", frequency="Once daily",
               start_date=datetime.utcnow().date(), end_date=None),
])

appointment_date = (datetime.utcnow() + timedelta(days=3)).date()
db.add(Appointment(
    doctor_name="Dr. Farhana Rahman",
    location="BRAC Health Center, Room 4",
    status="upcoming",
    patient_name=patient.name,
    patient_email=patient.email,
    appointment_date=appointment_date,
    start_time=datetime.strptime("10:00", "%H:%M").time(),
    end_time=datetime.strptime("10:30", "%H:%M").time(),
    reason="Routine follow-up",
))

db.commit()

print("Seed complete.")
print(f"Patient ID: {patient.id}")
print(f"Patient Code (for family/doctor registration): {patient.patient_code}")
print("Login: patient@demo.com / family@demo.com / doctor@demo.com, password: password123")

db.close()
