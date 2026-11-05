# `knowledge_agent`

Coordinator knowledge assistant as a compiled LangGraph graph (Support Agent with LangGraph, Parts 1 and 2). It answers from the knowledge base, the live incident manager, the inventory service, or a mix of them. Full design, trace queries, and eval commands: [`docs/agent/langgraph-agent.md`](../../docs/agent/langgraph-agent.md).

| Module | Purpose |
|--------|---------|
| `state.py` | `AgentState` (`question`, `plan`, `tool_results`, `fallbacks`, `context`, `answer`, `outcome`) |
| `planner.py` | `SourcePlanner` (LLM plan; the rules planner takes over on failure) and `rules_plan` |
| `tools/` | Typed, read-only tools: `ticket_lookup`, `inventory_lookup`, and the shared `ReadOnlyApiSession` (GET only, 4.0 s deadline) |
| `nodes.py` | Nodes and routing functions. Retrieval and generation come from `data/pipelines/rag.py` via `AgentDependencies`. |
| `graph.py` | Topology, build-time validation, `compile_agent_graph()` |
| `runner.py` | `AgentRunner`: run, trace, checkpoint, resume. `get_agent_runner()` for the API. |
| `trace_store.py` | SQLite `agent_runs` / `agent_steps`, `source_sequence()` |
| `offline.py` | Eval-only doubles for recording traces without the model gateway |

Tools read `HEALTHCORE_API_URL` (default `http://localhost:8001`), `AGENT_SERVICE_EMAIL`, and `AGENT_SERVICE_PASSWORD` from the environment. If the credentials are missing, a tool returns `auth_failed` and the agent gives the fallback answer.

Runtime files go to `.state/` (gitignored; `AGENT_STATE_DIR` overrides). `AGENT_TRACE_STORE_TEXT=true` stores question and answer text in traces (eval recordings only).
