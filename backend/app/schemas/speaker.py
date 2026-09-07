"""Pydantic schemas for speaker endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SpeakerEnrollRequest(BaseModel):
    speaker_id: str = Field(..., examples=["speaker_001"])
    name: str = Field(..., examples=["Rahul"])
    # For the MVP, enrollment audio is provided as injected samples via a
    # separate path; here we accept an optional textual seed so the mock
    # embedding is stable per speaker without shipping raw audio in JSON.
    enrollment_seed: str | None = Field(
        default=None,
        description="Optional stable seed for the mock embedding (MVP only).",
    )


class SpeakerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    created_at: datetime | None = None
