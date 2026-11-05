"""Graph state for the coordinator knowledge agent.

Single-turn desk Q&A: a run never needs earlier turns, so there is no message
history here. Inspecting or resuming a run goes through the checkpointer thread
(``thread_id == run_id``), not through state.
"""

from __future__ import annotations

from typing import Literal, TypedDict, get_type_hints

Outcome = Literal["answered", "no_context", "invalid_question"]


class RetrievedChunk(TypedDict):
    source_document: str
    chunk_index: int
    section: str
    text: str
    score: float


class AgentState(TypedDict, total=False):
    question: str
    context: list[RetrievedChunk]
    answer: str
    outcome: Outcome


STATE_KEYS: frozenset[str] = frozenset(get_type_hints(AgentState))
