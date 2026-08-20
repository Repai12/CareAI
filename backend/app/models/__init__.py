"""
models/__init__.py
--------------------
Imports every model file so SQLAlchemy's Base.metadata knows about all
tables when main.py calls Base.metadata.create_all(). When you add a new
model file, add its import here too.
"""
from app.models.user import User, UserRole, CareLink, CareLinkStatus, CareLinkPermission, RefreshToken
from app.models.vitals import VitalsLog
from app.models.medication import Medication, Appointment, MedicationLog, MedicationLogStatus, VisitNote
from app.models.email_log import EmailLog
from app.models.emergency import EmergencyContact
from app.models.fall_incident import FallIncident
from app.models.safety_checkin import SafetyCheckin
from app.models.notification import Notification
from app.models.mood import MoodLog, MoodLevel
from app.models.patient_qa import PatientQuestion
from app.models.companion import CompanionMessage, CompanionPersona, CompanionRole
