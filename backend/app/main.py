"""
main.py
-------
FastAPI application entrypoint. Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import dashboard, reports, auth_stub, me
from app.services.scheduler import start_scheduler

# Creates tables that don't exist yet (fine for dev; use Alembic for prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CareAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_stub.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(me.router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/")
def root():
    return {"status": "CareAI backend running"}
