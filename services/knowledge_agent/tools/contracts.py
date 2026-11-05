"""Typed input/output contracts for the agent's external tools.

Output fields mirror what the HealthCore API exposes (``IncidentRecord`` and
``MedicalSupplyResponse``). Every expected failure is a ``status`` value, so a
tool call always returns one of these models instead of raising.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ToolStatus = Literal[
    "ok",
    "not_found",
    "invalid_input",
    "timeout",
    "unavailable",
    "auth_failed",
    "bad_response",
]

IncidentStatus = Literal["open", "closed", "discarded"]
IncidentCategory = Literal["APPOINTMENT", "BILLING", "CLINICAL", "FACILITIES", "IT", "WORKFORCE"]

TICKET_ID_PATTERN = r"^INC-\d{4,6}$"


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TicketLookupInput(_Contract):
    """One ticket by id, or a filtered search. At least one of the two."""

    ticket_id: str | None = Field(default=None, pattern=TICKET_ID_PATTERN)
    status: IncidentStatus | None = None
    category: IncidentCategory | None = None
    clinic_id: str | None = Field(default=None, min_length=3, max_length=40)
    limit: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def _id_or_filter(self) -> TicketLookupInput:
        if self.ticket_id is None and not (self.status or self.category or self.clinic_id):
            raise ValueError("a ticket_id or at least one filter is required")
        return self


class TicketRecord(_Contract):
    model_config = ConfigDict(extra="ignore", frozen=True)

    incident_id: str
    clinic_id: str
    country: str
    category: IncidentCategory
    status: IncidentStatus
    satisfaction_score: float | None = None
    source_file: str = ""
    first_recorded_at: str
    updated_at: str


class TicketLookupOutput(_Contract):
    status: ToolStatus
    tickets: tuple[TicketRecord, ...] = ()
    total: int = 0
    http_status: int | None = None
    latency_ms: float = 0.0
    endpoint: str = ""


class InventoryLookupInput(_Contract):
    product_query: str = Field(min_length=2, max_length=80)


class ProductStock(_Contract):
    name: str
    sku: str
    category: str
    current_stock: int
    threshold: int
    below_threshold: bool


class InventoryLookupOutput(_Contract):
    status: ToolStatus
    products: tuple[ProductStock, ...] = ()
    http_status: int | None = None
    latency_ms: float = 0.0
    endpoint: str = ""
