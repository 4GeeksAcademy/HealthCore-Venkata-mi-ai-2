"""Reporting API routes for the monthly clinic supply pipeline."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[3]
PIPELINES = REPO / "data" / "pipelines"


@pytest.fixture
def reporting_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "reporting.db"
    monkeypatch.setenv("REPORTING_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("TELEMETRY_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    for location in (str(REPO), str(PIPELINES), str(REPO / "services")):
        if location not in sys.path:
            sys.path.insert(0, location)
    from monthly_clinic_supply.db import reset_engine

    reset_engine()
    yield db_path
    reset_engine()


def test_reporting_endpoints_require_auth(client: TestClient, reporting_db) -> None:
    assert client.get("/reporting/pipeline-runs/latest").status_code == 401
    assert client.post("/reporting/pipeline-runs", json={}).status_code == 401
    assert client.get("/reporting/monthly-clinic-supply-performance").status_code == 401


def test_reporting_trigger_and_query(
    client: TestClient, auth_headers: dict, reporting_db
) -> None:
    triggered = client.post(
        "/reporting/pipeline-runs",
        headers=auth_headers,
        json={"month_start": "2026-09-01"},
    )
    assert triggered.status_code == 200, triggered.text
    body = triggered.json()
    assert body["status"] == "Completed"
    assert body["records_loaded"] == 10
    assert body["month_start"] == "2026-09-01"

    latest = client.get("/reporting/pipeline-runs/latest", headers=auth_headers)
    assert latest.status_code == 200
    meta = latest.json()
    assert meta["status"] == "Completed"
    assert meta["records_loaded"] == 10
    assert meta["started_at"]
    assert meta["ended_at"]

    kpis = client.get(
        "/reporting/monthly-clinic-supply-performance",
        headers=auth_headers,
        params={"month_start": "2026-09-01"},
    )
    assert kpis.status_code == 200
    payload = kpis.json()
    assert payload["month_start"] == "2026-09-01"
    assert len(payload["clinics"]) == 10
    austin = next(row for row in payload["clinics"] if row["clinic_id"] == "us-tx-001")
    assert austin["total_supply_cost"] == 320.5
    assert austin["supply_consumption_count"] == 2
    assert austin["critical_stockout_count"] == 1
    assert austin["currency"] == "USD"
