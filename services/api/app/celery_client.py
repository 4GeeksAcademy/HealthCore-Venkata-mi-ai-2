"""Celery client for the FastAPI process (enqueue + status only)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from celery import Celery

_app: Celery | None = None


def redis_url() -> str:
    return (os.environ.get("REDIS_URL") or "redis://127.0.0.1:6379/0").strip()


def _ensure_repo_paths() -> None:
    # services/api/app/celery_client.py -> repo root
    repo = Path(__file__).resolve().parents[3]
    services = repo / "services"
    for location in (str(repo), str(services)):
        if location not in sys.path:
            sys.path.insert(0, location)


def get_celery_app() -> Celery:
    """Prefer the shared ``services.celery_app`` so task names match the worker."""
    global _app
    if _app is None:
        _ensure_repo_paths()
        try:
            from services.celery_app import celery_app as shared

            _app = shared
        except ImportError:
            _app = Celery(
                "healthcore",
                broker=redis_url(),
                backend=redis_url(),
            )
            _app.conf.update(
                task_serializer="json",
                accept_content=["json"],
                result_serializer="json",
                task_track_started=True,
            )
    return _app


def reset_celery_app() -> None:
    global _app
    _app = None
