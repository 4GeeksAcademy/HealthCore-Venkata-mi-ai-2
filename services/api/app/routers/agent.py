"""Coordinator knowledge agent — invokes the compiled LangGraph graph; no business logic here."""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


def _agent_package() -> ModuleType:
    # Local runs: walk up to the monorepo root. In Compose /repo/services is on PYTHONPATH.
    for parent in Path(__file__).resolve().parents:
        if (parent / "services" / "knowledge_agent" / "__init__.py").is_file():
            for path in (parent, parent / "services"):
                if str(path) not in sys.path:
                    sys.path.insert(0, str(path))
            break
    return importlib.import_module("knowledge_agent")


def get_agent_runner() -> Any:
    return _agent_package().get_agent_runner()


class AgentQuery(BaseModel):
    question: str = Field(max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=64)


class AgentAnswer(BaseModel):
    answer: str
    outcome: str
    run_id: str
    sources: list[str]
    conversation_id: str
    memory_event: str


class GuardrailSummary(BaseModel):
    total: int
    by_failure_type: dict[str, int]
    by_action: dict[str, int]
    by_rule: dict[str, int]


@router.get("/guardrails/summary", response_model=GuardrailSummary)
def get_guardrail_summary(
    _user: dict = Depends(get_current_user),
    runner: Any = Depends(get_agent_runner),
) -> GuardrailSummary:
    """How many times each harness guardrail blocked or redirected in this session DB."""
    return GuardrailSummary(**runner.guardrail_summary())


@router.post("/query", response_model=AgentAnswer)
def post_agent_query(
    body: AgentQuery,
    _user: dict = Depends(get_current_user),
    runner: Any = Depends(get_agent_runner),
) -> AgentAnswer:
    agent = _agent_package()
    try:
        result = runner.run(
            body.question,
            conversation_id=body.conversation_id,
            actor_id=f"staff:{_user['id']}",
        )
    except agent.AgentRunFailed as exc:
        logger.error("Agent run %s failed at %s (%s)", exc.run_id, exc.node, exc.error_type)
        if exc.service_unavailable:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "The knowledge assistant is temporarily unavailable. Please try again. "
                    f"Reference: {exc.run_id}"
                ),
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The knowledge assistant could not complete this request. Reference: {exc.run_id}",
        ) from exc
    if result.outcome == "invalid_question":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=result.answer)
    return AgentAnswer(
        answer=result.answer,
        outcome=result.outcome,
        run_id=result.run_id,
        sources=list(result.sources),
        conversation_id=result.conversation_id,
        memory_event=result.memory_event,
    )
