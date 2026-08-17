from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
# Import all models to ensure metadata registration
from app.models import user, emergency, vitals, medication, notification, email_log, fall_incident
from app.routers import (
    auth,
    me,
    vitals as vitals_router,
    medications,
    emergency as emergency_router,
    dashboard,
    notifications,
    reports,
    ai_summary
)
from app.services.scheduler import start_scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CareAI System",
    description="AI-Powered Elderly Health Monitoring Platform",
    version="1.0.0"
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registrations
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(vitals_router.router)
app.include_router(medications.router)
app.include_router(emergency_router.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(ai_summary.router)

# Startup Event to Start Safety Check-in Scheduler
@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.get("/")
def read_root():
    return {"message": "CareAI API is running successfully"}
