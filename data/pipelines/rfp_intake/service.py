"""Upload, enqueue, and read tickets. Routers call this module and do not own the graph."""

from __future__ import annotations

import logging
import os
import threading

from . import store
from .db import init_schema, reset_engine
from .errors import (
    RfpDatabaseUnconfigured,
    RfpStorageError,
    UploadRejected,
)
from .paths import MAX_PDF_BYTES, absolute_pdf_path, raw_dir, sanitize_filename
logger = logging.getLogger("healthcore.rfp")

__all__ = [
    "RfpDatabaseUnconfigured",
    "RfpStorageError",
    "UploadRejected",
    "accept_upload",
    "enqueue",
    "get_ticket",
    "init_schema",
    "list_tickets",
    "enqueue_response",
    "reprocess",
    "reset_engine",
    "start_draft",
    "stale_after_seconds",
]


def stale_after_seconds() -> int:
    raw = os.getenv("RFP_STALE_AFTER_SECONDS", "900").strip()
    try:
        return max(int(raw), 0)
    except ValueError:
        return 900


def accept_upload(filename: str, content: bytes) -> str:
    safe_name = sanitize_filename(filename)
    if not content or len(content) < 8:
        raise UploadRejected("empty")
    if len(content) > MAX_PDF_BYTES:
        raise UploadRejected("too_large")
    if not safe_name.lower().endswith(".pdf") or not content.startswith(b"%PDF"):
        raise UploadRejected("not_pdf")
    ticket_id = store.new_ticket_id()
    destination = absolute_pdf_path(ticket_id)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    except OSError as exc:
        raise RfpStorageError("rfp_pdf") from exc
    try:
        store.insert_analyzing(ticket_id=ticket_id, original_filename=safe_name)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    enqueue(ticket_id)
    return ticket_id


def enqueue(ticket_id: str) -> None:
    """Start the graph on a background thread and return without waiting."""

    def _run() -> None:
        from .runner import execute_ticket as run_ticket

        status = ""
        try:
            status = run_ticket(ticket_id)
        except Exception:
            logger.error("rfp background failed ticket_id=%s", ticket_id)
            try:
                store.mark_failed(ticket_id, "pipeline_crashed")
            except RfpStorageError:
                logger.error("rfp failed status not saved ticket_id=%s", ticket_id)
            return
        if status != "intake_complete":
            return
        try:
            from data.pipelines.rfp_response.runner import execute_response

            execute_response(ticket_id)
        except Exception:
            logger.error("rfp response failed ticket_id=%s", ticket_id)

    thread = threading.Thread(target=_run, name=f"rfp-{ticket_id[:8]}", daemon=True)
    thread.start()


def enqueue_response(ticket_id: str) -> None:
    """Draft proposal sections on a background thread and return without waiting."""

    def _run() -> None:
        from data.pipelines.rfp_response.runner import execute_response

        try:
            execute_response(ticket_id)
        except Exception:
            logger.error("rfp response failed ticket_id=%s", ticket_id)

    thread = threading.Thread(target=_run, name=f"rfp-draft-{ticket_id[:8]}", daemon=True)
    thread.start()


def start_draft(ticket_id: str) -> str:
    """Queue Part 2 for an intake-complete ticket. Returns the new status."""
    existing = store.get_ticket(ticket_id)
    if existing is None:
        raise KeyError(ticket_id)
    if existing.status != "intake_complete" or not existing.handoff_ready:
        raise ValueError("not_draftable")
    if not store.set_response_status(ticket_id, "drafting"):
        raise ValueError("not_draftable")
    enqueue_response(ticket_id)
    return "drafting"


def list_tickets() -> list[dict]:
    return store.list_tickets(stale_after_seconds=stale_after_seconds())


def get_ticket(ticket_id: str) -> dict | None:
    return store.ticket_view(ticket_id, stale_after_seconds=stale_after_seconds())


def reprocess(ticket_id: str) -> str:
    """Queue another run for a discarded or failed ticket. Returns the new status."""
    existing = store.get_ticket(ticket_id)
    if existing is None:
        raise KeyError(ticket_id)
    if existing.status not in {"failed", "discarded"}:
        raise ValueError("not_reprocessable")
    if not store.reset_for_reprocess(ticket_id):
        raise ValueError("not_reprocessable")
    enqueue(ticket_id)
    return "analyzing"


def raw_directory() -> str:
    path = raw_dir()
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
