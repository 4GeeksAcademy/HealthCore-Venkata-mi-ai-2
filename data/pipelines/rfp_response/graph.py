"""Draft and evaluate department sections. The PDF is not an input."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from data.pipelines.rfp_intake.departments import DEPARTMENTS, DEPARTMENT_IDS
from data.pipelines.rfp_intake.phi import redact
from data.pipelines.rfp_intake import store

from . import GRAPH_NAME
from .evaluators import evaluate_many, phi_hold_result
from .generators import CompleteJson, default_complete, generate_many
from .state import ResponseState

REQUIRED_NODES = frozenset(
    {
        "load_handoff",
        "mark_drafting",
        "department_round",
        "decide",
        "persist",
        "persist_blocked",
    }
)
FORBIDDEN_NODES = frozenset(
    {"generate_answer", "retrieve", "receive_question", "convert", "department_worker"}
)


class ResponseGraphBuildError(RuntimeError):
    """The response graph is structurally invalid and must not run."""


def max_rounds_from_env() -> int:
    raw = os.getenv("RFP_DRAFT_MAX_ITERATIONS", "2").strip()
    try:
        return max(int(raw), 1)
    except ValueError:
        return 2


@dataclass
class ResponseDeps:
    complete_json: CompleteJson = default_complete
    max_rounds: int | None = None

    def rounds(self) -> int:
        if self.max_rounds is not None:
            return max(int(self.max_rounds), 1)
        return max_rounds_from_env()


def assignments_from(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = dict(handoff.get("metadata") or {})
    by_id: dict[str, dict[str, Any]] = {}
    for section in handoff.get("sections") or []:
        department_id = str(section.get("department_id") or "")
        if department_id not in DEPARTMENT_IDS:
            continue
        owner = DEPARTMENTS[department_id]
        by_id[department_id] = {
            "department_id": department_id,
            "owner_name": str(section.get("owner_name") or owner.owner_name),
            "owner_role": str(section.get("owner_role") or owner.owner_role),
            "key_aspects": list(section.get("key_aspects") or []),
            "open_questions": list(section.get("open_questions") or []),
            "metadata": metadata,
        }
    for department_id in DEPARTMENT_IDS:
        if department_id in by_id:
            continue
        owner = DEPARTMENTS[department_id]
        by_id[department_id] = {
            "department_id": department_id,
            "owner_name": owner.owner_name,
            "owner_role": owner.owner_role,
            "key_aspects": [],
            "open_questions": [],
            "metadata": metadata,
        }
    return [by_id[department_id] for department_id in DEPARTMENT_IDS]


def _latest(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    chosen: dict[str, dict[str, Any]] = {}
    for event in events:
        department_id = str(event.get("department_id") or "")
        current = chosen.get(department_id)
        if current is None or int(event.get("round") or 0) >= int(current.get("round") or 0):
            chosen[department_id] = event
    return chosen


def _empty_failure(department_id: str) -> dict[str, Any]:
    return {
        "section_id": department_id,
        "department_id": department_id,
        "readability": {"pass": False, "score": None, "details": "No draft was written."},
        "relevance": {"pass": False, "missing_aspects": ["the department section"]},
        "compliance": {"pass": True, "rule_ids": ["HC-PHI-01"], "violations": []},
        "overall_pass": False,
        "feedback_for_generator": "Write the department section from the intake notes.",
        "contains_phi": False,
    }


def _section_payload(
    assignment: dict[str, Any],
    draft: str,
    result: dict[str, Any],
    *,
    iterations_used: int,
    iteration_limit: int,
) -> dict[str, Any]:
    stored, found = redact(draft)
    evaluation = dict(result)
    contains = bool(evaluation.get("contains_phi") or found)
    if found:
        compliance = dict(evaluation.get("compliance") or {})
        violations = list(compliance.get("violations") or [])
        rule_ids = list(compliance.get("rule_ids") or [])
        if "HC-PHI-01" not in rule_ids:
            rule_ids.append("HC-PHI-01")
            violations.append(
                {
                    "rule_id": "HC-PHI-01",
                    "detail": "Remove the patient name, diagnosis, or other patient identifier.",
                }
            )
        compliance["pass"] = False
        compliance["rule_ids"] = rule_ids
        compliance["violations"] = violations
        evaluation["compliance"] = compliance
        evaluation["overall_pass"] = False
        evaluation["contains_phi"] = True
    passed = bool(evaluation.get("overall_pass")) and not contains
    review = "passed" if passed else "needs_human_review"
    evaluation["review_state"] = review
    evaluation["provisional"] = review != "passed"
    evaluation["iterations_used"] = iterations_used
    evaluation["iteration_limit"] = iteration_limit
    evaluation["contains_phi"] = contains
    evaluation["section_id"] = assignment["department_id"]
    evaluation["department_id"] = assignment["department_id"]
    return {
        "department_id": assignment["department_id"],
        "owner_name": assignment.get("owner_name") or "",
        "owner_role": assignment.get("owner_role") or "",
        "key_aspects": list(assignment.get("key_aspects") or []),
        "open_questions": list(assignment.get("open_questions") or []),
        "draft_content": stored,
        "contains_phi": contains,
        "review_state": review,
        "provisional": review != "passed",
        "iterations_used": iterations_used,
        "evaluation_results": evaluation,
        "evaluation_result": evaluation,
    }


def load_handoff_node(deps: ResponseDeps) -> Callable[[ResponseState], dict]:
    def _node(state: ResponseState) -> dict:
        ticket = store.get_ticket(state["ticket_id"])
        if ticket is None or ticket.status not in {"intake_complete", "drafting"} or not ticket.handoff_ready:
            raise ValueError("not_draftable")
        handoff = dict(ticket.handoff_json or {})
        blocked = str(handoff.get("part2_guard") or "") == "phi_review_required"
        assignments = assignments_from(handoff)
        return {
            "handoff": handoff,
            "metadata": dict(handoff.get("metadata") or {}),
            "assignments": assignments,
            "round": 1,
            "max_rounds": deps.rounds(),
            "active_ids": [item["department_id"] for item in assignments],
            "feedback": {},
            "blocked_phi": blocked,
            "part2_outcome": "",
            "final_status": "",
        }

    return _node


def route_after_load(state: ResponseState) -> str:
    if state.get("blocked_phi"):
        return "persist_blocked"
    return "mark_drafting"


def mark_drafting_node(state: ResponseState) -> dict:
    store.set_response_status(state["ticket_id"], "drafting")
    return {}


def department_round_node(deps: ResponseDeps) -> Callable[[ResponseState], dict]:
    def _node(state: ResponseState) -> dict:
        active = set(state.get("active_ids") or [])
        items = [item for item in state.get("assignments") or [] if item["department_id"] in active]
        drafts = generate_many(
            items,
            dict(state.get("feedback") or {}),
            deps.complete_json,
            int(state.get("round") or 1),
        )
        store.set_response_status(state["ticket_id"], "under_evaluation")
        evaluations = evaluate_many(drafts, dict(state.get("metadata") or {}))
        return {"draft_events": drafts, "eval_events": evaluations}

    return _node


def decide_node(state: ResponseState) -> dict:
    latest = _latest(list(state.get("eval_events") or []))
    failed = [
        department_id
        for department_id, event in latest.items()
        if not (event.get("result") or {}).get("overall_pass")
    ]
    rnd = int(state.get("round") or 1)
    limit = int(state.get("max_rounds") or 1)
    if not failed or rnd >= limit:
        return {"part2_outcome": "closed"}
    feedback = dict(state.get("feedback") or {})
    for department_id in failed:
        result = (latest[department_id].get("result") or {})
        feedback[department_id] = str(result.get("feedback_for_generator") or "")
    return {
        "round": rnd + 1,
        "active_ids": failed,
        "feedback": feedback,
        "part2_outcome": "",
    }


def route_after_decide(state: ResponseState) -> str:
    if state.get("part2_outcome") == "closed":
        return "persist"
    return "mark_drafting"


def persist_node(state: ResponseState) -> dict:
    limit = int(state.get("max_rounds") or 1)
    drafts = _latest(list(state.get("draft_events") or []))
    evaluations = _latest(list(state.get("eval_events") or []))
    sections: list[dict[str, Any]] = []
    for assignment in state.get("assignments") or []:
        department_id = assignment["department_id"]
        draft_event = drafts.get(department_id) or {}
        eval_event = evaluations.get(department_id) or {}
        result = dict(eval_event.get("result") or _empty_failure(department_id))
        sections.append(
            _section_payload(
                assignment,
                str(draft_event.get("draft") or ""),
                result,
                iterations_used=int(eval_event.get("round") or 0),
                iteration_limit=limit,
            )
        )
    failed = any(section["review_state"] != "passed" for section in sections)
    outcome = "needs_human_review" if failed else "passed"
    final_status = "needs_human_review" if failed else "under_evaluation"
    store.save_response(
        state["ticket_id"],
        final_status=final_status,
        part2_outcome=outcome,
        sections=sections,
        iteration_limit=limit,
    )
    return {"final_status": final_status, "part2_outcome": outcome}


def persist_blocked_node(state: ResponseState) -> dict:
    limit = int(state.get("max_rounds") or 1)
    sections: list[dict[str, Any]] = []
    for assignment in state.get("assignments") or []:
        result = phi_hold_result(assignment["department_id"], iteration_limit=limit)
        sections.append(
            {
                "department_id": assignment["department_id"],
                "owner_name": assignment.get("owner_name") or "",
                "owner_role": assignment.get("owner_role") or "",
                "key_aspects": list(assignment.get("key_aspects") or []),
                "open_questions": list(assignment.get("open_questions") or []),
                "draft_content": "",
                "contains_phi": False,
                "review_state": "needs_human_review",
                "provisional": True,
                "iterations_used": 0,
                "evaluation_results": result,
                "evaluation_result": result,
            }
        )
    store.save_response(
        state["ticket_id"],
        final_status="needs_human_review",
        part2_outcome="needs_human_review",
        sections=sections,
        iteration_limit=limit,
    )
    return {"final_status": "needs_human_review", "part2_outcome": "needs_human_review"}


def build_graph(deps: ResponseDeps | None = None):
    deps = deps or ResponseDeps()
    graph = StateGraph(ResponseState)
    graph.add_node("load_handoff", load_handoff_node(deps))
    graph.add_node("mark_drafting", mark_drafting_node)
    graph.add_node("department_round", department_round_node(deps))
    graph.add_node("decide", decide_node)
    graph.add_node("persist", persist_node)
    graph.add_node("persist_blocked", persist_blocked_node)

    graph.add_edge(START, "load_handoff")
    graph.add_conditional_edges(
        "load_handoff",
        route_after_load,
        {"persist_blocked": "persist_blocked", "mark_drafting": "mark_drafting"},
    )
    graph.add_edge("persist_blocked", END)
    graph.add_edge("mark_drafting", "department_round")
    graph.add_edge("department_round", "decide")
    graph.add_conditional_edges(
        "decide",
        route_after_decide,
        {"persist": "persist", "mark_drafting": "mark_drafting"},
    )
    graph.add_edge("persist", END)

    compiled = graph.compile()
    names = set(compiled.get_graph().nodes)
    missing = REQUIRED_NODES - names
    if missing:
        raise ResponseGraphBuildError(f"missing nodes: {sorted(missing)}")
    mixed = FORBIDDEN_NODES & names
    if mixed:
        raise ResponseGraphBuildError(f"forbidden nodes present: {sorted(mixed)}")
    if GRAPH_NAME in {"healthcore_knowledge_agent", "healthcore_rfp_intake"}:
        raise ResponseGraphBuildError("response graph reused another graph name")
    return compiled


def initial_state(ticket_id: str) -> ResponseState:
    return {
        "ticket_id": ticket_id,
        "handoff": {},
        "metadata": {},
        "assignments": [],
        "round": 1,
        "max_rounds": 2,
        "active_ids": [],
        "feedback": {},
        "draft_events": [],
        "eval_events": [],
        "blocked_phi": False,
        "part2_outcome": "",
        "final_status": "",
    }
