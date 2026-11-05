"""Coordinator knowledge agent mechanics: compilation, routing, checkpointing, tracing.

Stubs only — no Qdrant, embeddings, or generation model.
"""

from __future__ import annotations

import inspect
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from langgraph.graph import END  # noqa: E402

from data.pipelines import rag  # noqa: E402
from services.knowledge_agent import (  # noqa: E402
    AgentDependencies,
    AgentGraphBuildError,
    AgentRunFailed,
    AgentRunner,
    NodeSpec,
    TraceStore,
    compile_agent_graph,
    default_spec,
)
from services.knowledge_agent import nodes as agent_nodes  # noqa: E402

CHUNK = {
    "company": "healthcore",
    "language": "en",
    "source_document": "appointment-policy",
    "chunk_index": 1,
    "section": "Cancellation policy",
    "text": "Cancelling less than 24 hours in advance, or no-show: 50 USD (or 40 GBP in the UK).",
    "score": 0.64,
}


class StubRag:
    def __init__(self, hits: list[dict[str, Any]], answer: str = "50 USD.\nSource: appointment-policy") -> None:
        self.hits = hits
        self.answer = answer
        self.retrieve_calls: list[str] = []
        self.generate_calls: list[tuple[str, list[dict[str, Any]]]] = []
        self.fail_generation_times = 0

    def retrieve(self, question: str) -> list[dict[str, Any]]:
        self.retrieve_calls.append(question)
        return self.hits

    def generate_answer(self, question: str, context: list[dict[str, Any]]) -> str:
        self.generate_calls.append((question, context))
        if self.fail_generation_times:
            self.fail_generation_times -= 1
            raise rag.KnowledgeBaseUnavailable("generation model unavailable")
        return self.answer

    def deps(self) -> AgentDependencies:
        return AgentDependencies(retrieve=self.retrieve, generate_answer=self.generate_answer)


@pytest.fixture
def make_runner(tmp_path: Path):
    runners: list[AgentRunner] = []

    def _make(stub: StubRag, **kwargs: Any) -> AgentRunner:
        runner = AgentRunner(deps=stub.deps(), state_dir=tmp_path / f"state{len(runners)}", **kwargs)
        runners.append(runner)
        return runner

    yield _make
    for runner in runners:
        runner.close()


# ---------------------------------------------------------------------------
# Compilation and structure
# ---------------------------------------------------------------------------


def test_default_graph_compiles_with_conditional_edges() -> None:
    drawn = compile_agent_graph(deps=StubRag([]).deps()).get_graph()

    assert set(drawn.nodes) == {
        "__start__",
        "receive_question",
        "retrieve",
        "generate_answer",
        "no_context_answer",
        "reject_question",
        "__end__",
    }
    conditional = {(e.source, e.target) for e in drawn.edges if e.conditional}
    assert conditional == {
        ("receive_question", "retrieve"),
        ("receive_question", "reject_question"),
        ("retrieve", "generate_answer"),
        ("retrieve", "no_context_answer"),
    }


def test_orphan_node_fails_compilation() -> None:
    spec = default_spec(StubRag([]).deps())
    spec = replace(spec, nodes=spec.nodes + (NodeSpec("orphan", lambda s: {}, frozenset()),))

    with pytest.raises(AgentGraphBuildError, match="not reachable from START: \\['orphan'\\]"):
        compile_agent_graph(spec)


def test_node_without_path_to_end_fails_compilation() -> None:
    spec = default_spec(StubRag([]).deps())
    spec = replace(spec, edges=tuple(e for e in spec.edges if e[0] != "reject_question"))

    with pytest.raises(AgentGraphBuildError, match="no path to END: \\['reject_question'\\]"):
        compile_agent_graph(spec)


def test_edge_to_unknown_node_fails_compilation() -> None:
    spec = default_spec(StubRag([]).deps())
    spec = replace(spec, edges=spec.edges + (("generate_answer", "nowhere"),))

    with pytest.raises(AgentGraphBuildError, match="unknown node `nowhere`"):
        compile_agent_graph(spec)


def test_mistyped_state_key_fails_compilation() -> None:
    spec = default_spec(StubRag([]).deps())
    nodes = tuple(
        replace(n, writes=frozenset({"answr", "outcome"})) if n.name == "generate_answer" else n
        for n in spec.nodes
    )

    with pytest.raises(AgentGraphBuildError, match="unknown state key\\(s\\) \\['answr'\\]"):
        compile_agent_graph(replace(spec, nodes=nodes))


def test_undeclared_write_fails_the_run_at_that_node(make_runner) -> None:
    spec = default_spec(StubRag([CHUNK]).deps())
    nodes = tuple(
        replace(n, fn=lambda s: {"context": [], "answer": "leak"}) if n.name == "retrieve" else n
        for n in spec.nodes
    )
    runner = make_runner(StubRag([CHUNK]), spec=replace(spec, nodes=nodes))

    with pytest.raises(AgentRunFailed) as failed:
        runner.run("cancel fee?")

    assert failed.value.node == "retrieve"
    assert failed.value.error_type == "AgentStateError"
    assert runner.traces.get_run(failed.value.run_id)["status"] == "failed"


