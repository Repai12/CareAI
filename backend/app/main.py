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

# ============================================================
# TEAM ROUTERS
# ============================================================

from app.routers import dashboard, reports, auth_stub

# ============================================================
# TEAM SCHEDULER
# ============================================================

from app.services.scheduler import start_scheduler

# ============================================================
# MEMBER 2 - AFIFA
# ============================================================

from app.routes import router as medication_router
from app.appointments import router as appointment_router
from app.calendar import router as calendar_router
from app.medication_logs import router as medication_log_router
from app.visit_notes import router as visit_note_router


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="CareAI API",
    description="AI-Powered Elderly Health Monitoring Platform",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# TEAM ROUTERS
# ============================================================

app.include_router(auth_stub.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


# ============================================================
# MEMBER 2 - AFIFA ROUTERS
# ============================================================

app.include_router(medication_router)
app.include_router(appointment_router)
app.include_router(calendar_router)
app.include_router(medication_log_router)
app.include_router(visit_note_router)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def on_startup():
    start_scheduler()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "CareAI backend running"
    }