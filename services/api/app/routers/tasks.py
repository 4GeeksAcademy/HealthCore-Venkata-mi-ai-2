"""Task status polling — Ticket #DEV-55."""

from __future__ import annotations

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status

from app.celery_client import get_celery_app
from app.deps.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

_STATUS_MAP = {
    "PENDING": "pending",
    "RECEIVED": "pending",
    "STARTED": "started",
    "RETRY": "started",
    "SUCCESS": "success",
    "FAILURE": "failure",
    "REVOKED": "failure",
}


def map_celery_status(state: str) -> str:
    return _STATUS_MAP.get((state or "PENDING").upper(), "pending")


@router.get("/{task_id}")
def get_task_status(
    task_id: str,
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    if not task_id or len(task_id) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task_id.",
        )
    app = get_celery_app()
    async_result = AsyncResult(task_id, app=app)
    mapped = map_celery_status(async_result.state)
    payload: dict[str, Any] = {
        "task_id": task_id,
        "status": mapped,
        "result": None,
    }
    if mapped == "success":
        payload["result"] = async_result.result
    elif mapped == "failure":
        err = async_result.result
        payload["result"] = {"error": str(err) if err is not None else "task failed"}
    return payload
