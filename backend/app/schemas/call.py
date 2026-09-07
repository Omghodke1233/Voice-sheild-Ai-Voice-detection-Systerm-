"""Pydantic schemas for call endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CallStartRequest(BaseModel):
    claimed_speaker_id: str | None = Field(default=None, examples=["speaker_001"])


class CallStartResponse(BaseModel):
    call_id: str
    status: str


class CallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claimed_speaker_id: str | None = None
    status: str
    overall_risk: float | None = None
    risk_level: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None


class RiskEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    call_id: str
    event_type: str
    confidence: float | None = None
    description: str | None = None
    timestamp: datetime | None = None
