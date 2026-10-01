"""Telemetry receiver and operational report."""

from __future__ import annotations

import importlib
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.core.errors import StorageError
from app.core.ttl_cache import TtlCache
from app.models.telemetry import TelemetryBatchEnvelope, TelemetryReceived, TelemetryReport
from app.telemetry.store import bulk_insert_events, get_telemetry_engine, validate_and_partition

REPORT_TTL_SECONDS = 60
report_cache = TtlCache()

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
logger = logging.getLogger("api.telemetry")


@router.get("/events", response_class=HTMLResponse)
def describe_events() -> HTMLResponse:
    """Browser address-bar visits are GET. Return HTML so the page is visible."""
    _configured_endpoint = get_settings().telemetry_endpoint
    logger.info("telemetry sink inspected endpoint_configured=%s", bool(_configured_endpoint))
    page = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>HealthCore telemetry</title>
</head>
<body style="margin:0;background:#f5f2ea;color:#1f2a2e;font-family:Segoe UI,sans-serif;">
  <main style="max-width:40rem;margin:3rem auto;padding:1.5rem;background:#fffdf8;border:1px solid #d9d0c2;">
    <h1>HealthCore telemetry</h1>
    <p>This address accepts <strong>POST</strong> with a JSON body <code>{"events":[...]}</code>.</p>
    <p>Opening it in the browser sends GET and does not record events.</p>
    <p>Valid events are stored in Supabase <code>telemetry_events</code>. The response is
       <code>{"received": N, "stored": M, "rejected": R}</code>.</p>
  </main>
</body>
</html>
"""
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


@router.post("/events", response_model=TelemetryReceived)
def receive_events(payload: TelemetryBatchEnvelope) -> TelemetryReceived:
    received = len(payload.events)
    rows, rejected = validate_and_partition(payload.events)
    types = [row.event_type for row in rows]
    stored = bulk_insert_events(rows)
    logger.info(
        "telemetry batch received=%s stored=%s rejected=%s types=%s",
        received,
        stored,
        rejected,
        types,
    )
    return TelemetryReceived(received=received, stored=stored, rejected=rejected)


def _analysis_module() -> Any:
    mounted = Path("/opt/healthcore-telemetry")
    local = Path(__file__).resolve().parents[3] / "telemetry"
    directory = mounted if (mounted / "analysis.py").is_file() else local
    location = str(directory)
    if location not in sys.path:
        sys.path.insert(0, location)
    return importlib.import_module("analysis")


def _parse_bound(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid request. Please check the submitted data.",
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@router.get("/report", response_model=TelemetryReport)
def telemetry_report(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> TelemetryReport:
    """Serve cached operational metrics. The date window is resolved once here."""
    if end_date is None:
        end = datetime.now(timezone.utc)
    else:
        end = _parse_bound(end_date)
    if start_date is None:
        start = end - timedelta(days=7)
    else:
        start = _parse_bound(start_date)
    if start >= end:
        raise HTTPException(
            status_code=422,
            detail="Invalid request. Please check the submitted data.",
        )

    cache_key = f"telemetry:report:{start.isoformat()}:{end.isoformat()}"
    cached = report_cache.get(cache_key)
    if isinstance(cached, dict):
        return TelemetryReport.model_validate(cached)

    analysis = _analysis_module()
    engine = get_telemetry_engine()
    try:
        metrics = {
            "events_per_day": analysis.events_per_day(engine, start, end),
            "error_rate_by_type": analysis.error_rate_by_type(engine, start, end),
            "latency_per_day": analysis.latency_per_day(engine, start, end),
            "auth_failure_rate": analysis.auth_failure_rate(engine, start, end),
        }
    except analysis.ReportQueryError as exc:
        raise StorageError("Unable to access telemetry data store") from exc

    payload = {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "metrics": metrics,
    }
    report_cache.set(cache_key, payload, REPORT_TTL_SECONDS)
    return TelemetryReport.model_validate(payload)
