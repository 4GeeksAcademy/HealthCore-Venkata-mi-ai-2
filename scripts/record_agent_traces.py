"""Record one traced run of the coordinator knowledge agent per eval case.

Usage (from repo root):

    uv run python scripts/record_agent_traces.py                 # live if OPENAI_API_KEY is set, else offline
    uv run python scripts/record_agent_traces.py --mode live     # real 4Geeks models + Qdrant (.env), LLM planner
    uv run python scripts/record_agent_traces.py --mode live --setup   # re-index first
    uv run python scripts/record_agent_traces.py --mode offline  # real corpus/setup/retrieve/generate_answer,
                                                                 # in-memory Qdrant, lexical embedding, extractive LLM,
                                                                 # rules planner

Ticket questions call the MCP server. Inventory still calls the HealthCore API. Before recording:

    cd services/api && python seed.py            # inventory seed + scripts/samples/incidents-healthcore.csv
    python -m uvicorn app.main:app --port 8001   # JWT_SECRET_KEY set
    # env: HEALTHCORE_API_URL, AGENT_SERVICE_EMAIL, AGENT_SERVICE_PASSWORD
    #      HEALTHCORE_MCP_URL, MCP_TOKEN_URL, MCP_AGENT_CLIENT_ID, MCP_AGENT_CLIENT_SECRET

Cases with ``tool_override`` point the ticket tool at a closed local port
(``unreachable``) or at a local server that accepts and never answers
(``silent``), so the outage and timeout fallbacks are real network conditions.

Writes the queryable SQLite trace to ``services/knowledge_agent/.state/eval/`` and the
export the evals read to ``tests/pipelines/fixtures/agent_traces.json``.
Exit code 1 if any run failed or the API preflight fails.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import sys
import threading
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402

from data.pipelines.rag import default_min_score  # noqa: E402
from data.process.rag import embedding_model, generation_model  # noqa: E402
from services.knowledge_agent import (  # noqa: E402
    GRAPH_VERSION,
    AgentDependencies,
    AgentRunFailed,
    AgentRunner,
    rules_plan,
)
from services.knowledge_agent.offline import (  # noqa: E402
    OFFLINE_MIN_SCORE,
    build_offline_dependencies,
)
from services.knowledge_agent.tools import (  # noqa: E402
    TOOL_TIMEOUT_SECONDS,
    InventoryLookupTool,
    ReadOnlyApiSession,
    ServiceCredentials,
    TicketLookupInput,
)
from services.knowledge_agent.tools.mcp_incidents import McpIncidentLookup  # noqa: E402

CASES_PATH = REPO_ROOT / "tests" / "pipelines" / "agent_eval_cases.json"
EXPORT_PATH = REPO_ROOT / "tests" / "pipelines" / "fixtures" / "agent_traces.json"
STATE_DIR = REPO_ROOT / "services" / "knowledge_agent" / ".state" / "eval"


def _closed_port_url() -> str:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return f"http://127.0.0.1:{port}"


@contextmanager
def _silent_server() -> Iterator[str]:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    server.settimeout(0.2)
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept() -> None:
        while not stop.is_set():
            try:
                held.append(server.accept()[0])
            except OSError:
                continue

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.getsockname()[1]}"
    finally:
        stop.set()
        thread.join(1)
        for conn in held:
            conn.close()
        server.close()


def _preflight(credentials: ServiceCredentials | None) -> str | None:
    if credentials is None:
        return "set AGENT_SERVICE_EMAIL and AGENT_SERVICE_PASSWORD (an active staff account on the API)"
    lookup = McpIncidentLookup.from_env()
    if not lookup.configured:
        return "set HEALTHCORE_MCP_URL, MCP_TOKEN_URL, MCP_AGENT_CLIENT_ID, and MCP_AGENT_CLIENT_SECRET"
    probe = lookup(TicketLookupInput(ticket_id="INC-0042"))
    if probe.status != "ok":
        return (
            f"MCP incident preflight returned {probe.status}; start the MCP server and the API, "
            "and load scripts/samples/incidents-healthcore.csv"
        )
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mode", choices=["auto", "live", "offline"], default="auto")
    parser.add_argument("--setup", action="store_true", help="live only: re-index the knowledge base first")
    args = parser.parse_args()

    mode = args.mode
    if mode == "auto":
        mode = "live" if os.getenv("OPENAI_API_KEY") else "offline"

    credentials = ServiceCredentials.from_env()
    problem = _preflight(credentials)
    if problem:
        print(f"Preflight failed: {problem}", file=sys.stderr)
        return 1
    assert credentials is not None
    session = ReadOnlyApiSession(credentials)
    tools = {"lookup_ticket": McpIncidentLookup.from_env(), "lookup_inventory": InventoryLookupTool(session)}

    if mode == "live":
        deps = AgentDependencies(**tools)
        models = {"embedding": embedding_model(), "generation": generation_model(), "planner": generation_model()}
        min_score = default_min_score()
        if args.setup:
            from data.process.rag import setup

            print(f"Indexed {setup()} chunks")
    else:
        deps = replace(build_offline_dependencies(), plan_sources=rules_plan, **tools)
        models = {
            "embedding": "offline lexical-hash-1024",
            "generation": "offline extractive stand-in",
            "planner": "rules",
        }
        min_score = OFFLINE_MIN_SCORE

    shutil.rmtree(STATE_DIR, ignore_errors=True)
    runner = AgentRunner(deps=deps, state_dir=STATE_DIR, store_text=True, mode=mode)
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]

    def runner_for(base_url: str) -> AgentRunner:
        broken = McpIncidentLookup(
            mcp_url=base_url,
            token_url=f"{base_url}/oauth/token",
            client_id="trace-probe",
            client_secret="trace-probe",
            timeout_seconds=TOOL_TIMEOUT_SECONDS,
        )
        return AgentRunner(
            deps=replace(deps, lookup_ticket=broken),
            checkpointer=InMemorySaver(),
            trace_store=runner.traces,
            store_text=True,
            mode=mode,
        )

    failures = 0
    run_ids: list[str] = []
    print(f"mode={mode} graph={GRAPH_VERSION} min_score={min_score} tool_timeout={TOOL_TIMEOUT_SECONDS}s")
    for case in cases:
        override = case.get("tool_override")
        try:
            if override == "silent":
                with _silent_server() as url:
                    result = runner_for(url).run(case["question"], labels={"case_id": case["id"]})
            elif override == "unreachable":
                result = runner_for(_closed_port_url()).run(case["question"], labels={"case_id": case["id"]})
            else:
                result = runner.run(case["question"], labels={"case_id": case["id"]})
            run_ids.append(result.run_id)
            path = " -> ".join(runner.traces.node_sequence(result.run_id))
            print(f"  {case['id']:<36} {result.outcome:<17} {path}")
        except AgentRunFailed as exc:
            failures += 1
            run_ids.append(exc.run_id)
            print(f"  {case['id']:<36} FAILED at {exc.node} ({exc.error_type})")

    export = {
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "mode": mode,
        "graph_version": GRAPH_VERSION,
        "models": models,
        "min_score": min_score,
        "tools": {
            "transport": "MCP Streamable HTTP for tickets; HTTP for inventory",
            "timeout_seconds": TOOL_TIMEOUT_SECONDS,
            "incident_manager": ["MCP incident_check_status"],
            "inventory_manager": ["GET /inventory/products"],
        },
        "graph_mermaid": runner.graph.get_graph().draw_mermaid(),
        "runs": runner.traces.export(run_ids),
    }
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(json.dumps(export, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    runner.close()
    session.close()
    if mode == "live":
        from data.process.rag import get_qdrant_client

        get_qdrant_client().close()
    print(f"Trace store: {STATE_DIR.relative_to(REPO_ROOT) / 'traces.sqlite'}")
    print(f"Export:      {EXPORT_PATH.relative_to(REPO_ROOT)} ({len(run_ids)} runs)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
