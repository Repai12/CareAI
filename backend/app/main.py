"""
main.py
-------
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload

De-duplicated after a merge conflict resolution left two copies of every
import/setup block in this file (CORS, app creation, router registration,
root endpoint were each defined twice) - consolidated into one clean
version, keeping every router that's actually implemented.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Import all models so SQLAlchemy registers them before create_all() runs.
import app.models  # noqa: F401

from app.routers import (
    auth,
    me,
    dashboard,
    reports,
    ai_summary,
    notifications,
    mood,
    patient_qa,
)
from app.routers import vitals as vitals_router
from app.routers import emergency as emergency_router
from app.routers import medications as medications_router
from app.routers import fall_incidents as fall_incidents_router
from app.routers import safety_checkin as safety_checkin_router
from app import appointments as appointments_router
from app import calendar as calendar_router
from app import medication_logs as medication_logs_router
from app import visit_notes as visit_notes_router

from app.services.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CareAI System",
    description="AI-Powered Elderly Health Monitoring Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(vitals_router.router)
app.include_router(medications_router.router)
app.include_router(emergency_router.router)
app.include_router(fall_incidents_router.router)
app.include_router(safety_checkin_router.router)
app.include_router(appointments_router.router)
# Google Calendar OAuth flow - fully built but nobody on the team has
# completed the OAuth consent flow / has a credentials.json yet, so
# every route here 404s/401s until someone does. Booking itself doesn't
# depend on this (see appointments.py/crud.py - Calendar sync is
# best-effort), this just exposes the connect/status/events endpoints.
app.include_router(calendar_router.router)
app.include_router(medication_logs_router.router)
app.include_router(visit_notes_router.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(ai_summary.router)
app.include_router(mood.router)
app.include_router(patient_qa.router)


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.get("/")
def root():
    return {"status": "CareAI backend running"}
