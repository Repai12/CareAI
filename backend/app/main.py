"""
main.py
-------
SHARED FILE - FastAPI entrypoint. Run with:
    uvicorn app.main:app --reload

TEAM RULE: when you add your own router, add ONE import line and ONE
app.include_router() line below, in the marked sections. Don't touch
anyone else's line. This keeps merge conflicts on this file to a minimum.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
import app.models  # noqa: F401 - imports every model so create_all sees them

from app.routers import auth, dashboard, reports, me, ai_summary, notifications
from app.routers import vitals as vitals_router
from app.routers import emergency as emergency_router

# --- Member 2 (Afifa) - Medications, Appointments, Google Calendar sync,
# Medication Adherence logging, Doctor Visit Notes ---
from app.routers import medications as medications_router
from app.routers.appointments import router as appointment_router
from app.routers.calendar import router as calendar_router
from app.routers.medication_logs import router as medication_log_router
from app.routers.visit_notes import router as visit_note_router

from app.services.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Shared / Member 4 routers (active) ---
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(me.router)
app.include_router(ai_summary.router)
app.include_router(notifications.router)

# --- Member 1 (Mubasshira) ---
app.include_router(vitals_router.router)

# --- Member 2 (Afifa) ---
app.include_router(medications_router.router)
app.include_router(appointment_router)
app.include_router(calendar_router)
app.include_router(medication_log_router)
app.include_router(visit_note_router)

# --- Member 3 (Faisal) ---
app.include_router(emergency_router.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def root():
    return {"status": "CareAI backend running"}