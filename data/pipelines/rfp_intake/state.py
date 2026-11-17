"""Graph state. ``section_results`` accumulates the parallel workers."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class RfpState(TypedDict, total=False):
    ticket_id: str
    markdown: str
    redacted_markdown: str
    readability: dict[str, Any]
    is_rfp: bool
    discard_reason_code: str
    phi_detected: bool
    metadata: dict[str, Any]
    unknown_departments: list[str]
    work_items: list[dict[str, Any]]
    work_item: dict[str, Any]
    section_results: Annotated[list[dict[str, Any]], operator.add]
    conflicts: list[dict[str, Any]]
    sales_summary: str
    summary_source: str
    handoff: dict[str, Any]
    status: str
    _ordered_sections: list[dict[str, Any]]
