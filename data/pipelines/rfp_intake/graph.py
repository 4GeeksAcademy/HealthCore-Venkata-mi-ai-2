"""Dedicated rfp_intake graph. Build fails if a knowledge-agent node is present."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from . import GRAPH_NAME
from .nodes import (
    RfpDeps,
    classify_node,
    convert_node,
    department_worker_node,
    extract_metadata_node,
    fan_out,
    orchestrate_node,
    persist_complete_node,
    persist_discard_node,
    readability_node,
    route_after_classify,
    screen_phi_node,
    synthesize_node,
)
from .state import RfpState

REQUIRED_NODES = frozenset(
    {
        "convert",
        "readability",
        "screen_phi",
        "classify",
        "persist_discard",
        "extract_metadata",
        "orchestrate",
        "department_worker",
        "synthesize",
        "persist_complete",
    }
)
FORBIDDEN_NODES = frozenset({"generate_answer", "retrieve", "receive_question"})


class RfpGraphBuildError(RuntimeError):
    """The intake graph is structurally invalid and must not run."""


def build_graph(deps: RfpDeps | None = None):
    deps = deps or RfpDeps()
    graph = StateGraph(RfpState)
    graph.add_node("convert", convert_node(deps))
    graph.add_node("readability", readability_node(deps))
    graph.add_node("screen_phi", screen_phi_node)
    graph.add_node("classify", classify_node(deps))
    graph.add_node("persist_discard", persist_discard_node)
    graph.add_node("extract_metadata", extract_metadata_node(deps))
    graph.add_node("orchestrate", orchestrate_node)
    graph.add_node("department_worker", department_worker_node(deps))
    graph.add_node("synthesize", synthesize_node(deps))
    graph.add_node("persist_complete", persist_complete_node)

    graph.add_edge(START, "convert")
    graph.add_edge("convert", "readability")
    graph.add_edge("readability", "screen_phi")
    graph.add_edge("screen_phi", "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {"extract_metadata": "extract_metadata", "persist_discard": "persist_discard"},
    )
    graph.add_edge("persist_discard", END)
    graph.add_edge("extract_metadata", "orchestrate")
    graph.add_conditional_edges("orchestrate", fan_out, ["department_worker"])
    graph.add_edge("department_worker", "synthesize")
    graph.add_edge("synthesize", "persist_complete")
    graph.add_edge("persist_complete", END)

    compiled = graph.compile()
    names = set(compiled.get_graph().nodes)
    missing = REQUIRED_NODES - names
    if missing:
        raise RfpGraphBuildError(f"missing nodes: {sorted(missing)}")
    mixed = FORBIDDEN_NODES & names
    if mixed:
        raise RfpGraphBuildError(f"knowledge-agent nodes present: {sorted(mixed)}")
    if GRAPH_NAME == "healthcore_knowledge_agent":
        raise RfpGraphBuildError("intake graph reused the knowledge-agent name")
    return compiled


def initial_state(ticket_id: str) -> RfpState:
    return {
        "ticket_id": ticket_id,
        "markdown": "",
        "redacted_markdown": "",
        "readability": {},
        "is_rfp": False,
        "discard_reason_code": "",
        "phi_detected": False,
        "metadata": {},
        "unknown_departments": [],
        "work_items": [],
        "section_results": [],
        "conflicts": [],
        "sales_summary": "",
        "summary_source": "",
        "handoff": {},
        "status": "analyzing",
        "_ordered_sections": [],
    }
