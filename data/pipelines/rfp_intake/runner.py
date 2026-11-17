"""Run one ticket to a terminal status. Exceptions become a failed ticket."""

from __future__ import annotations

import logging

from .errors import ConversionError, ModelUnavailable, RfpStorageError
from .graph import RfpDeps, build_graph, initial_state
from . import store

logger = logging.getLogger("healthcore.rfp")


def _failure_code(exc: Exception) -> str:
    if isinstance(exc, ConversionError):
        return "conversion_failed"
    if isinstance(exc, ModelUnavailable) and exc.code in {
        "classifier_unavailable",
        "worker_unavailable",
    }:
        return exc.code
    if isinstance(exc, ModelUnavailable):
        return "classifier_unavailable"
    if isinstance(exc, RfpStorageError):
        return "storage_failed"
    return "pipeline_crashed"


def execute_ticket(ticket_id: str, *, deps: RfpDeps | None = None) -> str:
    """Run the intake graph. Returns the status written on the ticket."""
    try:
        store.touch(ticket_id)
        compiled = build_graph(deps)
        result = compiled.invoke(initial_state(ticket_id))
        status = str(result.get("status") or "")
        if status in {"discarded", "intake_complete"}:
            return status
        store.mark_failed(ticket_id, "pipeline_crashed")
        return "failed"
    except Exception as exc:
        code = _failure_code(exc)
        logger.error(
            "rfp intake failed ticket_id=%s error_type=%s code=%s",
            ticket_id,
            type(exc).__name__,
            code,
        )
        try:
            store.mark_failed(ticket_id, code)
        except RfpStorageError:
            logger.error("rfp failed status not saved ticket_id=%s", ticket_id)
        return "failed"
