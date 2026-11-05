"""Single-responsibility nodes. Retrieval and generation are the existing RAG
functions from ``data/pipelines/rag.py``, injected through ``AgentDependencies``."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data.pipelines import rag  # noqa: E402

from .state import AgentState, RetrievedChunk  # noqa: E402

logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 1000

INVALID_QUESTION_MESSAGE = (
    f"Please type a question for the knowledge assistant (up to {MAX_QUESTION_CHARS} characters)."
)
NO_CONTEXT_FOLLOW_UP = "Please check with the relevant HealthCore team before answering the patient."

RetrieveFn = Callable[[str], list[dict[str, Any]]]
GenerateFn = Callable[[str, list[dict[str, Any]]], str]


@dataclass(frozen=True)
class AgentDependencies:
    retrieve: RetrieveFn = rag.retrieve
    generate_answer: GenerateFn = rag.generate_answer


def receive_question(state: AgentState) -> AgentState:
    question = " ".join((state.get("question") or "").split())
    if not question or len(question) > MAX_QUESTION_CHARS:
        return {"question": question, "outcome": "invalid_question"}
    return {"question": question}


def reject_question(_state: AgentState) -> AgentState:
    return {"answer": INVALID_QUESTION_MESSAGE, "outcome": "invalid_question"}


def make_retrieve_node(deps: AgentDependencies) -> Callable[[AgentState], AgentState]:
    def retrieve(state: AgentState) -> AgentState:
        hits = deps.retrieve(state["question"])
        context: list[RetrievedChunk] = [
            {
                "source_document": str(hit.get("source_document", "")),
                "chunk_index": int(hit.get("chunk_index", -1)),
                "section": str(hit.get("section", "")),
                "text": str(hit.get("text", "")),
                "score": float(hit.get("score", 0.0)),
            }
            for hit in hits
        ]
        # Chunk ids and scores only — the question may contain details typed at the desk.
        logger.info(
            "agent retrieve hits=%d %s",
            len(context),
            ", ".join(f"{c['source_document']}#{c['chunk_index']}={c['score']:.3f}" for c in context),
        )
        return {"context": context}

    return retrieve


def make_generate_node(deps: AgentDependencies) -> Callable[[AgentState], AgentState]:
    def generate_answer(state: AgentState) -> AgentState:
        answer = deps.generate_answer(state["question"], list(state["context"]))
        return {"answer": answer, "outcome": "answered"}

    return generate_answer


def no_context_answer(_state: AgentState) -> AgentState:
    return {"answer": f"{rag.NO_CONTEXT_SENTENCE} {NO_CONTEXT_FOLLOW_UP}", "outcome": "no_context"}


def route_after_receive(state: AgentState) -> str:
    return "reject_question" if state.get("outcome") == "invalid_question" else "retrieve"


def route_after_retrieve(state: AgentState) -> str:
    return "generate_answer" if state.get("context") else "no_context_answer"
