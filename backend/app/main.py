from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routes import router
from .appointments import router as appointment_router
from .calendar import router as calendar_router
from .medication_logs import router as medication_log_router
from .visit_notes import router as visit_note_router


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Medication Management API"
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
# ROUTERS
# ============================================================

# Existing medication routes
app.include_router(router)

# Appointment routes
app.include_router(appointment_router)

# Google Calendar routes
app.include_router(calendar_router)

# Medication Reminder & Adherence routes
app.include_router(medication_log_router)

# Doctor Visit History & Prescription Notes routes
app.include_router(visit_note_router)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "HealthCare Management API is running"
    }