"""
Phase 8 integration + stability tests.

Covers the three demo scenarios end-to-end through the real WebSocket, plus
failure/disconnect handling and a soak test proving many consecutive calls
run without crashing (project target: >= 10 consecutive runs).
"""

import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _enroll_and_start(speaker="speaker_demo"):
    client.post("/api/v1/speakers/enroll", json={
        "speaker_id": speaker, "name": "Rahul", "enrollment_seed": "seed"})
    r = client.post("/api/v1/calls/start", json={"claimed_speaker_id": speaker})
    return r.json()["call_id"]


def _drain_until_risk(ws, sends, expect_events=0):
    """Send messages, then read frames until we've captured the risk_update
    and at least `expect_events` risk_event frames.

    Message order per analyzed frame is: transcript_update, speaker_update,
    risk_update, then risk_event(s). We stop as soon as our expectations are
    met so we never block waiting on frames that won't come.
    """
    for s in sends:
        ws.send_json(s)
    risk = None
    events = 0
    types = set()
    for _ in range(60):
        m = ws.receive_json()
        types.add(m["type"])
        if m["type"] == "risk_update":
            risk = m
        elif m["type"] == "risk_event":
            events += 1
        if risk is not None and events >= expect_events:
            break
    return risk, types


# --- Demo scenarios ---------------------------------------------------------


def test_scenario_genuine_conversation_runs():
    call_id = _enroll_and_start()
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        assert ws.receive_json()["status"] == "ACTIVE"
        risk, _ = _drain_until_risk(
            ws, [{"action": "analyze", "transcript": "Hi, confirming our meeting tomorrow at 10."}])
        assert risk is not None
        assert risk["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        ws.send_json({"action": "end"})


def test_scenario_full_attack_emits_events_and_high_risk():
    call_id = _enroll_and_start()
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        assert ws.receive_json()["status"] == "ACTIVE"
        risk, types = _drain_until_risk(ws, [{
            "action": "analyze",
            "transcript": ("This is an emergency. Transfer the money immediately "
                           "and don't tell anyone. Share the OTP now."),
        }], expect_events=1)
        assert risk is not None
        # Social-engineering-heavy transcript should elevate risk meaningfully.
        assert risk["overall_risk"] >= 0.25
        assert "risk_event" in types


def test_events_persisted_and_retrievable():
    call_id = _enroll_and_start()
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        ws.receive_json()
        _drain_until_risk(ws, [{
            "action": "analyze",
            "transcript": "Emergency! Send money now, share your OTP, keep it secret."}],
            expect_events=1)
        ws.send_json({"action": "end"})
    events = client.get(f"/api/v1/calls/{call_id}/events").json()
    assert isinstance(events, list)
    assert len(events) >= 1


# --- Failure / disconnect ---------------------------------------------------


def test_disconnect_midcall_is_clean():
    call_id = _enroll_and_start()
    ws = client.websocket_connect(f"/ws/calls/{call_id}")
    conn = ws.__enter__()
    assert conn.receive_json()["status"] == "ACTIVE"
    conn.send_json({"action": "analyze", "transcript": "hello"})
    # Abrupt close without an 'end' action.
    ws.__exit__(None, None, None)
    # Call should be marked ENDED by the finalize path.
    call = client.get(f"/api/v1/calls/{call_id}").json()
    assert call["status"] == "ENDED"


def test_call_without_enrolled_speaker_still_runs():
    # No speaker enrolled -> speaker module INCONCLUSIVE, pipeline continues.
    r = client.post("/api/v1/calls/start", json={"claimed_speaker_id": "ghost"})
    call_id = r.json()["call_id"]
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        ws.receive_json()
        risk, _ = _drain_until_risk(ws, [{"action": "analyze", "transcript": "hello there"}])
        assert risk is not None  # did not crash despite missing speaker


# --- Soak / stability -------------------------------------------------------


def test_ten_consecutive_calls_without_crash():
    for i in range(12):
        call_id = _enroll_and_start(speaker=f"spk_{i}")
        with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
            assert ws.receive_json()["status"] == "ACTIVE"
            risk, _ = _drain_until_risk(
                ws, [{"action": "analyze", "transcript": f"call number {i}, send money now"}])
            assert risk is not None
            ws.send_json({"action": "end"})
        ended = client.get(f"/api/v1/calls/{call_id}").json()
        assert ended["status"] == "ENDED"
