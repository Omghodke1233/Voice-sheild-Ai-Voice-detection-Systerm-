"""Speaker ORM model.

Represents an enrolled speaker. Note we store an `embedding_reference`
(a pointer/id) rather than the raw voice or raw embedding here, keeping
sensitive biometric data out of the primary table by default.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Speaker(Base):
    __tablename__ = "speakers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # Pointer to where the voice embedding lives (file/id), not the embedding.
    embedding_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="ENROLLED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
