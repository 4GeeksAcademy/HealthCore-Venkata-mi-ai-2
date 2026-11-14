"""Single-responsibility nodes. Retrieval and generation are the existing RAG
functions from ``data/pipelines/rag.py``; source planning and the two read-only
tools are injected the same way, through ``AgentDependencies``."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from langgraph.graph import END  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from data.pipelines import rag  # noqa: E402

from .guardrails.canned import CASUAL_REDIRECT_SUFFIX  # noqa: E402
from .guardrails.external import sanitize_external_text  # noqa: E402
from .guardrails.input import classify_input  # noqa: E402
from .guardrails.output import validate_output  # noqa: E402
from .planner import SourcePlanner  # noqa: E402
from .state import (  # noqa: E402
    AgentState,
    FallbackNote,
    GuardEvent,
    RetrievedChunk,
    SourcePlan,
    ToolResult,
)
from .tools import (  # noqa: E402
    InventoryLookupInput,
    InventoryLookupOutput,
    InventoryLookupTool,
    TicketLookupInput,
    TicketLookupOutput,
)
from .tools.inventory import TOOL_NAME as INVENTORY_TOOL  # noqa: E402
from .tools.incidents import TOOL_NAME as TICKET_TOOL  # noqa: E402
from .tools.mcp_incidents import McpIncidentLookup  # noqa: E402

logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 1000

INVALID_QUESTION_MESSAGE = (
    f"Please type a question for the knowledge assistant (up to {MAX_QUESTION_CHARS} characters)."
)
NO_CONTEXT_FOLLOW_UP = "Please check with the relevant HealthCore team before answering the patient."

RetrieveFn = Callable[[str], list[dict[str, Any]]]
GenerateFn = Callable[[str, list[dict[str, Any]]], str]
PlanFn = Callable[[str], SourcePlan]
TicketFn = Callable[[TicketLookupInput], TicketLookupOutput]
InventoryFn = Callable[[InventoryLookupInput], InventoryLookupOutput]


@dataclass(frozen=True)
class AgentDependencies:
    retrieve: RetrieveFn = rag.retrieve
    generate_answer: GenerateFn = rag.generate_answer
    plan_sources: PlanFn = field(default_factory=SourcePlanner)
    lookup_ticket: TicketFn = field(default_factory=McpIncidentLookup.from_env)
    lookup_inventory: InventoryFn = field(default_factory=InventoryLookupTool.from_env)


def receive_question(state: AgentState) -> AgentState:
    question = " ".join((state.get("question") or "").split())
    if not question or len(question) > MAX_QUESTION_CHARS:
        return {"question": question, "outcome": "invalid_question"}
    return {"question": question}


def reject_question(_state: AgentState) -> AgentState:
    return {"answer": INVALID_QUESTION_MESSAGE, "outcome": "invalid_question"}


def knowledge_question(state: AgentState) -> str:
    """What the knowledge base is asked: the policy part of a mixed question, else the question."""
    return (state.get("plan") or {}).get("knowledge_question") or state["question"]


def make_retrieve_node(deps: AgentDependencies) -> Callable[[AgentState], AgentState]:
    def retrieve(state: AgentState) -> AgentState:
        hits = deps.retrieve(knowledge_question(state))
        context: list[RetrievedChunk] = [
            {
                "source_document": str(hit.get("source_document", "")),
                "chunk_index": int(hit.get("chunk_index", -1)),
                "section": str(hit.get("section", "")),
                "text": sanitize_external_text(str(hit.get("text", ""))),
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
        answer = deps.generate_answer(knowledge_question(state), list(state["context"]))
        return {"answer": answer, "outcome": "answered"}

    return generate_answer


def no_context_answer(_state: AgentState) -> AgentState:
    return {"answer": f"{rag.NO_CONTEXT_SENTENCE} {NO_CONTEXT_FOLLOW_UP}", "outcome": "no_context"}


def make_plan_node(deps: AgentDependencies) -> Callable[[AgentState], AgentState]:
    def plan_sources(state: AgentState) -> AgentState:
        plan = deps.plan_sources(state["question"])
        logger.info("agent plan sources=%s planner=%s", ",".join(plan["sources"]), plan["planner"])
        return {"plan": plan}

    return plan_sources


def _tool_result(tool: str, request: dict[str, Any], output: Any) -> ToolResult:
    return {"tool": tool, "status": output.status, "input": request, "output": output.model_dump(mode="json")}


def make_ticket_node(deps: AgentDependencies) -> Callable[[AgentState], AgentState]:
    def lookup_ticket(state: AgentState) -> AgentState:
        request = dict(state["plan"].get("ticket_input") or {})
        try:
            output = deps.lookup_ticket(TicketLookupInput.model_validate(request))
        except ValidationError:
            output = TicketLookupOutput(status="invalid_input")
        logger.info("agent ticket_lookup status=%s %s %.0fms", output.status, output.endpoint, output.latency_ms)
        return {"tool_results": [*state.get("tool_results", []), _tool_result(TICKET_TOOL, request, output)]}

    return lookup_ticket


def make_inventory_node(deps: AgentDependencies) -> Callable[[AgentState], AgentState]:
    def lookup_inventory(state: AgentState) -> AgentState:
        request = dict(state["plan"].get("inventory_input") or {})
        try:
            output = deps.lookup_inventory(InventoryLookupInput.model_validate(request))
        except ValidationError:
            output = InventoryLookupOutput(status="invalid_input", endpoint="")
        logger.info("agent inventory_lookup status=%s %.0fms", output.status, output.latency_ms)
        return {"tool_results": [*state.get("tool_results", []), _tool_result(INVENTORY_TOOL, request, output)]}

    return lookup_inventory


_UNREACHABLE_REASON = {
    "timeout": "did not respond in time",
    "unavailable": "is not reachable",
    "bad_response": "sent a reply I could not read",
    "auth_failed": "did not accept the assistant's sign-in",
}
FALLBACK_FOLLOW_UP = "Please try again in a moment, or check it directly in the HealthCore backoffice."


def fallback_message(result: ToolResult) -> str:
    status, request = result["status"], result["input"]
    if result["tool"] == TICKET_TOOL:
        ticket = request.get("ticket_id")
        if status == "invalid_input":
            return "I couldn't tell which ticket you mean. Please give the incident ID (for example INC-0042)."
        if status == "not_found":
            return (
                f"I couldn't find ticket {ticket} in the incident manager, so I can't confirm its status. "
                "Please check the ticket number."
            )
        subject = f"ticket {ticket}'s status" if ticket else "those tickets"
        return f"I couldn't confirm {subject} right now: the incident manager {_UNREACHABLE_REASON[status]}. {FALLBACK_FOLLOW_UP}"
    product = request.get("product_query")
    if status == "invalid_input":
        return "I couldn't tell which product you mean. Please give the product name or SKU."
    if status == "not_found":
        return f'I couldn\'t find a product matching "{product}" in the inventory manager, so I can\'t confirm stock for it.'
    return f"I couldn't confirm stock levels right now: the inventory manager {_UNREACHABLE_REASON[status]}. {FALLBACK_FOLLOW_UP}"


def tool_fallback(state: AgentState) -> AgentState:
    """Honest reply for every failed tool call not yet handled. Never a status or a stock figure."""
    fallbacks: list[FallbackNote] = list(state.get("fallbacks", []))
    failed = [r for r in state.get("tool_results", []) if r["status"] != "ok"]
    for result in failed[len(fallbacks) :]:
        fallbacks.append({"tool": result["tool"], "reason": result["status"], "message": fallback_message(result)})
    return {"fallbacks": fallbacks}


def _render_ticket(output: dict[str, Any], request: dict[str, Any]) -> str:
    tickets = output["tickets"]
    if request.get("ticket_id"):
        t = tickets[0]
        return (
            f"Ticket {t['id']} is {t['status']}. Category: {t['category']}. "
            f"Branch: {t['branch']}. Title: {t.get('title') or '(none)'}. "
            f"Last updated: {t['updated_at']}.\n"
            "Source: HealthCore incident manager (live)"
        )
    described = " ".join(
        part
        for part in (request.get("status"), request.get("category"), "incident" if output["total"] == 1 else "incidents")
        if part
    )
    where = f" at {request['branch']}" if request.get("branch") else ""
    lines = [f"The incident manager has {output['total']} {described}{where}."]
    if tickets:
        shown = "; ".join(f"{t['id']} ({t['status']}, {t['category']}, {t['branch']})" for t in tickets)
        prefix = "First " + str(len(tickets)) if len(tickets) < output["total"] else "They are"
        lines.append(f"{prefix}: {shown}.")
    lines.append("Source: HealthCore incident manager (live)")
    return "\n".join(lines)


def _render_inventory(output: dict[str, Any]) -> str:
    lines = [
        f"{p['name']} (SKU {p['sku']}): {p['current_stock']} in stock, reorder threshold {p['threshold']}"
        + (" (below threshold)." if p["below_threshold"] else ".")
        for p in output["products"]
    ]
    lines.append("Source: HealthCore inventory manager (live)")
    return "\n".join(lines)


def compose_answer(state: AgentState) -> AgentState:
    """Tool facts verbatim from the typed outputs, then the knowledge-base answer if one was produced."""
    sections: list[str] = []
    fallback_by_tool = {note["tool"]: note["message"] for note in state.get("fallbacks", [])}
    for result in state.get("tool_results", []):
        if result["status"] != "ok":
            sections.append(fallback_by_tool[result["tool"]])
        elif result["tool"] == TICKET_TOOL:
            sections.append(_render_ticket(result["output"], result["input"]))
        else:
            sections.append(_render_inventory(result["output"]))
    if "context" in state and state.get("answer"):
        sections.append(f"From the HealthCore knowledge base:\n{state['answer']}")
    outcome = "tool_fallback" if state.get("fallbacks") else "answered"
    answer = "\n\n".join(sections)
    if state.get("redirect_required"):
        answer = f"{answer.rstrip()}{CASUAL_REDIRECT_SUFFIX}"
    return {"answer": answer, "outcome": outcome}


def input_guard(state: AgentState) -> AgentState:
    """Classify scope / abuse before any planner or tool LLM sees the question."""
    decision = classify_input(state.get("question") or "")
    events: list[GuardEvent] = list(state.get("guard_events") or [])
    if decision.failure_type is not None:
        events.append(
            {
                "layer": "input",
                "failure_type": decision.failure_type,
                "action": "block" if decision.action == "block" else "redirect",
                "rule_id": decision.rule_id,
                "classification": decision.classification,
            }
        )
        logger.info(
            "agent input_guard class=%s action=%s rule=%s type=%s",
            decision.classification,
            decision.action,
            decision.rule_id,
            decision.failure_type,
        )
    if decision.action == "block":
        return {
            "answer": decision.answer or "",
            "outcome": "guard_blocked",
            "redirect_required": False,
            "guard_events": events,
        }
    return {
        "redirect_required": decision.redirect_required,
        "guard_events": events,
    }


def output_guard(state: AgentState) -> AgentState:
    """Validate the composed answer: PHI, instruction leaks, expected shape."""
    kb_used = bool(state.get("context")) and state.get("outcome") in {"answered", "no_context"}
    # Tool-only answers still need PHI / leak checks.
    decision = validate_output(
        state.get("answer") or "",
        outcome=state.get("outcome"),
        kb_used=bool(state.get("context")) and state.get("outcome") == "answered",
    )
    events: list[GuardEvent] = list(state.get("guard_events") or [])
    if decision.failure_type is not None:
        events.append(
            {
                "layer": "output",
                "failure_type": decision.failure_type,
                "action": decision.action if decision.action == "block" else "redirect",
                "rule_id": decision.rule_id,
                "classification": decision.rule_id,
            }
        )
        logger.info(
            "agent output_guard action=%s rule=%s type=%s",
            decision.action,
            decision.rule_id,
            decision.failure_type,
        )
    if decision.action == "block":
        return {
            "answer": decision.answer,
            "outcome": "guard_blocked",
            "guard_events": events,
        }
    update: AgentState = {"answer": decision.answer, "guard_events": events}
    if state.get("redirect_required") and CASUAL_REDIRECT_SUFFIX not in decision.answer:
        # KB-only path may skip compose_answer; attach redirect here.
        if "tool_results" not in state:
            update["answer"] = f"{decision.answer.rstrip()}{CASUAL_REDIRECT_SUFFIX}"
    _ = kb_used  # reserved for future structural tightening
    return update


def route_after_receive(state: AgentState) -> str:
    return "reject_question" if state.get("outcome") == "invalid_question" else "input_guard"


def route_after_input_guard(state: AgentState) -> str:
    return END if state.get("outcome") == "guard_blocked" else "plan_sources"


_SOURCE_NODE = {"ticket": ("lookup_ticket", TICKET_TOOL), "inventory": ("lookup_inventory", INVENTORY_TOOL)}


def route_next_source(state: AgentState) -> str:
    """Next planned source not yet used, in plan order; ``compose_answer`` once all are done."""
    done = {r["tool"] for r in state.get("tool_results", [])}
    for source in state["plan"]["sources"]:
        if source == "knowledge_base":
            if "context" not in state:
                return "retrieve"
        elif _SOURCE_NODE[source][1] not in done:
            return _SOURCE_NODE[source][0]
    return "compose_answer"


def route_after_tool(state: AgentState) -> str:
    if state["tool_results"][-1]["status"] != "ok":
        return "tool_fallback"
    return route_next_source(state)


def route_after_retrieve(state: AgentState) -> str:
    return "generate_answer" if state.get("context") else "no_context_answer"


def route_after_answer(state: AgentState) -> str:
    return "compose_answer" if state.get("tool_results") else "output_guard"
