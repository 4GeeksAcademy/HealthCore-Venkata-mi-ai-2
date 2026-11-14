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

IncidentStatus = Literal["open", "in_progress", "resolved", "discarded"]
IncidentCategory = Literal[
    "clinical_equipment",
    "it_system",
    "billing_error",
    "compliance_breach",
    "patient_experience",
    "staff_issue",
    "facility_issue",
    "referral_issue",
    "other",
]
IncidentOrigin = Literal["customer", "branch", "internal"]
IncidentBranch = Literal[
    "central",
    "austin_north",
    "dallas_uptown",
    "houston_med_center",
    "san_antonio_west",
    "miami_brickell",
    "miami_doral",
    "orlando_east",
    "tampa_bay",
    "atlanta_midtown",
    "savannah",
    "london_city",
    "london_west",
    "manchester_central",
]


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TicketLookupInput(_Contract):
    """One ticket by id, or a filtered search. At least one of the two."""

    ticket_id: str | None = Field(default=None, min_length=8, max_length=80)
    status: IncidentStatus | None = None
    category: IncidentCategory | None = None
    branch: IncidentBranch | None = None
    limit: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def _id_or_filter(self) -> TicketLookupInput:
        if self.ticket_id is None and not (self.status or self.category or self.branch):
            raise ValueError("a ticket_id or at least one filter is required")
        return self


class TicketRecord(_Contract):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str
    title: str = ""
    description: str = ""
    category: IncidentCategory
    status: IncidentStatus
    origin: IncidentOrigin = "customer"
    branch: IncidentBranch
    created_at: str = ""
    updated_at: str = ""


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
