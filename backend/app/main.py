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
# Uncomment as each member's router gets real endpoints:
from app.routers import vitals as vitals_router
from app.routers import medications as medications_router
from app.routers import emergency as emergency_router

from app.services.scheduler import start_scheduler

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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

# --- Teammate routers (placeholders, safe to include even with no routes yet) ---
app.include_router(vitals_router.router)
app.include_router(medications_router.router)
app.include_router(emergency_router.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def root():
    return {"status": "CareAI backend running"}
