"""Coordinator knowledge agent evals — checked against the recorded trace, not a live run.

Record (or refresh) the trace:  uv run python scripts/record_agent_traces.py [--mode live]
Run the evals:                  uv run pytest tests/pipelines/test_agent_evals.py -v
Another export:                 AGENT_TRACE_FILE=path/to/export.json uv run pytest tests/pipelines/test_agent_evals.py

These extend tests/pipelines/test_rag.py; they do not replace it. Grounding
cases are an acceptance gate: a correct path with an answer that drops the
BRIEFING policy facts fails.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.knowledge_agent import GRAPH_VERSION  # noqa: E402

CASES_PATH = Path(__file__).with_name("agent_eval_cases.json")
TRACE_PATH = Path(os.getenv("AGENT_TRACE_FILE") or Path(__file__).parent / "fixtures" / "agent_traces.json")

CASES: list[dict[str, Any]] = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
TRACE: dict[str, Any] = json.loads(TRACE_PATH.read_text(encoding="utf-8"))
RUNS_BY_CASE: dict[str, dict[str, Any]] = {run["labels"]["case_id"]: run for run in TRACE["runs"]}


def _run_for(case: dict[str, Any]) -> dict[str, Any]:
    required = case.get("requires_mode")
    if required and TRACE["mode"] != required:
        pytest.skip(f"{case['id']} needs a {required} trace; fixture was recorded {TRACE['mode']}")
    assert case["id"] in RUNS_BY_CASE, f"no recorded run for {case['id']}; re-record the trace"
    return RUNS_BY_CASE[case["id"]]


def _nodes(run: dict[str, Any]) -> list[str]:
    return [step["node"] for step in run["steps"]]


def _step(run: dict[str, Any], node: str) -> dict[str, Any]:
    return next(step for step in run["steps"] if step["node"] == node)


def _case_ids(kind: str | None = None) -> list[Any]:
    return [pytest.param(c, id=c["id"]) for c in CASES if kind is None or c["kind"] == kind]


# ---------------------------------------------------------------------------
# Trace completeness
# ---------------------------------------------------------------------------


def test_trace_covers_every_case_with_the_current_graph() -> None:
    assert TRACE["graph_version"] == GRAPH_VERSION, "trace is stale; re-record it"
    assert {c["id"] for c in CASES} == set(RUNS_BY_CASE)
    assert all(run["status"] == "completed" for run in TRACE["runs"])
    assert all(run["graph_version"] == GRAPH_VERSION for run in TRACE["runs"])


def test_every_run_has_ordered_timed_steps() -> None:
    for run in TRACE["runs"]:
        assert [s["seq"] for s in run["steps"]] == list(range(1, len(run["steps"]) + 1))
        assert all(s["status"] == "completed" and s["duration_ms"] >= 0 for s in run["steps"])
        assert run["started_at"] <= run["finished_at"]


# ---------------------------------------------------------------------------
# Per-case criteria
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case", _case_ids())
def test_path_matches_expected_route(case: dict[str, Any]) -> None:
    run = _run_for(case)
    nodes = _nodes(run)
    assert nodes == case["expected_nodes"]
    assert not set(nodes) & set(case.get("forbidden_nodes", []))
    assert run["outcome"] == case["expected_outcome"]


@pytest.mark.parametrize("case", _case_ids())
def test_retrieval_matches_expected_source(case: dict[str, Any]) -> None:
    run = _run_for(case)
    if "retrieve" not in _nodes(run):
        pytest.skip("retrieve is not on this route")
    hits = _step(run, "retrieve")["output"]["hits"]
    if "expected_hits" in case:
        assert len(hits) == case["expected_hits"]
    if "expected_top_source" in case:
        assert hits, "retrieve returned no context above min_score"
        assert hits[0]["source_document"] == case["expected_top_source"]
        assert all(h["score"] >= TRACE["min_score"] for h in hits)


@pytest.mark.parametrize("case", _case_ids())
def test_answer_contains_briefing_facts(case: dict[str, Any]) -> None:
    run = _run_for(case)
    answer = run["answer_text"] or ""
    lowered = answer.lower()
    for group in case["answer_must_include"]:
        assert any(phrase.lower() in lowered for phrase in group), (group, answer)
    for phrase in case.get("answer_must_not_include", []):
        assert phrase.lower() not in lowered, (phrase, answer)


@pytest.mark.parametrize("case", _case_ids("grounding"))
def test_grounded_answer_cites_the_retrieved_document(case: dict[str, Any]) -> None:
    run = _run_for(case)
    output = _step(run, "generate_answer")["output"]
    assert output["source_line"], "answer has no Source: line"
    assert case["expected_top_source"] in output["source_line"]


# ---------------------------------------------------------------------------
# Cross-run trace invariants
# ---------------------------------------------------------------------------


def test_retrieve_runs_exactly_once_before_generation() -> None:
    answered = [run for run in TRACE["runs"] if "generate_answer" in _nodes(run)]
    assert answered
    for run in answered:
        nodes = _nodes(run)
        assert nodes.count("retrieve") == 1
        assert nodes.count("generate_answer") == 1
        assert nodes.index("retrieve") < nodes.index("generate_answer")


def test_generation_never_runs_on_empty_context() -> None:
    for run in TRACE["runs"]:
        if "retrieve" in _nodes(run) and not _step(run, "retrieve")["output"]["hits"]:
            assert "generate_answer" not in _nodes(run)
            assert _nodes(run)[-1] == "no_context_answer"
