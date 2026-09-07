"""
Database engine and declarative Base.

Uses SQLAlchemy 2.0 style. The engine is created from settings.database_url,
so switching between SQLite (local dev) and PostgreSQL (Docker/prod) is a
matter of changing one environment variable — no code changes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False when used across FastAPI's threadpool.
# This argument is invalid for other drivers, so apply it only for SQLite.
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""
