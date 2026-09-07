"""
Session helpers.

`get_db` is a FastAPI dependency that yields a scoped session and always closes
it. `init_db` creates tables for the MVP (a lightweight substitute for
migrations, which can be added later with Alembic).
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.connection import Base, SessionLocal, engine


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when the request finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Safe to call repeatedly; existing tables are kept."""
    # Import models so they register with Base.metadata before create_all.
    from app import models  # noqa: F401  (registration side effect)

    Base.metadata.create_all(bind=engine)
