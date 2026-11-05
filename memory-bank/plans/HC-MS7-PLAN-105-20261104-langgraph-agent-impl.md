---
stamp: HC-MS7-PLAN-105
sequence: 105
milestone: MS7
date: 2026-11-04
title: Coordinator Knowledge Agent LangGraph Implementation
status: implemented
phase: implementation
summary: >
  Implements PLAN-104 (Support Agent with LangGraph, Part 1). Compiled StateGraph
  in services/knowledge_agent with four-key state, five single-responsibility
  nodes, two conditional edges, build-time validation (unknown edge, orphan,
  dead end, undeclared state key), SqliteSaver checkpoints per super-step with
  resume, SQLite run/step trace store, POST /agent/query compiled at API startup.
  Trace-based evals 29 passed / 5 skipped against an offline-recorded trace;
  graph mechanics 18 passed; existing RAG tests unchanged and passing; API suite
  79 passed. Live re-record pending (no .env or Docker in session). Eval Results
  pending human approval. Does not close MS7.
related_paths:
  - services/knowledge_agent/
  - services/api/app/routers/agent.py
  - services/api/app/main.py
  - services/api/tests/test_agent.py
  - services/api/tests/conftest.py
  - services/api/requirements.txt
  - services/README.md
  - tests/pipelines/test_agent_graph.py
  - tests/pipelines/test_agent_evals.py
  - tests/pipelines/agent_eval_cases.json
  - tests/pipelines/fixtures/agent_traces.json
  - scripts/record_agent_traces.py
  - docs/agent/langgraph-agent.md
  - docs/agent/eval-output.txt
  - pyproject.toml
  - uv.lock
  - .gitignore
do_not_repeat:
  - Validate dead ends on compiled.get_graph() (it draws an implicit edge to END); validate on the declared GraphSpec
  - Trust LangGraph to reject orphan nodes or unknown state keys (1.2.19 accepts both silently)
  - Call query() from any node, or move retrieval/generation into the router
  - Present the offline trace as proof of live-model faithfulness
  - Run `uv add` without --system-certs on this machine (TLS UnknownIssuer)
  - Promise `uv run pytest tests/pipelines` for the whole folder (test_pipeline.py needs sqlalchemy/prefect from the API requirements)
  - Save the agent Results eval without human approval
  - Rewrite PLAN-104
---

# HC-MS7-PLAN-105 — Coordinator Knowledge Agent LangGraph Implementation

## What shipped

| Piece | Location |
|-------|----------|
| State (`question`, `context`, `answer`, `outcome`) | `services/knowledge_agent/state.py` |
| Nodes + routers (reuse `rag.retrieve` / `rag.generate_answer`) | `services/knowledge_agent/nodes.py` |
| Topology, validation, `compile_agent_graph()` | `services/knowledge_agent/graph.py` |
| Runner: stream-based tracing, `SqliteSaver`, `checkpoints()`, `resume()` | `services/knowledge_agent/runner.py` |
| Trace store (`agent_runs`, `agent_steps`) | `services/knowledge_agent/trace_store.py` |
| Offline eval doubles | `services/knowledge_agent/offline.py` |
| `POST /agent/query` → `{answer, outcome, run_id}`; 422 / 503 / 500 with `Reference: run_id` | `services/api/app/routers/agent.py`; compiled in `main.py` lifespan |
| Eval cases (8), recorder, trace export | `tests/pipelines/agent_eval_cases.json`, `scripts/record_agent_traces.py`, `tests/pipelines/fixtures/agent_traces.json` |
| Evals / mechanics / API tests | `tests/pipelines/test_agent_evals.py`, `tests/pipelines/test_agent_graph.py`, `services/api/tests/test_agent.py` |
| Design doc + eval console output | `docs/agent/langgraph-agent.md`, `docs/agent/eval-output.txt` |

## Deviations from PLAN-104

- Reachability and dead-end checks run on the declared `GraphSpec`, not `compiled.get_graph()`, because the drawn graph adds an implicit edge to `END` and hid a dead end in testing.
- The offline recorder uses `min_score` 0.25 for the lexical embedding. Off-topic top-1 scores were 0.185 or lower, and correct chunks scored 0.33 or higher. Live keeps 0.30.

## Verification (2026-11-04)

- `uv run pytest tests/pipelines/test_agent_evals.py -v`: **29 passed, 5 skipped**. The skips are Humana, which needs a live trace, and "retrieve not on route" for the blank question.
- Negative check: a corrupted trace (cancellation answer without the fee, and an off-topic run through `generate_answer`) gives **3 failed**.
- `tests/pipelines/test_agent_graph.py`: **18 passed**. `tests/pipelines/test_rag.py`: **13 passed**, unchanged.
- `python -m pytest tests/pipelines`: **74 passed, 5 skipped**. `python -m pytest` (API): **79 passed**, up from 71 (+8 agent).
- Not done: no live-model trace. The session has no `.env`, 4Geeks key, or Docker engine. LangGraph was also installed into the system Python (`uv pip install --system`) for the API suite.

## Agent instructions

1. Before the PR, run `uv run python scripts/record_agent_traces.py --mode live` with the local `.env` and indexed Qdrant, then re-run the evals. The Humana case must pass, not skip.
2. Rebuild the API image (`docker compose build api`). `requirements.txt` now includes LangGraph.
3. Present the "What We Will Evaluate" scores in chat. Write `memory-bank/evaluations/Results/LangGraphAgent-20261104.md` only after human approval (next stamp).
4. Part 2 adds a tool node and a conditional edge. Add both to `default_spec()`, so they get the same validation, and add eval cases. Do not change the existing nodes.
