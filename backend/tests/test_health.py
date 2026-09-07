"""Phase 1 smoke test: the health endpoint responds and the app boots."""


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "VoiceShield"
    assert "version" in body