def test_nodes_reuse_data_pipelines_rag_and_never_call_query() -> None:
    deps = AgentDependencies()

    assert deps.retrieve is rag.retrieve
    assert deps.generate_answer is rag.generate_answer
    assert "query(" not in inspect.getsource(agent_nodes)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def test_generation_receives_exactly_the_retrieved_context(make_runner) -> None:
    stub = StubRag([CHUNK])
    runner = make_runner(stub)

    result = runner.run("  Is there a   charge for cancelling 12 hours ahead? ")

    assert result.outcome == "answered"
    assert stub.retrieve_calls == ["Is there a charge for cancelling 12 hours ahead?"]
    [(question, context)] = stub.generate_calls
    assert question == stub.retrieve_calls[0]
    assert context == [{k: CHUNK[k] for k in ("source_document", "chunk_index", "section", "text", "score")}]
    assert runner.traces.node_sequence(result.run_id) == ["receive_question", "retrieve", "generate_answer"]


def test_empty_context_routes_to_honest_answer_without_generation(make_runner) -> None:
    stub = StubRag([])
    runner = make_runner(stub)

    result = runner.run("What is the Wi-Fi password?")

    assert result.outcome == "no_context"
    assert result.answer.startswith(rag.NO_CONTEXT_SENTENCE)
    assert stub.generate_calls == []
    assert runner.traces.node_sequence(result.run_id) == ["receive_question", "retrieve", "no_context_answer"]


@pytest.mark.parametrize("question", ["", "   \n\t ", "x" * 1001])
def test_invalid_question_never_reaches_retrieval(make_runner, question: str) -> None:
    stub = StubRag([CHUNK])
    runner = make_runner(stub)

    result = runner.run(question)

    assert result.outcome == "invalid_question"
    assert stub.retrieve_calls == []
    assert runner.traces.node_sequence(result.run_id) == ["receive_question", "reject_question"]


# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------


def test_checkpoint_after_every_transition(make_runner) -> None:
    runner = make_runner(StubRag([CHUNK]))

    result = runner.run("cancel fee?")
    checkpoints = runner.checkpoints(result.run_id)

    assert [c["step"] for c in checkpoints] == [-1, 0, 1, 2, 3]
    assert [c["next"] for c in checkpoints] == [
        ["__start__"],
        ["receive_question"],
        ["retrieve"],
        ["generate_answer"],
        [],
    ]
    assert checkpoints[3]["state_keys"] == ["context", "question"]


def test_failed_run_resumes_from_checkpoint_without_retrieving_again(make_runner) -> None:
    stub = StubRag([CHUNK])
    stub.fail_generation_times = 1
    runner = make_runner(stub)

    with pytest.raises(AgentRunFailed) as failed:
        runner.run("cancel fee?")
    run_id = failed.value.run_id

    assert failed.value.node == "generate_answer"
    assert failed.value.service_unavailable is True
    assert runner.checkpoints(run_id)[-1]["next"] == ["generate_answer"]
    run = runner.traces.get_run(run_id)
    assert (run["status"], run["failed_node"], run["error_type"]) == (
        "failed",
        "generate_answer",
        "KnowledgeBaseUnavailable",
    )

    resumed = runner.resume(run_id)

    assert resumed.outcome == "answered"
    assert len(stub.retrieve_calls) == 1
    assert len(stub.generate_calls) == 2
    run = runner.traces.get_run(run_id)
    assert run["status"] == "completed"
    assert [(s["node"], s["status"]) for s in run["steps"]] == [
        ("receive_question", "completed"),
        ("retrieve", "completed"),
        ("generate_answer", "failed"),
        ("generate_answer", "completed"),
    ]


# ---------------------------------------------------------------------------
# Tracing
# ---------------------------------------------------------------------------


def test_trace_is_queryable_from_disk_after_the_run(tmp_path: Path) -> None:
    runner = AgentRunner(deps=StubRag([CHUNK]).deps(), state_dir=tmp_path)
    result = runner.run("cancel fee?", labels={"case_id": "probe"})
    runner.close()

    reopened = TraceStore(tmp_path / "traces.sqlite")
    run = reopened.get_run(result.run_id)
    reopened.close()

    assert run["labels"] == {"case_id": "probe"}
    assert run["outcome"] == "answered"
    retrieve_step = run["steps"][1]
    assert retrieve_step["node"] == "retrieve"
    assert retrieve_step["output"]["hits"] == [
        {"source_document": "appointment-policy", "chunk_index": 1, "section": "Cancellation policy", "score": 0.64}
    ]
    assert run["steps"][2]["output"]["source_line"] == "Source: appointment-policy"


def test_trace_omits_question_and_answer_text_by_default(make_runner, monkeypatch) -> None:
    monkeypatch.delenv("AGENT_TRACE_STORE_TEXT", raising=False)
    runner = make_runner(StubRag([CHUNK]))

    result = runner.run("cancel fee?")
    run = runner.traces.get_run(result.run_id)

    assert run["question_text"] is None and run["answer_text"] is None
    assert len(run["question_sha256"]) == 64 and run["question_chars"] == len("cancel fee?")
    for step in run["steps"]:
        assert "question" not in step["output"] and "answer" not in step["output"]


def test_list_runs_filters_by_outcome(make_runner) -> None:
    runner = make_runner(StubRag([]))
    runner.run("Wi-Fi password?")
    runner.run("   ")

    assert [r["outcome"] for r in runner.traces.list_runs(outcome="no_context")] == ["no_context"]
    assert len(runner.traces.list_runs(status="completed")) == 2


def test_graph_end_constant_is_the_terminal_target() -> None:
    assert all(target == END for _source, target in default_spec(StubRag([]).deps()).edges)
