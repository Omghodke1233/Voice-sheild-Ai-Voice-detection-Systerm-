"""
Live call WebSocket endpoint.

WS /ws/calls/{call_id}

Accepts two kinds of client messages:
  * Binary frames  -> raw 16-bit PCM mono @ 16 kHz audio samples.
  * JSON text frames -> control / mock injection, e.g.
        {"action": "analyze", "transcript": "send the money now"}
        {"action": "end"}

For Phase 5 we prove real-time communication using injected/mock data before
live browser audio is wired in (Phase 7). The server runs AnalysisService per
chunk and emits: call_status, risk_update, speaker_update, transcript_update,
and risk_event messages.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database.session import SessionLocal
from app.services import call_service
from app.services.analysis_service import AnalysisService

logger = logging.getLogger("voiceshield.ws")

router = APIRouter()

# One analysis service shared across connections (modules are stateless).
_analysis = AnalysisService()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pcm16_bytes_to_float32(data: bytes) -> np.ndarray:
    """Interpret raw bytes as int16 PCM and normalize to float32 [-1, 1]."""
    pcm = np.frombuffer(data, dtype=np.int16)
    return (pcm.astype(np.float32)) / 32768.0


async def _send(ws: WebSocket, payload: dict) -> None:
    await ws.send_text(json.dumps(payload))


@router.websocket("/ws/calls/{call_id}")
async def call_ws(ws: WebSocket, call_id: str):
    await ws.accept()
    await _send(ws, {"type": "call_status", "call_id": call_id, "status": "ACTIVE"})

    # Look up the call's claimed speaker (best-effort; demo calls may be adhoc).
    claimed_speaker_id = None
    db = SessionLocal()
    try:
        call = call_service.get_call(db, call_id)
        if call is not None:
            claimed_speaker_id = call.claimed_speaker_id
    finally:
        db.close()

    try:
        while True:
            message = await ws.receive()

            # Client disconnected.
            if message.get("type") == "websocket.disconnect":
                break

            samples: np.ndarray | None = None
            injected_transcript: str | None = None

            if message.get("bytes") is not None:
                samples = _pcm16_bytes_to_float32(message["bytes"])
            elif message.get("text") is not None:
                try:
                    ctrl = json.loads(message["text"])
                except json.JSONDecodeError:
                    await _send(ws, {"type": "call_status", "call_id": call_id,
                                     "status": "ERROR"})
                    continue

                if ctrl.get("action") == "end":
                    break
                injected_transcript = ctrl.get("transcript")
                # Optional inline PCM as a list of int16 (demo convenience).
                if ctrl.get("pcm16"):
                    samples = (np.array(ctrl["pcm16"], dtype=np.int16)
                               .astype(np.float32) / 32768.0)

            # Nothing usable to analyze in this frame.
            if samples is None and injected_transcript is None:
                continue

            await _send(ws, {"type": "call_status", "call_id": call_id,
                             "status": "ANALYZING"})

            # If we only have a transcript (mock demo), synthesize a short
            # neutral audio buffer so voice/speaker modules can still run.
            if samples is None:
                samples = np.zeros(16_000, dtype=np.float32)

            result = _analysis.analyze_chunk(
                samples,
                claimed_speaker_id=claimed_speaker_id,
                injected_transcript=injected_transcript,
            )
            await _emit_results(ws, call_id, result, injected_transcript)

    except WebSocketDisconnect:
        logger.info("ws disconnected", extra={"component": "ws", "call_id": call_id})
    except Exception as exc:  # never crash the server on one connection
        logger.exception("ws error", extra={"component": "ws", "call_id": call_id,
                                             "error_type": type(exc).__name__})
        try:
            await _send(ws, {"type": "call_status", "call_id": call_id,
                             "status": "ERROR"})
        except Exception:
            pass
    finally:
        # Persist the final risk snapshot and mark the call ended.
        _finalize(call_id)
        try:
            await _send(ws, {"type": "call_status", "call_id": call_id,
                             "status": "ENDED"})
        except Exception:
            pass


async def _emit_results(
    ws: WebSocket, call_id: str, result: dict, transcript: str | None
) -> None:
    """Translate an analysis result into the frontend's event messages."""
    risk = result["risk"]
    speaker = result.get("speaker")
    nlp = result.get("nlp") or {}

    # transcript_update (echo what was analyzed, if any)
    if transcript:
        await _send(ws, {"type": "transcript_update", "text": transcript,
                         "timestamp": _now_iso()})

    # speaker_update
    if speaker and speaker.get("status") != "ERROR":
        await _send(ws, {"type": "speaker_update",
                         "status": speaker.get("status"),
                         "similarity": speaker.get("similarity")})

    # risk_update
    await _send(ws, {
        "type": "risk_update", "call_id": call_id,
        "voice_suspicion": risk.get("voice_suspicion"),
        "speaker_risk": risk.get("speaker_risk"),
        "social_engineering": risk.get("social_engineering"),
        "conversation_anomaly": risk.get("conversation_anomaly"),
        "overall_risk": risk.get("overall_risk"),
        "risk_level": risk.get("risk_level"),
        "recommended_action": risk.get("recommended_action"),
    })

    # risk_event(s) from NLP-detected events + persist them
    db = SessionLocal()
    try:
        for ev in nlp.get("events", []) or []:
            category = ev.get("type", "EVENT")
            confidence = float(ev.get("confidence", 0.0))
            description = ev.get("description")
            await _send(ws, {"type": "risk_event", "category": category,
                             "confidence": confidence, "timestamp": _now_iso(),
                             "description": description})
            call_service.record_event(db, call_id, category, confidence, description)
        # Keep the call's latest risk snapshot fresh.
        if risk.get("overall_risk") is not None:
            call_service.update_call_risk(
                db, call_id, risk["overall_risk"], risk["risk_level"])
    finally:
        db.close()


def _finalize(call_id: str) -> None:
    db = SessionLocal()
    try:
        call = call_service.get_call(db, call_id)
        if call and call.status != "ENDED":
            call_service.end_call(db, call_id, call.overall_risk, call.risk_level)
    except Exception:
        logger.exception("finalize failed", extra={"component": "ws",
                                                    "call_id": call_id})
    finally:
        db.close()
