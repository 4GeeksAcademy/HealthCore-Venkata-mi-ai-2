# `knowledge_agent`

Coordinator knowledge assistant as a compiled LangGraph graph (Support Agent with LangGraph, Parts 1 and 2). It answers from the knowledge base, the live incident manager, the inventory service, or a mix of them. Full design, trace queries, and eval commands: [`docs/agent/langgraph-agent.md`](../../docs/agent/langgraph-agent.md).

| Module | Purpose |
|--------|---------|
| `state.py` | `AgentState` (`question`, `plan`, `tool_results`, `fallbacks`, `context`, `answer`, `outcome`) |
| `planner.py` | `SourcePlanner` (LLM plan; the rules planner takes over on failure) and `rules_plan` |
| `tools/` | Inventory stays a direct read of the inventory API. Ticket lookup is `McpIncidentLookup` only (MCP server, scope `incidents:read`). |
| `nodes.py` | Nodes and routing functions. Retrieval and generation come from `data/pipelines/rag.py` via `AgentDependencies`. |
| `graph.py` | Topology, build-time validation, `compile_agent_graph()` |
| `runner.py` | `AgentRunner`: run, trace, checkpoint, resume. `get_agent_runner()` for the API. |
| `trace_store.py` | SQLite `agent_runs` / `agent_steps`, `source_sequence()` |
| `offline.py` | Eval-only doubles for recording traces without the model gateway |

Inventory reads `HEALTHCORE_API_URL` (default `http://localhost:8001`), `AGENT_SERVICE_EMAIL`, and `AGENT_SERVICE_PASSWORD`. Ticket questions use the MCP server: `HEALTHCORE_MCP_URL`, `MCP_TOKEN_URL`, `MCP_AGENT_CLIENT_ID`, and `MCP_AGENT_CLIENT_SECRET` (scope `incidents:read` only). If those are missing, the ticket tool returns `auth_failed` and the agent gives the fallback answer. It does not call `/api/incidents` itself.

Runtime files go to `.state/` (gitignored; `AGENT_STATE_DIR` overrides). `AGENT_TRACE_STORE_TEXT=true` stores question and answer text in traces (eval recordings only).
