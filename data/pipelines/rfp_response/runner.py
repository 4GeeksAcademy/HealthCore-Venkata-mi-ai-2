"""Run Part 2 for one ticket. A crash keeps the ticket for a person to review."""

from __future__ import annotations

import logging

from data.pipelines.rfp_intake.errors import RfpStorageError
from data.pipelines.rfp_intake import store

from .graph import ResponseDeps, build_graph, initial_state

logger = logging.getLogger("healthcore.rfp")


def execute_response(ticket_id: str, *, deps: ResponseDeps | None = None) -> str:
    """Draft and evaluate one intake-complete ticket. Returns the status written."""
    try:
        compiled = build_graph(deps)
        result = compiled.invoke(initial_state(ticket_id))
        status = str(result.get("final_status") or "")
        if status in {"under_evaluation", "needs_human_review"}:
            return status
        store.mark_response_needs_review(ticket_id)
        return "needs_human_review"
    except ValueError:
        logger.error("rfp response skipped ticket_id=%s", ticket_id)
        current = store.get_ticket(ticket_id)
        return current.status if current is not None else "skipped"
    except Exception as exc:
        logger.error(
            "rfp response failed ticket_id=%s error_type=%s",
            ticket_id,
            type(exc).__name__,
        )
        try:
            store.mark_response_needs_review(ticket_id)
        except RfpStorageError:
            logger.error("rfp response status not saved ticket_id=%s", ticket_id)
        return "needs_human_review"
