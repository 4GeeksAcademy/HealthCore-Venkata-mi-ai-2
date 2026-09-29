"""Telemetry receiver: per-event validate + bulk insert into telemetry_events."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.models.telemetry import TelemetryBatchEnvelope, TelemetryReceived
from app.telemetry.store import bulk_insert_events, validate_and_partition

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
