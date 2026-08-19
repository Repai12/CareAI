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
)
from app.routers import vitals as vitals_router
from app.routers import emergency as emergency_router
from app.routers import medications as medications_router
from app.routers import fall_incidents as fall_incidents_router
from app.routers import safety_checkin as safety_checkin_router

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
app.include_router(medications_router.router)  # placeholder, 0 routes
app.include_router(emergency_router.router)
app.include_router(fall_incidents_router.router)
app.include_router(safety_checkin_router.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(reports.router)
app.include_router(ai_summary.router)


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.get("/")
def root():
    return {"status": "CareAI backend running"}
