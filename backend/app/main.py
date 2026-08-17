"""
main.py
-------
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine

# Import all models so SQLAlchemy registers them
# before create_all() is executed.
import app.models  # noqa: F401

# Team routers
from app.routers import (
    auth,
    me,
    dashboard,
    reports,
    ai_summary,
    notifications,
)

from app.routers import vitals as vitals_router
from app.routers import emergency as emergency_router

# Member 2 — Afifa
from app.routers import medications as medications_router
from app.routers.appointments import router as appointment_router
from app.routers.calendar import router as calendar_router
from app.routers.medication_logs import router as medication_log_router
from app.routers.visit_notes import router as visit_note_router

# Scheduler
from app.services.scheduler import start_scheduler


# ============================================================
# DATABASE TABLE CREATION
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="CareAI System",
    description="AI-Powered Elderly Health Monitoring Platform",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

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


# ============================================================
# TEAM ROUTERS
# ============================================================

app.include_router(auth.router)
app.include_router(me.router)

app.include_router(vitals_router.router)
app.include_router(emergency_router.router)

app.include_router(dashboard.router)
app.include_router(reports.router)

app.include_router(notifications.router)
app.include_router(ai_summary.router)


# ============================================================
# MEMBER 2 — AFIFA
# ============================================================

# Medication management
app.include_router(medications_router.router)

# Appointment management
app.include_router(appointment_router)

# Google Calendar integration
app.include_router(calendar_router)

# Medication reminder and adherence tracking
app.include_router(medication_log_router)

# Doctor visit history and prescription notes
app.include_router(visit_note_router)


# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
def startup_event():
    start_scheduler()


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "CareAI backend running"
    }