"""FastAPI routes for the business performance pipeline."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.deps.auth import get_current_user

router = APIRouter(prefix="/reporting", tags=["reporting"])


def _pipelines_root() -> Path:
    # services/reporting/router.py -> repo root
    return Path(__file__).resolve().parents[2]


def _ensure_pipeline_imports() -> None:
    root = str(_pipelines_root())
    pipelines = str(_pipelines_root() / "data" / "pipelines")
    for location in (root, pipelines):
        if location not in sys.path:
            sys.path.insert(0, location)


def _latest_pipeline_run() -> Any:
    _ensure_pipeline_imports()
    module = importlib.import_module("monthly_clinic_supply.runs")
    return module.latest_pipeline_run()


def _trigger_flow(month_start: str | None) -> dict[str, Any]:
    _ensure_pipeline_imports()
    module = importlib.import_module("monthly_clinic_supply.flow")
    return module.trigger_monthly_clinic_supply_performance(month_start=month_start)


def _query_kpis(month_start: str | None) -> dict[str, Any]:
    _ensure_pipeline_imports()
    module = importlib.import_module("monthly_clinic_supply.query")
    return module.query_monthly_clinic_supply_performance(month_start=month_start)


class PipelineTriggerBody(BaseModel):
    month_start: str | None = None


class ClinicRow(BaseModel):
    clinic_id: str
    country: str
    total_supply_cost: float
    supply_consumption_count: int
    critical_stockout_count: int
    expiry_risk_count: int
    currency: str


class MonthlyResponse(BaseModel):
    month_start: str
    clinics: list[ClinicRow] = Field(default_factory=list)


@router.get("/pipeline-runs/latest")
def get_latest_pipeline_run(_user: dict = Depends(get_current_user)) -> dict[str, Any]:
    row = _latest_pipeline_run()
    if row is None:
        return {
            "status": "none",
            "started_at": None,
            "ended_at": None,
            "records_extracted": 0,
            "records_loaded": 0,
            "error_message": None,
        }
    return {
        "run_id": row.get("run_id"),
        "status": row.get("status"),
        "phase": row.get("phase"),
        "month_start": row.get("month_start"),
        "started_at": row.get("started_at"),
        "ended_at": row.get("ended_at"),
        "records_extracted": row.get("records_extracted", 0),
        "records_deduped": row.get("records_deduped", 0),
        "records_rejected": row.get("records_rejected", 0),
        "records_loaded": row.get("records_loaded", 0),
        "error_message": row.get("error_message"),
        "source": row.get("source"),
    }


@router.post("/pipeline-runs", status_code=status.HTTP_200_OK)
def post_pipeline_run(
    body: PipelineTriggerBody | None = None,
    _user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    month_start = body.month_start if body else None
    try:
        return _trigger_flow(month_start)
    except RuntimeError as exc:
        if str(exc) == "pipeline_already_running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pipeline run is already in progress for that month.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to run the reporting pipeline.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to run the reporting pipeline.",
        ) from exc


@router.get(
    "/monthly-clinic-supply-performance",
    response_model=MonthlyResponse,
)
def get_monthly_clinic_supply_performance(
    month_start: str | None = Query(default=None),
    _user: dict = Depends(get_current_user),
) -> MonthlyResponse:
    try:
        payload = _query_kpis(month_start)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to read monthly clinic supply performance.",
        ) from exc
    return MonthlyResponse.model_validate(payload)
