"""Celery task wrapping the monthly clinic-supply reporting pipeline."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

from celery.exceptions import MaxRetriesExceededError

from services.celery_app import celery_app
from services.tasks.dlq import init_dlq_schema, record_dead_letter

logger = logging.getLogger("healthcore.tasks.pipeline")

TASK_NAME = "healthcore.run_monthly_clinic_supply_pipeline"


def retry_countdown(retries: int) -> int:
    """Exponential backoff seconds — never zero (no immediate retry)."""
    return max(2 ** int(retries or 0), 1)


def _ensure_pipeline_imports() -> None:
    repo = Path(__file__).resolve().parents[2]
    pipelines = repo / "data" / "pipelines"
    for location in (str(repo), str(pipelines), str(repo / "services")):
        if location not in sys.path:
            sys.path.insert(0, location)


def _run_pipeline(month_start: str | None) -> dict[str, Any]:
    _ensure_pipeline_imports()
    from monthly_clinic_supply.flow import (  # noqa: WPS433
        trigger_monthly_clinic_supply_performance,
    )

    return trigger_monthly_clinic_supply_performance(month_start=month_start)


@celery_app.task(
    bind=True,
    name=TASK_NAME,
    max_retries=3,
    soft_time_limit=300,
    time_limit=360,
)
def run_monthly_clinic_supply_pipeline(
    self,
    month_start: str | None = None,
) -> dict[str, Any]:
    """Execute Prefect ETL off the API request thread.

    Message body carries only ``month_start`` (identifier). The worker loads
    telemetry / fixture data itself — never large payloads in Redis.
    """
    init_dlq_schema()
    task_id = self.request.id or "unknown"
    attempt = int(self.request.retries or 0) + 1
    started = time.monotonic()
    logger.info(
        "task_start task_id=%s attempt=%s month_start=%s",
        task_id,
        attempt,
        month_start,
    )
    try:
        result = _run_pipeline(month_start)
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.info(
            "task_done task_id=%s attempt=%s status=success duration_ms=%s",
            task_id,
            attempt,
            duration_ms,
        )
        return {
            "month_start": result.get("month_start"),
            "status": result.get("status"),
            "records_loaded": result.get("records_loaded"),
            "run_id": result.get("run_id"),
        }
    except MaxRetriesExceededError:
        raise
    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.error(
            "task_fail task_id=%s attempt=%s status=failure duration_ms=%s error=%s",
            task_id,
            attempt,
            duration_ms,
            exc,
            exc_info=True,
        )
        countdown = retry_countdown(self.request.retries or 0)
        try:
            raise self.retry(exc=exc, countdown=countdown) from exc
        except MaxRetriesExceededError:
            record_dead_letter(
                task_id=task_id,
                attempt=attempt,
                error_message=str(exc),
            )
            raise exc from exc
