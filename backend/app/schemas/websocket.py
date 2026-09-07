"""
WebSocket message schemas.

Documents the event contract the frontend consumes. Server->client messages
use a `type` discriminator: risk_update | transcript_update | risk_event |
speaker_update | call_status.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RiskUpdate(BaseModel):
    type: Literal["risk_update"] = "risk_update"
    call_id: str
    voice_suspicion: float | None = None
    speaker_risk: float | None = None
    social_engineering: float | None = None
    conversation_anomaly: float | None = None
    overall_risk: float
    risk_level: str
    recommended_action: str | None = None


class TranscriptUpdate(BaseModel):
    type: Literal["transcript_update"] = "transcript_update"
    text: str
    timestamp: str


class RiskEventMsg(BaseModel):
    type: Literal["risk_event"] = "risk_event"
    category: str
    confidence: float
    timestamp: str
    description: str | None = None


class SpeakerUpdate(BaseModel):
    type: Literal["speaker_update"] = "speaker_update"
    status: str
    similarity: float | None = None


class CallStatusMsg(BaseModel):
    type: Literal["call_status"] = "call_status"
    call_id: str
    status: str  # CONNECTING | ACTIVE | ANALYZING | ENDED | ERROR
