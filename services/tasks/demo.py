"""Demo tasks for Flower / ops verification (not used by production API routes)."""

from __future__ import annotations

from celery.exceptions import MaxRetriesExceededError

from services.celery_app import celery_app
from services.tasks.dlq import record_dead_letter
from services.tasks.pipeline import retry_countdown

DEMO_FAIL_NAME = "healthcore.demo_fail"


@celery_app.task(bind=True, name=DEMO_FAIL_NAME, max_retries=3)
def demo_fail(self, reason: str = "demo failure for Flower") -> None:
    """Always fails — used to show a FAILURE row in Flower during demos."""
    task_id = self.request.id or "unknown"
    attempt = int(self.request.retries or 0) + 1
    exc = RuntimeError(reason)
    try:
        raise self.retry(exc=exc, countdown=retry_countdown(self.request.retries or 0))
    except MaxRetriesExceededError:
        record_dead_letter(task_id=task_id, attempt=attempt, error_message=str(exc))
        raise exc from exc
