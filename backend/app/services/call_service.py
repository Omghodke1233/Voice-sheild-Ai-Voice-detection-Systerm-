"""
Call lifecycle service.

Owns creation/lookup of speakers and calls and persistence of risk events.
Keeps DB access out of the API/WebSocket layers and out of the AI modules
(project rule: AI modules never touch the database).

IDs are generated with uuid4 hex; time uses timezone-aware UTC.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.ai.speaker_verification.embedding import embed
from app.ai.speaker_verification.enrollment import get_store
from app.models.call import Call, RiskEvent
from app.models.speaker import Speaker

logger = logging.getLogger("voiceshield.services.call")


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Speakers ---------------------------------------------------------------


def enroll_speaker(
    db: Session, speaker_id: str, name: str, enrollment_seed: str | None
) -> Speaker:
    """Create/replace a speaker and register a mock reference embedding.

    The embedding is derived from a stable seed (or the speaker_id) so the MVP
    has a deterministic reference without storing raw audio.
    """
    import numpy as np

    seed_text = enrollment_seed or speaker_id
    # Build a deterministic pseudo-signal from the seed for the mock embedding.
    seed_bytes = np.frombuffer(seed_text.encode("utf-8"), dtype=np.uint8)
    signal = (seed_bytes.astype(np.float32) / 255.0) if seed_bytes.size else np.zeros(1, dtype=np.float32)
    get_store().enroll(speaker_id, signal)

    speaker = db.get(Speaker, speaker_id)
    if speaker is None:
        speaker = Speaker(id=speaker_id, name=name, status="ENROLLED",
                          embedding_reference=f"mock:{speaker_id}")
        db.add(speaker)
    else:
        speaker.name = name
        speaker.status = "ENROLLED"
    db.commit()
    db.refresh(speaker)
    logger.info("speaker enrolled", extra={"component": "services.call"})
    return speaker


def get_speaker(db: Session, speaker_id: str) -> Speaker | None:
    return db.get(Speaker, speaker_id)


# --- Calls ------------------------------------------------------------------


def start_call(db: Session, claimed_speaker_id: str | None) -> Call:
    call = Call(
        id=_uid("call"),
        claimed_speaker_id=claimed_speaker_id,
        status="ACTIVE",
        started_at=_utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def get_call(db: Session, call_id: str) -> Call | None:
    return db.get(Call, call_id)


def end_call(
    db: Session, call_id: str,
    overall_risk: float | None = None, risk_level: str | None = None,
) -> Call | None:
    call = db.get(Call, call_id)
    if call is None:
        return None
    call.status = "ENDED"
    call.ended_at = _utcnow()
    if overall_risk is not None:
        call.overall_risk = overall_risk
    if risk_level is not None:
        call.risk_level = risk_level
    db.commit()
    db.refresh(call)
    return call


def update_call_risk(
    db: Session, call_id: str, overall_risk: float, risk_level: str
) -> None:
    call = db.get(Call, call_id)
    if call is None:
        return
    call.overall_risk = overall_risk
    call.risk_level = risk_level
    db.commit()


def record_event(
    db: Session, call_id: str, event_type: str,
    confidence: float | None, description: str | None,
) -> RiskEvent:
    event = RiskEvent(
        id=_uid("evt"),
        call_id=call_id,
        event_type=event_type,
        confidence=confidence,
        description=description,
        timestamp=_utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session, call_id: str) -> list[RiskEvent]:
    call = db.get(Call, call_id)
    return list(call.events) if call else []
