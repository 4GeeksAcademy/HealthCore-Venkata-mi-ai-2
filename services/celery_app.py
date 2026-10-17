"""Celery application — Redis broker and result backend (Ticket #DEV-55)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from celery import Celery

_SERVICES = Path(__file__).resolve().parent
_REPO = _SERVICES.parent
for location in (
    str(_REPO),
    str(_SERVICES),
    str(_REPO / "data" / "pipelines"),
):
    if location not in sys.path:
        sys.path.insert(0, location)


def redis_url() -> str:
    return (os.environ.get("REDIS_URL") or "redis://127.0.0.1:6379/0").strip()


celery_app = Celery(
    "healthcore",
    broker=redis_url(),
    backend=redis_url(),
    include=["services.tasks.pipeline", "services.tasks.demo"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=86400,
)
