"""Call lifecycle endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.call import (
    CallResponse,
    CallStartRequest,
    CallStartResponse,
    RiskEventResponse,
)
from app.services import call_service

router = APIRouter(prefix="/api/v1/calls", tags=["calls"])


@router.post("/start", response_model=CallStartResponse)
def start_call(req: CallStartRequest, db: Session = Depends(get_db)):
    call = call_service.start_call(db, req.claimed_speaker_id)
    return CallStartResponse(call_id=call.id, status=call.status)


@router.get("/{call_id}", response_model=CallResponse)
def get_call(call_id: str, db: Session = Depends(get_db)):
    call = call_service.get_call(db, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="call not found")
    return call


@router.post("/{call_id}/end", response_model=CallResponse)
def end_call(call_id: str, db: Session = Depends(get_db)):
    call = call_service.end_call(db, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="call not found")
    return call


@router.get("/{call_id}/events", response_model=list[RiskEventResponse])
def get_events(call_id: str, db: Session = Depends(get_db)):
    call = call_service.get_call(db, call_id)
    if call is None:
        raise HTTPException(status_code=404, detail="call not found")
    return call_service.list_events(db, call_id)
