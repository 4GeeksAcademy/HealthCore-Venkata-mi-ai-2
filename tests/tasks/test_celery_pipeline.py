"""Unit tests for Celery pipeline task, retries, and DLQ (Ticket #DEV-55)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SERVICES = REPO / "services"
API = SERVICES / "api"


@pytest.fixture
def celery_env(tmp_path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "jobs.db"
    monkeypatch.setenv("JOB_RUNS_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    for location in (
        str(REPO),
        str(SERVICES),
        str(API),
        str(REPO / "data" / "pipelines"),
    ):
        if location not in sys.path:
            sys.path.insert(0, location)

    from services.celery_app import celery_app
    from services.job_runner.db import reset_job_engine
    from services.tasks.dlq import init_dlq_schema

    reset_job_engine()
    init_dlq_schema()
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    celery_app.conf.task_store_eager_result = True
    celery_app.conf.result_backend = "cache+memory://"
    yield celery_app
    celery_app.conf.task_always_eager = False
    reset_job_engine()


def test_task_message_is_month_start_only() -> None:
    from services.tasks.pipeline import TASK_NAME, run_monthly_clinic_supply_pipeline

    assert TASK_NAME == "healthcore.run_monthly_clinic_supply_pipeline"
    names = set(run_monthly_clinic_supply_pipeline.run.__code__.co_varnames)
    assert "month_start" in names
    assert "events" not in names
    assert "payload" not in names


def test_retry_backoff_is_exponential_and_non_zero() -> None:
    from services.tasks.pipeline import retry_countdown, run_monthly_clinic_supply_pipeline

    assert run_monthly_clinic_supply_pipeline.max_retries == 3
    assert retry_countdown(0) == 1
    assert retry_countdown(1) == 2
    assert retry_countdown(2) == 4
    assert retry_countdown(0) >= 1
    assert retry_countdown(1) > retry_countdown(0)


def test_dlq_recorded_after_retries_exhausted(
    celery_env, monkeypatch: pytest.MonkeyPatch
):
    from celery.exceptions import MaxRetriesExceededError

    from services.tasks import pipeline as pipeline_mod
    from services.tasks.dlq import list_dead_letters

    monkeypatch.setattr(
        pipeline_mod,
        "_run_pipeline",
        lambda month_start=None: (_ for _ in ()).throw(RuntimeError("always fail")),
    )

    task = pipeline_mod.run_monthly_clinic_supply_pipeline

    def exhausted_retry(self, exc=None, countdown=None, **kwargs):
        raise MaxRetriesExceededError("retries exhausted")

    monkeypatch.setattr(task, "retry", exhausted_retry.__get__(task, type(task)))

    # Simulate the final attempt (retries already at max).
    with pytest.raises(RuntimeError, match="always fail"):
        task.apply(
            kwargs={"month_start": "2026-09-01"},
            throw=True,
        ).get(propagate=True)

    rows = list_dead_letters()
    assert len(rows) >= 1
    assert rows[0]["attempt"] >= 1
    assert "always fail" in rows[0]["error_message"]
    assert rows[0]["task_id"]


def test_status_mapping_helpers(celery_env) -> None:
    from app.routers.tasks import map_celery_status

    assert map_celery_status("PENDING") == "pending"
    assert map_celery_status("STARTED") == "started"
    assert map_celery_status("SUCCESS") == "success"
    assert map_celery_status("FAILURE") == "failure"
