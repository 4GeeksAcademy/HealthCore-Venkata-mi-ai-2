"""Telemetry sink: per-event validate + bulk insert (no frontend changes)."""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.telemetry.models import TelemetryEventRow
from app.telemetry.store import get_telemetry_engine


def _valid_event(**overrides: object) -> dict:
    base = {
        "eventId": "11111111-1111-4111-8111-111111111111",
        "timestamp": "2026-09-25T18:00:00+00:00",
        "sessionId": "sess-1",
        "userId": "1",
        "event_type": "section_viewed",
        "schemaVersion": "1.0.0",
        "requestId": "req-1",
        "properties": {"path": "/inventory"},
    }
    base.update(overrides)
    return base


def test_telemetry_batch_stores_valid_events(client: TestClient) -> None:
    response = client.post(
        "/telemetry/events",
        json={
            "events": [
                _valid_event(),
                _valid_event(
                    eventId="22222222-2222-4222-8222-222222222222",
                    timestamp="2026-09-25T18:00:01+00:00",
                    userId=None,
                    event_type="login_failed",
                    requestId="req-2",
                    properties={"reason": "invalid_credentials"},
                ),
            ]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2, "stored": 2, "rejected": 0}

    with Session(get_telemetry_engine()) as session:
        rows = session.exec(select(TelemetryEventRow)).all()
    assert len(rows) == 2
    by_type = {row.event_type: row for row in rows}
    assert by_type["section_viewed"].tags["path"] == "/inventory"
    assert by_type["section_viewed"].tags["eventId"] == "11111111-1111-4111-8111-111111111111"
    assert by_type["login_failed"].level == "warn"
    assert by_type["login_failed"].tags["reason"] == "invalid_credentials"


def test_telemetry_mixed_batch_partial_accept(client: TestClient) -> None:
    response = client.post(
        "/telemetry/events",
        json={
            "events": [
                _valid_event(event_type="inbound_order_created", properties={"sku": "SKU-1", "quantity": 2}),
                {"event_type": "section_viewed"},
                "not-an-object",
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"received": 3, "stored": 1, "rejected": 2}

    with Session(get_telemetry_engine()) as session:
        rows = session.exec(select(TelemetryEventRow)).all()
    assert len(rows) == 1
    assert rows[0].event_type == "inbound_order_created"


def test_telemetry_missing_events_key_is_422(client: TestClient) -> None:
    response = client.post("/telemetry/events", json={"batch": []})
    assert response.status_code == 422


def test_telemetry_get_explains_post_only(client: TestClient) -> None:
    response = client.get("/telemetry/events")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HealthCore telemetry" in response.text
    assert "POST" in response.text
