"""Speaker enrollment/lookup endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.speaker import SpeakerEnrollRequest, SpeakerResponse
from app.services import call_service

router = APIRouter(prefix="/api/v1/speakers", tags=["speakers"])


@router.post("/enroll", response_model=SpeakerResponse)
def enroll(req: SpeakerEnrollRequest, db: Session = Depends(get_db)):
    speaker = call_service.enroll_speaker(
        db, req.speaker_id, req.name, req.enrollment_seed
    )
    return speaker


@router.get("/{speaker_id}", response_model=SpeakerResponse)
def get_speaker(speaker_id: str, db: Session = Depends(get_db)):
    speaker = call_service.get_speaker(db, speaker_id)
    if speaker is None:
        raise HTTPException(status_code=404, detail="speaker not found")
    return speaker
