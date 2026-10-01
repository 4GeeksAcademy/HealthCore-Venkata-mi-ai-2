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


def _event(event_type: str, stamp: str, **properties: object) -> dict:
    return {
        "eventId": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "timestamp": stamp,
        "sessionId": "sess-report",
        "userId": "1",
        "event_type": event_type,
        "schemaVersion": "1.0.0",
        "requestId": "req-report",
        "properties": properties,
    }


def test_telemetry_report_groups_operational_metrics(client: TestClient) -> None:
    day = "2026-09-28T12:00:00+00:00"
    later = "2026-09-28T12:05:00+00:00"
    response = client.post(
        "/telemetry/events",
        json={
            "events": [
                _event("section_viewed", day, path="/inventory"),
                _event("login_failed", day, reason="invalid_credentials"),
                _event("login_succeeded", later, role="staff"),
                _event("api_request_failed", later, route_template="/inventory/products", status_code=500),
                _event("api_latency_recorded", later, method="GET", route_template="/inventory/products", status_code=200, duration_ms=40, cache_status="miss"),
                _event("api_latency_recorded", later, method="GET", route_template="/inventory/products", status_code=200, duration_ms=60, cache_status="hit"),
            ]
        },
    )
    assert response.status_code == 200

    report = client.get(
        "/telemetry/report",
        params={"start_date": "2026-09-28T00:00:00+00:00", "end_date": "2026-09-29T00:00:00+00:00"},
    )
    assert report.status_code == 200
    body = report.json()
    assert body["period"]["from"].startswith("2026-09-28")
    assert set(body["metrics"]) == {
        "events_per_day",
        "error_rate_by_type",
        "latency_per_day",
        "auth_failure_rate",
    }
    volume = {row["event_type"]: row["event_count"] for row in body["metrics"]["events_per_day"]}
    assert volume["login_failed"] == 1
    assert volume["api_latency_recorded"] == 2
    rates = {row["event_type"]: row["error_rate"] for row in body["metrics"]["error_rate_by_type"]}
    assert rates["api_request_failed"] == 1
    assert rates["section_viewed"] == 0
    assert body["metrics"]["latency_per_day"][0]["mean_duration_ms"] == 50
    auth = body["metrics"]["auth_failure_rate"][0]
    assert auth["failed"] == 1
    assert auth["succeeded"] == 1
    assert auth["failure_rate"] == 0.5


def test_telemetry_report_uses_cache(client: TestClient, monkeypatch) -> None:
    import app.routers.telemetry as telemetry_router

    calls = {"n": 0}
    analysis = telemetry_router._analysis_module()
    original = analysis.events_per_day

    def counted(engine, start_date, end_date):
        calls["n"] += 1
        return original(engine, start_date, end_date)

    monkeypatch.setattr(analysis, "events_per_day", counted)
    params = {"start_date": "2026-09-01T00:00:00+00:00", "end_date": "2026-09-02T00:00:00+00:00"}
    first = client.get("/telemetry/report", params=params)
    second = client.get("/telemetry/report", params=params)
    assert first.status_code == 200
    assert second.json() == first.json()
    assert calls["n"] == 1


def test_telemetry_report_rejects_bad_window(client: TestClient) -> None:
    response = client.get(
        "/telemetry/report",
        params={"start_date": "2026-09-02T00:00:00+00:00", "end_date": "2026-09-01T00:00:00+00:00"},
    )
    assert response.status_code == 422


def test_telemetry_get_explains_post_only(client: TestClient) -> None:
    response = client.get("/telemetry/events")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "HealthCore telemetry" in response.text
    assert "POST" in response.text
