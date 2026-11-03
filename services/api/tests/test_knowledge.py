"""POST /knowledge/query — router delegates to data/pipelines/rag.query()."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def rag_pipeline():
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    return importlib.import_module("data.pipelines.rag")


def test_knowledge_query_requires_auth(client: TestClient) -> None:
    response = client.post("/knowledge/query", json={"question": "What should I bring?"})
    assert response.status_code == 401


def test_knowledge_query_returns_answer_only(
    client: TestClient, auth_headers: dict, rag_pipeline, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_query(question: str) -> str:
        calls.append(question)
        return "Bring a valid ID and the insurance card.\nSource: new-patient-checklist"

    monkeypatch.setattr(rag_pipeline, "query", fake_query)

    response = client.post(
        "/knowledge/query",
        headers=auth_headers,
        json={"question": "  What should a new patient bring?  "},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "answer": "Bring a valid ID and the insurance card.\nSource: new-patient-checklist"
    }
    assert calls == ["What should a new patient bring?"]


def test_knowledge_query_rejects_blank_question(client: TestClient, auth_headers: dict) -> None:
    response = client.post("/knowledge/query", headers=auth_headers, json={"question": "   "})
    assert response.status_code == 422


def test_knowledge_query_unavailable_returns_503(
    client: TestClient, auth_headers: dict, rag_pipeline, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_query(_question: str) -> str:
        raise rag_pipeline.KnowledgeBaseUnavailable("vector store unavailable")

    monkeypatch.setattr(rag_pipeline, "query", broken_query)

    response = client.post(
        "/knowledge/query", headers=auth_headers, json={"question": "Cancellation fee?"}
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "The knowledge assistant is temporarily unavailable. Please try again."
    }
