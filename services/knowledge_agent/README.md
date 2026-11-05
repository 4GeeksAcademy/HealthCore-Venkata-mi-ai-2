# `knowledge_agent`

Coordinator knowledge assistant as a compiled LangGraph graph (Support Agent with LangGraph, Part 1). Full design, trace queries, and eval commands: [`docs/agent/langgraph-agent.md`](../../docs/agent/langgraph-agent.md).

| Module | Purpose |
|--------|---------|
| `state.py` | `AgentState` (`question`, `context`, `answer`, `outcome`) |
| `nodes.py` | Nodes and routing functions. Retrieval and generation come from `data/pipelines/rag.py` via `AgentDependencies`. |
| `graph.py` | Topology, build-time validation, `compile_agent_graph()` |
| `runner.py` | `AgentRunner`: run, trace, checkpoint, resume. `get_agent_runner()` for the API. |
| `trace_store.py` | SQLite `agent_runs` / `agent_steps` |
| `offline.py` | Eval-only doubles for recording traces without the model gateway |

Runtime files go to `.state/` (gitignored; `AGENT_STATE_DIR` overrides). `AGENT_TRACE_STORE_TEXT=true` stores question and answer text in traces (eval recordings only).
