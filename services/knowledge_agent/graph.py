"""Graph topology, build-time validation, and compilation.

``compile_agent_graph()`` is the only way to obtain a runnable graph. LangGraph
1.2 rejects edges to unknown nodes on its own, but it accepts orphan nodes and
silently drops state keys that are not in the schema, so both are checked here
before anything can execute.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any

from langgraph.graph import END, START, StateGraph

from .nodes import (
    AgentDependencies,
    compose_answer,
    make_generate_node,
    make_inventory_node,
    make_plan_node,
    make_retrieve_node,
    make_ticket_node,
    no_context_answer,
    receive_question,
    reject_question,
    route_after_answer,
    route_after_receive,
    route_after_retrieve,
    route_after_tool,
    route_next_source,
    tool_fallback,
)
from .state import STATE_KEYS, AgentState

GRAPH_NAME = "healthcore_knowledge_agent"
GRAPH_VERSION = "knowledge-agent/2"


class AgentGraphBuildError(RuntimeError):
    """The graph is structurally invalid and must not be executed."""


class AgentStateError(RuntimeError):
    """A node returned a state key it did not declare."""


@dataclass(frozen=True)
class NodeSpec:
    name: str
    fn: Callable[[AgentState], AgentState]
    writes: frozenset[str]


@dataclass(frozen=True)
class RouteSpec:
    source: str
    router: Callable[[AgentState], str]
    targets: tuple[str, ...]


@dataclass(frozen=True)
class GraphSpec:
    entry: str
    nodes: tuple[NodeSpec, ...]
    routes: tuple[RouteSpec, ...]
    edges: tuple[tuple[str, str], ...]


def default_spec(deps: AgentDependencies | None = None) -> GraphSpec:
    deps = deps or AgentDependencies()
    return GraphSpec(
        entry="receive_question",
        nodes=(
            NodeSpec("receive_question", receive_question, frozenset({"question", "outcome"})),
            NodeSpec("plan_sources", make_plan_node(deps), frozenset({"plan"})),
            NodeSpec("lookup_ticket", make_ticket_node(deps), frozenset({"tool_results"})),
            NodeSpec("lookup_inventory", make_inventory_node(deps), frozenset({"tool_results"})),
            NodeSpec("tool_fallback", tool_fallback, frozenset({"fallbacks"})),
            NodeSpec("retrieve", make_retrieve_node(deps), frozenset({"context"})),
            NodeSpec("generate_answer", make_generate_node(deps), frozenset({"answer", "outcome"})),
            NodeSpec("no_context_answer", no_context_answer, frozenset({"answer", "outcome"})),
            NodeSpec("compose_answer", compose_answer, frozenset({"answer", "outcome"})),
            NodeSpec("reject_question", reject_question, frozenset({"answer", "outcome"})),
        ),
        routes=(
            RouteSpec("receive_question", route_after_receive, ("plan_sources", "reject_question")),
            RouteSpec("plan_sources", route_next_source, ("lookup_ticket", "lookup_inventory", "retrieve")),
            RouteSpec(
                "lookup_ticket",
                route_after_tool,
                ("tool_fallback", "lookup_inventory", "retrieve", "compose_answer"),
            ),
            RouteSpec("lookup_inventory", route_after_tool, ("tool_fallback", "retrieve", "compose_answer")),
            RouteSpec("tool_fallback", route_next_source, ("lookup_inventory", "retrieve", "compose_answer")),
            RouteSpec("retrieve", route_after_retrieve, ("generate_answer", "no_context_answer")),
            RouteSpec("generate_answer", route_after_answer, ("compose_answer", END)),
            RouteSpec("no_context_answer", route_after_answer, ("compose_answer", END)),
        ),
        edges=(
            ("compose_answer", END),
            ("reject_question", END),
        ),
    )


def _guard(node: NodeSpec) -> Callable[[AgentState], AgentState]:
    @wraps(node.fn)
    def guarded(state: AgentState) -> AgentState:
        update = node.fn(state)
        undeclared = set(update or {}) - node.writes
        if undeclared:
            raise AgentStateError(
                f"Node '{node.name}' wrote undeclared state key(s) {sorted(undeclared)}"
            )
        return update

    return guarded


def _validate_contract(spec: GraphSpec) -> None:
    names = [node.name for node in spec.nodes]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise AgentGraphBuildError(f"Duplicate node name(s): {duplicates}")
    for node in spec.nodes:
        unknown = sorted(node.writes - STATE_KEYS)
        if unknown:
            raise AgentGraphBuildError(
                f"Node '{node.name}' declares unknown state key(s) {unknown}; "
                f"AgentState keys are {sorted(STATE_KEYS)}"
            )
    known = set(names) | {END}
    if spec.entry not in names:
        raise AgentGraphBuildError(f"Entry node '{spec.entry}' is not defined")
    for route in spec.routes:
        if route.source not in names:
            raise AgentGraphBuildError(f"Conditional edge starts at unknown node '{route.source}'")
        missing = sorted(set(route.targets) - known)
        if missing:
            raise AgentGraphBuildError(
                f"Conditional edge from '{route.source}' targets unknown node(s) {missing}"
            )


def _validate_topology(spec: GraphSpec) -> None:
    # Checked on the declared edges: compiled.get_graph() draws an implicit edge to
    # END for nodes with no outgoing edge, which would hide a dead end.
    names = {node.name for node in spec.nodes}
    forward: dict[str, set[str]] = {name: set() for name in names | {START, END}}
    backward: dict[str, set[str]] = {name: set() for name in names | {START, END}}
    pairs = [(START, spec.entry), *spec.edges]
    pairs += [(route.source, target) for route in spec.routes for target in route.targets]
    for source, target in pairs:
        forward[source].add(target)
        backward[target].add(source)

    def reach(start: str, adjacency: dict[str, set[str]]) -> set[str]:
        seen, queue = {start}, deque([start])
        while queue:
            for nxt in adjacency[queue.popleft()]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    nodes = names
    unreachable = sorted(nodes - reach(START, forward))
    if unreachable:
        raise AgentGraphBuildError(f"Node(s) not reachable from START: {unreachable}")
    dead_ends = sorted(nodes - reach(END, backward))
    if dead_ends:
        raise AgentGraphBuildError(f"Node(s) with no path to END: {dead_ends}")


def compile_agent_graph(
    spec: GraphSpec | None = None,
    *,
    deps: AgentDependencies | None = None,
    checkpointer: Any | None = None,
) -> Any:
    """Validate and compile. Raises ``AgentGraphBuildError`` on any structural problem."""
    spec = spec or default_spec(deps)
    _validate_contract(spec)
    try:
        builder = StateGraph(AgentState)
        for node in spec.nodes:
            builder.add_node(node.name, _guard(node))
        builder.add_edge(START, spec.entry)
        for route in spec.routes:
            builder.add_conditional_edges(
                route.source, route.router, {target: target for target in route.targets}
            )
        for source, target in spec.edges:
            builder.add_edge(source, target)
        compiled = builder.compile(checkpointer=checkpointer, name=GRAPH_NAME)
    except Exception as exc:
        raise AgentGraphBuildError(f"LangGraph rejected the agent graph: {exc}") from exc
    _validate_topology(spec)
    return compiled
