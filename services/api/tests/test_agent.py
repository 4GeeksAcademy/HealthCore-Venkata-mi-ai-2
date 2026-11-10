"""POST /agent/query — the router only invokes the compiled knowledge agent graph."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest
from app.main import app
from app.routers import agent as agent_router
from fastapi.testclient import TestClient

CHUNK = {
    "source_document": "new-patient-checklist",
    "chunk_index": 1,
    "section": "Documents the patient should bring on the day of the appointment",
    "text": "- A valid ID document.\n- Insurance card (if applicable).",
    "score": 0.71,
}


class StubRag:
    def __init__(self, hits: list[dict[str, Any]], error: BaseException | None = None) -> None:
        self.hits = hits
        self.error = error
        self.retrieve_calls: list[str] = []

    def retrieve(self, question: str) -> list[dict[str, Any]]:
        self.retrieve_calls.append(question)
        return self.hits

    def generate_answer(self, question: str, context: list[dict[str, Any]]) -> str:
        if self.error:
            raise self.error
        return "Bring a valid ID and the insurance card.\nSource: new-patient-checklist"


@pytest.fixture
def agent():
    agent_router._agent_package()
    return importlib.import_module("knowledge_agent")


@pytest.fixture
def use_stub(agent, tmp_path: Path):
    runners = []

    def _use(stub: StubRag):
        runner = agent.AgentRunner(
            deps=agent.AgentDependencies(
                retrieve=stub.retrieve, generate_answer=stub.generate_answer, plan_sources=agent.rules_plan
            ),
            state_dir=tmp_path,
        )
        runners.append(runner)
        app.dependency_overrides[agent_router.get_agent_runner] = lambda: runner
        return runner

    yield _use
    app.dependency_overrides.pop(agent_router.get_agent_runner, None)
    for runner in runners:
        runner.close()


def test_agent_query_requires_auth(client: TestClient) -> None:
    response = client.post("/agent/query", json={"question": "What should I bring?"})
    assert response.status_code == 401


def test_graph_is_compiled_at_startup(client: TestClient) -> None:
    assert agent_router.get_agent_runner().graph is not None


def test_agent_query_returns_answer_outcome_and_run_id(
    client: TestClient, auth_headers: dict, use_stub
) -> None:
    stub = StubRag([CHUNK])
    runner = use_stub(stub)

    response = client.post(
        "/agent/query", headers=auth_headers, json={"question": "  What should a new patient bring?  "}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"answer", "outcome", "run_id", "sources", "conversation_id", "memory_event"}
    assert body["memory_event"] == "none"
    assert body["conversation_id"]
    assert body["answer"] == "Bring a valid ID and the insurance card.\nSource: new-patient-checklist"
    assert body["outcome"] == "answered"
    assert body["sources"] == ["knowledge_base"]
    assert stub.retrieve_calls == ["What should a new patient bring?"]
    assert runner.traces.node_sequence(body["run_id"]) == [
        "receive_question",
        "plan_sources",
        "retrieve",
        "generate_answer",
    ]


def test_agent_query_tool_fallback_is_a_200_honest_answer(
    client: TestClient, auth_headers: dict, use_stub, monkeypatch
) -> None:
    monkeypatch.delenv("AGENT_SERVICE_EMAIL", raising=False)
    stub = StubRag([CHUNK])
    use_stub(stub)

    response = client.post(
        "/agent/query", headers=auth_headers, json={"question": "What's the status of ticket INC-0042?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["outcome"] == "tool_fallback"
    assert body["sources"] == ["incident_manager"]
    assert body["answer"].startswith("I couldn't confirm ticket INC-0042's status right now")
    assert stub.retrieve_calls == []


def test_agent_query_no_context_is_an_honest_answer(
    client: TestClient, auth_headers: dict, use_stub
) -> None:
    use_stub(StubRag([]))

    response = client.post("/agent/query", headers=auth_headers, json={"question": "Wi-Fi password?"})

    assert response.status_code == 200
    assert response.json()["outcome"] == "no_context"
    assert response.json()["answer"].startswith("I don't have enough information")


def test_agent_query_blank_question_is_rejected_by_the_graph(
    client: TestClient, auth_headers: dict, use_stub
) -> None:
    stub = StubRag([CHUNK])
    use_stub(stub)

    response = client.post("/agent/query", headers=auth_headers, json={"question": "   "})

    assert response.status_code == 422
    assert response.json()["detail"].startswith("Please type a question")
    assert stub.retrieve_calls == []


def test_agent_query_model_unavailable_returns_503_without_internals(
    client: TestClient, auth_headers: dict, use_stub, agent
) -> None:
    rag = importlib.import_module("data.pipelines.rag")
    use_stub(StubRag([CHUNK], error=rag.KnowledgeBaseUnavailable("generation model unavailable")))

    response = client.post("/agent/query", headers=auth_headers, json={"question": "Cancellation fee?"})

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail.startswith("The knowledge assistant is temporarily unavailable. Please try again. Reference: ")
    assert "generation model" not in detail and "Traceback" not in detail


def test_agent_query_unexpected_node_error_returns_500_without_internals(
    client: TestClient, auth_headers: dict, use_stub
) -> None:
    runner = use_stub(StubRag([CHUNK], error=RuntimeError("db password=hunter2 at /srv/app.py:12")))

    response = client.post("/agent/query", headers=auth_headers, json={"question": "Cancellation fee?"})

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail.startswith("The knowledge assistant could not complete this request. Reference: ")
    assert "hunter2" not in response.text and "RuntimeError" not in response.text
    run_id = detail.rsplit(" ", 1)[-1]
    run = runner.traces.get_run(run_id)
    assert (run["status"], run["failed_node"], run["error_type"]) == ("failed", "generate_answer", "RuntimeError")


def test_agent_query_keeps_a_conversation_and_refuses_patient_memory(
    client: TestClient, auth_headers: dict, use_stub
) -> None:
    stub = StubRag([CHUNK])
    runner = use_stub(stub)

    echoed = client.post(
        "/agent/query",
        headers=auth_headers,
        json={"question": "What should a new patient bring?", "conversation_id": "desk-1"},
    )
    assert echoed.status_code == 200
    assert echoed.json()["conversation_id"] == "desk-1"
    assert echoed.json()["memory_event"] == "none"

    blocked = client.post(
        "/agent/query",
        headers=auth_headers,
        json={
            "question": "Patient Johnson cancelled tomorrow's appointment, note that down.",
            "conversation_id": "desk-phi",
        },
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["memory_event"] == "phi_blocked"
    assert blocked.json()["conversation_id"] == "desk-phi"
    assert "Johnson" not in blocked.text
    assert stub.retrieve_calls == ["What should a new patient bring?"]
    audit = runner.memory.store.list_audit("desk-phi")
    assert audit[-1].event == "phi_blocked"
    assert "Johnson" not in audit[-1].proposal_text
    assert "Johnson" not in audit[-1].originating_message


def test_router_has_no_retrieval_or_generation_logic() -> None:
    source = Path(agent_router.__file__).read_text(encoding="utf-8")
    for forbidden in ("data.pipelines", "rag.", "retrieve(", "generate_answer(", ".query("):
        assert forbidden not in source
