"""
ORM models package.

Importing this package registers every model with SQLAlchemy's metadata,
which `init_db` relies on to create tables.
"""

from app.models.call import Call, RiskEvent
from app.models.speaker import Speaker

__all__ = ["Speaker", "Call", "RiskEvent"]
