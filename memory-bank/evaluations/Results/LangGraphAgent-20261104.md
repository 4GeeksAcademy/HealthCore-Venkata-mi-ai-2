# Support Agent with LangGraph — Part 1 Evaluation

**Date:** 2026-11-04  
**Rubric:** Support Agent with LangGraph, Part 1 of 2 — "What We Will Evaluate" (11 checks)  
**Implementation as of:** [HC-MS7-PLAN-105](../../plans/HC-MS7-PLAN-105-20261104-langgraph-agent-impl.md)  
**Saved after:** [HC-MS7-PLAN-106](../../plans/HC-MS7-PLAN-106-20261104-langgraph-agent-eval-save.md); re-run on a live trace under [HC-MS7-PLAN-107](../../plans/HC-MS7-PLAN-107-20261104-langgraph-agent-live-trace.md)  
**Overall: PASS (11/11)** against a **live** trace (real 4Geeks models, Qdrant `healthcore_knowledge`, 14 chunks).

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/SupportAgentwithLangGraph_1.md`](../../../docs/Project_Contexts/SupportAgentwithLangGraph_1.md) |
| Plan | [HC-MS7-PLAN-104](../../plans/HC-MS7-PLAN-104-20261104-langgraph-agent-plan.md) |
| Agent package | [`services/knowledge_agent/`](../../../services/knowledge_agent/) |
| Endpoint | [`services/api/app/routers/agent.py`](../../../services/api/app/routers/agent.py) |
| Reused RAG | [`data/pipelines/rag.py`](../../../data/pipelines/rag.py), [`data/process/rag.py`](../../../data/process/rag.py) (unchanged) |
| Evals | [`tests/pipelines/test_agent_evals.py`](../../../tests/pipelines/test_agent_evals.py), [`tests/pipelines/agent_eval_cases.json`](../../../tests/pipelines/agent_eval_cases.json) |
| Trace export | [`tests/pipelines/fixtures/agent_traces.json`](../../../tests/pipelines/fixtures/agent_traces.json) |
| Eval output | [`docs/agent/eval-output.txt`](../../../docs/agent/eval-output.txt) |
| Design doc | [`docs/agent/langgraph-agent.md`](../../../docs/agent/langgraph-agent.md) |

Saved after human approval. Same-day re-evals overwrite this file only. Does not close MS7. Does not replace [RAGKnowledgeBase-20261102](./RAGKnowledgeBase-20261102.md).

## Method

- Recorded one traced run per eval case with `scripts/record_agent_traces.py --mode live --setup`. The models were `pplx-embed-v1-0.6b` (embeddings) and `gpt-6-luna` (generation), with `min_score` 0.30. `setup()` indexed 14 chunks.
- `uv run pytest tests/pipelines/test_agent_evals.py -v`: **33 passed, 1 skipped**. The skip is the retrieval check, which does not apply to the blank-question route. The live-only Humana case passes.
- Live answers: the cancellation answer gives 50 USD / 40 GBP for private pay and the Medicare/Medicaid exemption. The Humana answer says it is not on the documented list, refers to Tom Callahan in billing, and splits US and UK. Both end with a `Source:` line.
- The earlier offline recording gave 29 passed, 5 skipped. It is superseded by the live trace.
- Negative check: a deliberately corrupted trace (fee removed from the cancellation answer, off-topic run sent through `generate_answer`) gives **3 failed**.
- `tests/pipelines/test_agent_graph.py`: **18 passed**. `tests/pipelines/test_rag.py`: **13 passed**, unchanged.
- `python -m pytest tests/pipelines`: **74 passed, 5 skipped**. API suite `python -m pytest`: **79 passed**, up from 71.

## Rubric

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | State is minimal and explicit, with no unjustified history | Pass | `AgentState` has `question`, `context`, `answer`, and `outcome`. Single-turn; resume uses the checkpointer thread. |
| 2 | Single-responsibility nodes for receive, retrieve, generate | Pass | `receive_question`, `retrieve`, `generate_answer`, plus `no_context_answer` and `reject_question` |
| 3 | Edges set by output conditions | Pass | `route_after_receive` (invalid → reject) and `route_after_retrieve` (empty context → honest answer) |
| 4 | Compiled before execution; clear error on structural problems | Pass | `compile_agent_graph()` runs in the API lifespan. `AgentGraphBuildError` for unknown edge, orphan, dead end, and undeclared state key (tested). |
| 5 | Verifiable checkpointing | Pass | `SqliteSaver` checkpoints at steps -1 to 3. Resume after a generation failure does not re-run retrieval (tested). |
| 6 | Every run produces a queryable trace | Pass | SQLite `agent_runs` / `agent_steps`, reopened from disk in tests; JSON export |
| 7 | At least 3 runnable evals in `tests/pipelines/`, one asserting BRIEFING grounding | Pass | 8 cases, single command. Grounding is checked on 50 USD / 40 GBP / Medicare, US insurers, new-patient documents, Marcus Reid, and the Humana billing check, all against live model answers. |
| 8 | Existing RAG tests still pass | Pass | `test_rag.py` 13 passed, `test_knowledge.py` unchanged and passing |
| 9 | Endpoint invokes the graph only; errors hide internals | Pass | `POST /agent/query` returns 422, 503, or 500 with `Reference: run_id`. Tests show no exception text in responses. |
| 10 | Retrieval and generation are separate nodes; no wrapped `query()` | Pass | Tested: generation receives exactly the retrieved chunks, and nodes never call `query()` |
| 11 | Existing `retrieve` / `embed` / `query` reused, not rewritten | Pass | `AgentDependencies` defaults are `rag.retrieve` and `rag.generate_answer`; `data/` untouched |

The live trace export is the PR artifact. The `.env` stays local and gitignored, and the export contains no key or base URL.
