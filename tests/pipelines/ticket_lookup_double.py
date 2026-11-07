"""Test double for the old direct ticket client.

The agent does not import this module. Graph mechanics tests inject it so they
can simulate a ticket result without a second production path to the Incidents
Manager.
"""

from __future__ import annotations

import time
from urllib.parse import urlencode

from pydantic import ValidationError

from services.knowledge_agent.tools.contracts import TicketLookupInput, TicketLookupOutput, TicketRecord
from services.knowledge_agent.tools.session import ReadOnlyApiSession, ServiceCredentials, ToolCallError

TOOL_NAME = "ticket_lookup"
INCIDENTS_PATH = "/api/incidents"


class TicketLookupTool:
    """GET one ticket or a filtered list. Tests only."""

    name = TOOL_NAME

    def __init__(self, session: ReadOnlyApiSession | None) -> None:
        self.session = session

    @classmethod
    def from_env(cls) -> TicketLookupTool:
        credentials = ServiceCredentials.from_env()
        return cls(ReadOnlyApiSession(credentials) if credentials else None)

    def __call__(self, request: TicketLookupInput) -> TicketLookupOutput:
        if request.ticket_id:
            path, params = f"{INCIDENTS_PATH}/{request.ticket_id}", None
        else:
            params = {
                key: value
                for key, value in (
                    ("status", request.status),
                    ("category", request.category),
                    ("clinic_id", request.clinic_id),
                    ("limit", request.limit),
                )
                if value is not None
            }
            path = INCIDENTS_PATH
        endpoint = f"{path}?{urlencode(params)}" if params else path
        if self.session is None:
            return TicketLookupOutput(status="auth_failed", endpoint=endpoint)

        started = time.perf_counter()

        def elapsed() -> float:
            return round((time.perf_counter() - started) * 1000, 1)

        try:
            body, http_status = self.session.get_json(path, params)
        except ToolCallError as exc:
            return TicketLookupOutput(
                status=exc.status, http_status=exc.http_status, latency_ms=elapsed(), endpoint=endpoint
            )
        try:
            if request.ticket_id:
                tickets, total = (TicketRecord.model_validate(body),), 1
            else:
                tickets = tuple(TicketRecord.model_validate(item) for item in body["items"])
                total = int(body["total"])
        except (ValidationError, KeyError, TypeError, ValueError):
            return TicketLookupOutput(
                status="bad_response", http_status=http_status, latency_ms=elapsed(), endpoint=endpoint
            )
        return TicketLookupOutput(
            status="ok",
            tickets=tickets,
            total=total,
            http_status=http_status,
            latency_ms=elapsed(),
            endpoint=endpoint,
        )
