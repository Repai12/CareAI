"""
database.py
------------
Sets up the SQLAlchemy engine + session for talking to PostgreSQL.
Every router will import `get_db` as a dependency to get a DB session
per-request (and it auto-closes when the request finishes).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
