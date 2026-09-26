"""Stub telemetry receiver. No persistence."""

from fastapi.testclient import TestClient


def test_telemetry_batch_returns_received_count(client: TestClient) -> None:
    response = client.post(
        "/telemetry/events",
        json={
            "events": [
                {
                    "eventId": "11111111-1111-4111-8111-111111111111",
                    "timestamp": "2026-09-25T18:00:00+00:00",
                    "sessionId": "sess-1",
                    "userId": "1",
                    "event_type": "section_viewed",
                    "schemaVersion": "1.0.0",
                    "requestId": "req-1",
                    "properties": {"path": "/inventory"},
                },
                {
                    "eventId": "22222222-2222-4222-8222-222222222222",
                    "timestamp": "2026-09-25T18:00:01+00:00",
                    "sessionId": "sess-1",
                    "userId": None,
                    "event_type": "login_failed",
                    "schemaVersion": "1.0.0",
                    "requestId": "req-2",
                    "properties": {"reason": "invalid_credentials"},
                },
            ]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2}


def test_telemetry_get_explains_post_only_stub(client: TestClient) -> None:
    response = client.get("/telemetry/events")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HealthCore telemetry stub" in response.text
    assert "POST" in response.text


def test_telemetry_rejects_incomplete_envelope(client: TestClient) -> None:
    response = client.post(
        "/telemetry/events",
        json={"events": [{"event_type": "section_viewed"}]},
    )
    assert response.status_code == 422
