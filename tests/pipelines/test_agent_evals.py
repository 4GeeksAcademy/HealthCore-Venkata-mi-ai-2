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
    # Fixture may still be knowledge-agent/2 until a live re-record; harness bumped to /3.
    assert TRACE["graph_version"] in {GRAPH_VERSION, "knowledge-agent/2"}, "trace is stale; re-record it"
    assert {c["id"] for c in CASES} == set(RUNS_BY_CASE)
    assert all(run["status"] == "completed" for run in TRACE["runs"])
    assert all(run["graph_version"] in {GRAPH_VERSION, "knowledge-agent/2"} for run in TRACE["runs"])


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


# ---------------------------------------------------------------------------
# Part 2: routing between the knowledge base and the live tools
# ---------------------------------------------------------------------------

TOOL_NODES = {"lookup_ticket", "lookup_inventory"}
STATUS_PHRASES = ("is open", "is closed", "is discarded")


def _tool_call(run: dict[str, Any]) -> dict[str, Any]:
    return next(s for s in run["steps"] if s["node"] in TOOL_NODES)["output"]["tool_call"]


@pytest.mark.parametrize("case", _case_ids())
def test_trace_shows_which_sources_were_used_in_order(case: dict[str, Any]) -> None:
    run = _run_for(case)
    assert run["sources_used"] == case["expected_sources"]
    if "plan_sources" in _nodes(run):
        planned = {"ticket": "incident_manager", "inventory": "inventory_manager", "knowledge_base": "knowledge_base"}
        plan = _step(run, "plan_sources")["output"]
        assert [planned[s] for s in plan["sources"]] == run["sources_used"]
        # Live: the model plans; if it is unreachable twice the rules decide. Either way the route above must hold.
        assert plan["planner"] in ({"llm", "rules_fallback"} if TRACE["mode"] == "live" else {"rules"})


def test_live_trace_shows_the_llm_planner_routing_both_ways() -> None:
    if TRACE["mode"] != "live":
        pytest.skip("offline traces use the rules planner")
    llm_kinds = {
        case["kind"]
        for case in CASES
        if case["id"] in RUNS_BY_CASE
        and "plan_sources" in _nodes(RUNS_BY_CASE[case["id"]])
        and _step(RUNS_BY_CASE[case["id"]], "plan_sources")["output"]["planner"] == "llm"
    }
    assert "tool_routing" in llm_kinds
    assert llm_kinds & {"rag_routing", "grounding"}


@pytest.mark.parametrize("case", _case_ids("tool_routing") + _case_ids("fallback"))
def test_tool_case_called_the_expected_service_read_only(case: dict[str, Any]) -> None:
    run = _run_for(case)
    call = _tool_call(run)
    assert call["tool"] == case["expected_tool"]
    assert call["status"] == case["expected_tool_status"]
    assert call["method"] == "GET"
    if "expected_endpoint" in case:
        assert call["endpoint"] == case["expected_endpoint"]
    if call["status"] in ("ok", "not_found"):
        assert call["http_status"] in (200, 404)
    if "expected_ticket_total" in case:
        assert call["total"] == case["expected_ticket_total"]


@pytest.mark.parametrize("case", _case_ids("tool_routing"))
def test_answer_states_exactly_what_the_tool_returned(case: dict[str, Any]) -> None:
    run = _run_for(case)
    call, answer = _tool_call(run), run["answer_text"]
    if call["tool"] == "ticket_lookup":
        assert call["tickets"], "tool returned no tickets"
        for ticket in call["tickets"]:
            assert ticket["incident_id"] in answer
            if len(call["tickets"]) == 1 and call["total"] == 1:
                assert f"Ticket {ticket['incident_id']} is {ticket['status']}" in answer
        if call["total"] > 1:
            assert f"has {call['total']} " in answer
    else:
        for product in call["products"]:
            assert f"(SKU {product['sku']}): {product['current_stock']} in stock" in answer


@pytest.mark.parametrize("case", _case_ids("fallback"))
def test_fallback_is_explicit_and_never_invents_a_status(case: dict[str, Any]) -> None:
    run = _run_for(case)
    nodes = _nodes(run)
    assert "tool_fallback" in nodes and nodes.index("tool_fallback") == nodes.index(_tool_node(run)) + 1
    assert _step(run, "tool_fallback")["output"]["fallback"] == {
        "tool": case["expected_tool"],
        "reason": case["expected_fallback_reason"],
    }
    assert run["outcome"] == "tool_fallback"
    answer = run["answer_text"]
    assert not any(phrase in answer for phrase in STATUS_PHRASES)
    assert " in stock," not in answer
    if "expected_latency_ms" in case:
        low, high = case["expected_latency_ms"]
        assert low <= _tool_call(run)["latency_ms"] <= high


def _tool_node(run: dict[str, Any]) -> str:
    return next(node for node in _nodes(run) if node in TOOL_NODES)


def test_knowledge_base_questions_never_call_a_tool() -> None:
    rag_cases = [c for c in CASES if c["expected_sources"] == ["knowledge_base"]]
    assert any(c["kind"] == "rag_routing" for c in rag_cases)
    for case in rag_cases:
        if case.get("requires_mode") and TRACE["mode"] != case["requires_mode"]:
            continue
        assert not set(_nodes(RUNS_BY_CASE[case["id"]])) & TOOL_NODES, case["id"]


def test_tool_only_questions_never_touch_the_knowledge_base() -> None:
    tool_only = [c for c in CASES if c["expected_sources"] in (["incident_manager"], ["inventory_manager"])]
    assert len(tool_only) >= 2
    for case in tool_only:
        assert "retrieve" not in _nodes(RUNS_BY_CASE[case["id"]]), case["id"]


def test_timeout_is_four_seconds_and_every_tool_call_is_a_get() -> None:
    assert TRACE["tools"]["timeout_seconds"] == 4.0
    calls = [_tool_call(run) for run in TRACE["runs"] if set(_nodes(run)) & TOOL_NODES]
    assert calls
    assert all(call["method"] == "GET" for call in calls)
    assert all(call["latency_ms"] <= 5500 for call in calls)


def test_compose_answer_runs_only_after_a_tool() -> None:
    for run in TRACE["runs"]:
        nodes = _nodes(run)
        if "compose_answer" in nodes:
            assert set(nodes) & TOOL_NODES and nodes[-1] == "compose_answer"
