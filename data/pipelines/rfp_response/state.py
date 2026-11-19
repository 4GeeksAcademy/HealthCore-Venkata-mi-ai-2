"""Part 2 graph state. Draft and evaluation events accumulate across retries."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class ResponseState(TypedDict, total=False):
    ticket_id: str
    handoff: dict[str, Any]
    metadata: dict[str, Any]
    assignments: list[dict[str, Any]]
    round: int
    max_rounds: int
    active_ids: list[str]
    feedback: dict[str, str]
    draft_events: Annotated[list[dict[str, Any]], operator.add]
    eval_events: Annotated[list[dict[str, Any]], operator.add]
    blocked_phi: bool
    part2_outcome: str
    final_status: str
