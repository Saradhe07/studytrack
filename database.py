"""
SQLAlchemy engine + session setup for StudyTrack.
This file is intentionally minimal for now — we'll flesh out models.py next.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "studytrack.db"))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False is needed only for SQLite + FastAPI's threaded requests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI dependency: opens a session before the route body runs,
    closes it afterward, even if the route raises."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

