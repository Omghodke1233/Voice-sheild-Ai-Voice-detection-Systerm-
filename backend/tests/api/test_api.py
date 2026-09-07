"""API tests: speaker enrollment and call lifecycle."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_enroll_and_get_speaker():
    r = client.post("/api/v1/speakers/enroll", json={
        "speaker_id": "speaker_001", "name": "Om Ghodke",
        "enrollment_seed": "om-seed",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "speaker_001"
    assert body["name"] == "Om Ghodke"
    assert body["status"] == "ENROLLED"

    r2 = client.get("/api/v1/speakers/speaker_001")
    assert r2.status_code == 200
    assert r2.json()["name"] == "Om Ghodke"


def test_get_unknown_speaker_404():
    assert client.get("/api/v1/speakers/nope").status_code == 404


def test_call_lifecycle():
    start = client.post("/api/v1/calls/start",
                        json={"claimed_speaker_id": "speaker_001"})
    assert start.status_code == 200
    call_id = start.json()["call_id"]
    assert start.json()["status"] == "ACTIVE"

    got = client.get(f"/api/v1/calls/{call_id}")
    assert got.status_code == 200
    assert got.json()["id"] == call_id

    ended = client.post(f"/api/v1/calls/{call_id}/end")
    assert ended.status_code == 200
    assert ended.json()["status"] == "ENDED"

    events = client.get(f"/api/v1/calls/{call_id}/events")
    assert events.status_code == 200
    assert isinstance(events.json(), list)


def test_get_unknown_call_404():
    assert client.get("/api/v1/calls/nope").status_code == 404
