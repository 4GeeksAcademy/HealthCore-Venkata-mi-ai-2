"""Graph state for the coordinator knowledge agent.

Single-turn desk Q&A: a run never needs earlier turns, so there is no message
history here. Inspecting or resuming a run goes through the checkpointer thread
(``thread_id == run_id``), not through state.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, get_type_hints

Outcome = Literal[
    "answered",
    "no_context",
    "invalid_question",
    "tool_fallback",
    "guard_blocked",
]
SourceName = Literal["ticket", "inventory", "knowledge_base"]
PlannerName = Literal["llm", "rules", "rules_fallback"]


class RetrievedChunk(TypedDict):
    source_document: str
    chunk_index: int
    section: str
    text: str
    score: float


class SourcePlan(TypedDict):
    """Which sources answer the question, in execution order, and the tool inputs."""

    sources: list[SourceName]
    ticket_input: dict[str, Any] | None
    inventory_input: dict[str, Any] | None
    # Only when a tool is also planned: the policy part of the question, for the knowledge base.
    knowledge_question: str | None
    planner: PlannerName


class ToolResult(TypedDict):
    tool: Literal["ticket_lookup", "inventory_lookup"]
    status: str
    input: dict[str, Any]
    output: dict[str, Any]


class FallbackNote(TypedDict):
    tool: str
    reason: str
    message: str


class GuardEvent(TypedDict):
    layer: str
    failure_type: str
    action: str
    rule_id: str
    classification: str


class AgentState(TypedDict, total=False):
    question: str
    plan: SourcePlan
    tool_results: list[ToolResult]
    fallbacks: list[FallbackNote]
    context: list[RetrievedChunk]
    answer: str
    outcome: Outcome
    redirect_required: bool
    guard_events: list[GuardEvent]


STATE_KEYS: frozenset[str] = frozenset(get_type_hints(AgentState))
