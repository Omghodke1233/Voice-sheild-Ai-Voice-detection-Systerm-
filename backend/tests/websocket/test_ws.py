"""WebSocket tests using injected mock data (Phase 5)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _start_call() -> str:
    client.post("/api/v1/speakers/enroll", json={
        "speaker_id": "speaker_ws", "name": "Rahul", "enrollment_seed": "s"})
    r = client.post("/api/v1/calls/start",
                    json={"claimed_speaker_id": "speaker_ws"})
    return r.json()["call_id"]


def test_ws_connect_emits_active_status():
    call_id = _start_call()
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "call_status"
        assert msg["status"] == "ACTIVE"
        ws.send_json({"action": "end"})


def test_ws_transcript_produces_risk_update_and_events():
    call_id = _start_call()
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        assert ws.receive_json()["status"] == "ACTIVE"

        ws.send_json({"action": "analyze",
                      "transcript": "This is an emergency, send the money now, "
                                    "don't tell anyone."})

        # Drain messages until we see a risk_update.
        seen = set()
        risk = None
        for _ in range(20):
            m = ws.receive_json()
            seen.add(m["type"])
            if m["type"] == "risk_update":
                risk = m
                break
        assert risk is not None
        assert "overall_risk" in risk
        assert risk["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        ws.send_json({"action": "end"})


def test_ws_binary_pcm_frame_produces_risk_update():
    # Phase 7: live-mic path. Send raw int16 PCM bytes (no transcript) and
    # expect voice/speaker analysis to still yield a risk_update.
    import numpy as np

    call_id = _start_call()
    pcm = (np.random.default_rng(0).standard_normal(16_000) * 8000).astype(np.int16)
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        assert ws.receive_json()["status"] == "ACTIVE"
        ws.send_bytes(pcm.tobytes())

        risk = None
        for _ in range(20):
            m = ws.receive_json()
            if m["type"] == "risk_update":
                risk = m
                break
        assert risk is not None
        assert risk["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        ws.send_json({"action": "end"})


def test_ws_malformed_frame_does_not_crash():
    call_id = _start_call()
    with client.websocket_connect(f"/ws/calls/{call_id}") as ws:
        assert ws.receive_json()["status"] == "ACTIVE"
        ws.send_text("not json {")
        # Should get an ERROR status but the connection stays open.
        m = ws.receive_json()
        assert m["type"] == "call_status"
        assert m["status"] == "ERROR"
        ws.send_json({"action": "end"})
