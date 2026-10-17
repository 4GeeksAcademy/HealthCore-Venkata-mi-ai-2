"""Reporting API routes for the monthly clinic supply pipeline."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[3]
PIPELINES = REPO / "data" / "pipelines"
SERVICES = REPO / "services"


@pytest.fixture
def reporting_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "reporting.db"
    monkeypatch.setenv("REPORTING_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("TELEMETRY_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("JOB_RUNS_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    for location in (str(REPO), str(PIPELINES), str(SERVICES)):
        if location not in sys.path:
            sys.path.insert(0, location)

    from app.celery_client import reset_celery_app
    from monthly_clinic_supply.db import reset_engine
    from services.celery_app import celery_app
    from services.job_runner.db import reset_job_engine

    reset_celery_app()
    reset_engine()
    reset_job_engine()
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    celery_app.conf.task_store_eager_result = True
    celery_app.conf.result_backend = "cache+memory://"
    yield db_path
    reset_engine()
    reset_job_engine()
    reset_celery_app()
    celery_app.conf.task_always_eager = False


def test_reporting_endpoints_require_auth(client: TestClient, reporting_db) -> None:
    assert client.get("/reporting/pipeline-runs/latest").status_code == 401
    assert client.post("/reporting/pipeline-runs", json={}).status_code == 401
    assert client.get("/reporting/monthly-clinic-supply-performance").status_code == 401
    assert client.get("/tasks/fake-id").status_code == 401


def test_reporting_enqueue_returns_202_under_200ms(
    client: TestClient,
    auth_headers: dict,
    reporting_db,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTTP path only enqueues — mock broker so we measure API latency, not ETL."""
    from services.tasks.pipeline import run_monthly_clinic_supply_pipeline

    class _FakeAsyncResult:
        id = "demo-task-id-001"

    monkeypatch.setattr(
        run_monthly_clinic_supply_pipeline,
        "apply_async",
        lambda *args, **kwargs: _FakeAsyncResult(),
    )

    started = time.perf_counter()
    triggered = client.post(
        "/reporting/pipeline-runs",
        headers=auth_headers,
        json={"month_start": "2026-09-01"},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert triggered.status_code == 202, triggered.text
    assert triggered.json() == {"task_id": "demo-task-id-001"}
    assert elapsed_ms < 200


def test_reporting_task_completes_and_query(
    client: TestClient, auth_headers: dict, reporting_db
) -> None:
    from services.tasks.pipeline import run_monthly_clinic_supply_pipeline

    async_result = run_monthly_clinic_supply_pipeline.apply(
        kwargs={"month_start": "2026-09-01"}
    )
    assert async_result.successful()
    body = async_result.result
    assert body["month_start"] == "2026-09-01"
    assert body["records_loaded"] == 10

    status_resp = client.get(f"/tasks/{async_result.id}", headers=auth_headers)
    assert status_resp.status_code == 200
    status_body = status_resp.json()
    assert status_body["task_id"] == async_result.id
    assert status_body["status"] == "success"
    assert status_body["result"]["records_loaded"] == 10

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
