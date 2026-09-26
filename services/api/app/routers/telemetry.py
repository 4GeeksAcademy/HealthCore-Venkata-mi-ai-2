"""Temporary telemetry receiver. Validates the envelope and does not persist."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.core.config import get_settings
from app.models.telemetry import TelemetryBatch, TelemetryReceived

router = APIRouter(prefix="/telemetry", tags=["telemetry"])
logger = logging.getLogger("api.telemetry")


@router.get("/events", response_class=HTMLResponse)
def describe_events() -> HTMLResponse:
    """Browser address-bar visits are GET. Return HTML so the page is visible."""
    _configured_endpoint = get_settings().telemetry_endpoint
    logger.info("telemetry stub inspected endpoint_configured=%s", bool(_configured_endpoint))
    page = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>HealthCore telemetry stub</title>
</head>
<body style="margin:0;background:#f5f2ea;color:#1f2a2e;font-family:Segoe UI,sans-serif;">
  <main style="max-width:40rem;margin:3rem auto;padding:1.5rem;background:#fffdf8;border:1px solid #d9d0c2;">
    <h1>HealthCore telemetry stub</h1>
    <p>This address accepts <strong>POST</strong> with a JSON body <code>{"events":[...]}</code>.</p>
    <p>Opening it in the browser sends GET and does not record events.</p>
    <p>Use the backoffice, then look for <code>telemetry/events</code> in DevTools, Network tab. A batch returns <code>{"received": N}</code>.</p>
  </main>
</body>
</html>
"""
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


@router.post("/events", response_model=TelemetryReceived)
def receive_events(payload: TelemetryBatch) -> TelemetryReceived:
    # Pattern for the later sink. This stub does not forward or store the batch.
    _configured_endpoint = get_settings().telemetry_endpoint
    types = [event.event_type for event in payload.events]
    logger.info(
        "telemetry batch received=%s types=%s endpoint_configured=%s",
        len(types),
        types,
        bool(_configured_endpoint),
    )
    return TelemetryReceived(received=len(payload.events))
