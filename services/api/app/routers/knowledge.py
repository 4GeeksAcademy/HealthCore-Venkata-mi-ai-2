"""Coordinator knowledge assistant — answers from the HealthCore policy knowledge base."""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from types import ModuleType

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.deps.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _rag_pipeline() -> ModuleType:
    # Local runs: walk up to the monorepo root. In Compose the repo is on PYTHONPATH (/repo).
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "pipelines" / "rag.py").is_file():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            break
    return importlib.import_module("data.pipelines.rag")


class KnowledgeQuery(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

    @field_validator("question")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value.strip()


class KnowledgeAnswer(BaseModel):
    answer: str


@router.post("/query", response_model=KnowledgeAnswer)
def post_knowledge_query(
    body: KnowledgeQuery,
    _user: dict = Depends(get_current_user),
) -> KnowledgeAnswer:
    pipeline = _rag_pipeline()
    try:
        answer = pipeline.query(body.question)
    except pipeline.KnowledgeBaseUnavailable as exc:
        logger.error("Knowledge assistant unavailable (%s)", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The knowledge assistant is temporarily unavailable. Please try again.",
        ) from exc
    return KnowledgeAnswer(answer=answer)
