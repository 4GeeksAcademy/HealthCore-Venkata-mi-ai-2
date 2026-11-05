---
stamp: HC-MS7-PLAN-104
sequence: 104
milestone: MS7
date: 2026-11-04
title: Coordinator Knowledge Agent LangGraph Migration Plan
status: planned
phase: planning
summary: >
  Plan for "Support Agent with LangGraph, Part 1 of 2". Wraps the existing
  coordinator RAG (PLAN-102) in a compiled LangGraph StateGraph under
  services/knowledge_agent with a minimal explicit state, single-responsibility
  nodes (receive_question, retrieve, generate_answer, no_context_answer,
  reject_question), two real conditional edges, a build-time structural
  validator, SQLite checkpointing on every super-step (resumable), a SQLite
  run/step trace store with JSON export, trace-based evals in tests/pipelines
  (including BRIEFING grounding), and POST /agent/query that only invokes the
  graph. retrieve() and generate_answer() are reused from data/pipelines/rag.py.
related_paths:
  - docs/Project_Contexts/SupportAgentwithLangGraph_1.md
  - data/pipelines/rag.py
  - data/process/rag.py
  - services/knowledge_agent/
  - services/api/app/routers/agent.py
  - services/api/app/main.py
  - services/api/tests/test_agent.py
  - services/api/tests/conftest.py
  - tests/pipelines/test_agent_graph.py
  - tests/pipelines/test_agent_evals.py
  - tests/pipelines/agent_eval_cases.json
  - tests/pipelines/fixtures/agent_traces.json
  - scripts/record_agent_traces.py
  - docs/agent/langgraph-agent.md
  - pyproject.toml
  - uv.lock
  - services/api/requirements.txt
do_not_repeat:
  - Put the monolithic query() (retrieve + generate) inside a single node
  - Copy or rewrite retrieve(), embed(), build_prompt(), or generate_answer() into services/
  - Carry conversation history in the graph state (single-turn desk Q&A; the checkpointer thread is the resume mechanism)
  - Wire a straight-line graph with no conditional edges
  - Execute a graph that was not compiled and validated first
  - Store question or answer text in API traces by default (AGENT_TRACE_STORE_TEXT stays off outside eval runs)
  - Return chunks, scores, stack traces, or exception messages from POST /agent/query
  - Replace or weaken tests/pipelines/test_rag.py or services/api/tests/test_knowledge.py
  - Write anything under data/ (protected zone); eval cases and trace fixtures live in tests/pipelines/
  - Use pip install or pipenv (uv add only)
  - Commit .env files, keys, base URLs, or the local .state/ SQLite files
  - Save the agent Results eval without human approval
---

# HC-MS7-PLAN-104 — Coordinator Knowledge Agent LangGraph Migration Plan

## Problem

The coordinator knowledge assistant (PLAN-102) answers correctly but is a black box. `POST /knowledge/query` calls `query()`, which retrieves and then generates, and nothing records what was decided on the way. The tech lead's ticket (archived at [`docs/Project_Contexts/SupportAgentwithLangGraph_1.md`](../../docs/Project_Contexts/SupportAgentwithLangGraph_1.md)) asks for the same behaviour inside a LangGraph graph, with explicit state, single-responsibility nodes, conditional transitions, build-time compilation, checkpointing, and a queryable trace for every run. Part 2 (a new tool) will build on this and is out of scope.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Branch | `feature/langgraph-agent-base` (already checked out) |
| Dependencies | `uv add langgraph langgraph-checkpoint-sqlite` (installed 1.2.19 / 3.1.3). Same two lines in `services/api/requirements.txt` for the Docker image. |
| Package | `services/knowledge_agent/` (relative imports so it loads as `services.knowledge_agent` from tests and as `knowledge_agent` inside the API, where `services/` is on `sys.path`). |
| Reuse | Nodes call `data.pipelines.rag.retrieve` and `data.pipelines.rag.generate_answer` through an injectable `AgentDependencies` dataclass. `NO_CONTEXT_SENTENCE` and `KnowledgeBaseUnavailable` also come from `data/pipelines/rag.py`. `query()` is not called by the agent. Nothing in `data/` is edited. |
| Coexistence | `POST /knowledge/query` stays exactly as it is. New `POST /agent/query` (JWT) sits next to it. |

### State (minimal, explicit)

`AgentState` is a `TypedDict` with four keys only:

| Key | Written by | Why a node needs it |
|-----|------------|---------------------|
| `question` | `receive_question` | Normalised question, the input to `retrieve` and generation |
| `context` | `retrieve` | Chunks above `min_score` (`source_document`, `chunk_index`, `section`, `text`, `score`). Drives the second route. |
| `answer` | `generate_answer` / `no_context_answer` / `reject_question` | The partial, then final, answer |
| `outcome` | `receive_question` (invalid only) and every terminal node | `answered`, `no_context`, or `invalid_question`. Drives the first route and the endpoint status. |

No conversation history: the coordinator desk flow is single-turn, and each run gets its own checkpointer `thread_id` (= `run_id`), which is how a run is inspected or resumed.

### Nodes (single responsibility)

| Node | Does | Calls |
|------|------|-------|
| `receive_question` | Collapse whitespace; mark `invalid_question` when empty or over 1000 characters | — |
| `retrieve` | Fetch context above the threshold; log chunk ids and scores only | `rag.retrieve(question)` |
| `generate_answer` | Generate from the context `retrieve` already produced | `rag.generate_answer(question, context)` |
| `no_context_answer` | Honest "not enough information" reply plus "check with the relevant team"; no model call | `rag.NO_CONTEXT_SENTENCE` |
| `reject_question` | Clear message asking for a question; `END` | — |

### Edges (output conditions)

- `START` → `receive_question`
- `receive_question` → `route_after_receive`: `outcome == "invalid_question"` → `reject_question`, else `retrieve`
- `retrieve` → `route_after_retrieve`: empty `context` → `no_context_answer`, else `generate_answer`
- The three terminal nodes → `END`

Conditional edges declare their `path_map`, so the compiled graph knows every possible target.

### Compilation and build-time validation

`compile_agent_graph()` is the only way to get a runnable graph. It raises `AgentGraphBuildError` with a readable message when:

1. LangGraph's own `compile()` rejects the graph (for example, an edge to an unknown node). Verified in this session: LangGraph raises `ValueError: Found edge ending at unknown node`.
2. A node is not reachable from `START`, or cannot reach `END`. LangGraph 1.2.19 accepts orphan nodes silently (verified), so this check runs on `compiled.get_graph()`.
3. A node declares that it writes a key that is not in `AgentState`. LangGraph silently drops unknown keys (verified), so each node also gets a runtime guard that raises `AgentStateError` if it returns an undeclared key.

`AgentRunner.__init__` compiles. The API compiles once in the FastAPI lifespan, so a structural error stops startup instead of failing the first request.

### Checkpointing

`SqliteSaver` (`langgraph-checkpoint-sqlite`) writes a checkpoint after every super-step: input, `receive_question`, `retrieve`, and the terminal node. Default file `services/knowledge_agent/.state/checkpoints.sqlite` (gitignored; `AGENT_STATE_DIR` overrides). `AgentRunner.checkpoints(run_id)` lists them. `AgentRunner.resume(run_id)` calls `invoke(None)` on the same thread, so a run that failed in `generate_answer` resumes without re-running `retrieve`. Verified in the probe.

### Tracing (queryable, not console)

The runner drives the graph with `stream(stream_mode="updates")` and records every node update in a SQLite `TraceStore` (`.state/traces.sqlite`):

- `agent_runs`: `run_id`, `started_at`, `finished_at`, `status` (`running`, `completed`, `failed`), `outcome`, `failed_node`, `error_type`, `mode`, `labels`, `question_sha256`, `question_chars`, optional `question_text` / `answer_text`.
- `agent_steps`: `run_id`, `seq`, `node`, `status`, `duration_ms`, `output` JSON (chunk ids and scores for `retrieve`; answer length, Source line, and optional text for answer nodes).

Query helpers: `get_run`, `list_runs`, `node_sequence`, `export_json`. Text columns are filled only when `store_text=True` (eval recordings of synthetic questions). The API default is off, matching the PLAN-102 "never log the question" rule. LangSmith is optional: setting the `LANGSMITH_*` env vars turns on LangGraph's built-in export without code changes.

### Evals (`tests/pipelines/`, against the trace)

- `tests/pipelines/agent_eval_cases.json`: each case has a question and verifiable criteria (`expected_nodes`, `forbidden_nodes`, `expected_outcome`, `expected_top_source`, `answer_must_include` groups, `answer_must_not_include`).
- `scripts/record_agent_traces.py`: runs every case through the compiled graph and writes `tests/pipelines/fixtures/agent_traces.json` (plus the SQLite store). `--live` uses the real 4Geeks models and Qdrant from `.env`. `--offline` (default when no key) uses the real corpus, the real `setup()`, `retrieve()`, and `generate_answer()`, with injected doubles: in-memory Qdrant, a deterministic lexical embedding, and an extractive stand-in LLM that only quotes the top CONTEXT block. Each trace records its `mode`.
- `tests/pipelines/test_agent_evals.py`: reads the recorded trace only (no live call) and asserts per case. At least these:
  1. Grounding: "Is there a charge for cancelling 12 hours in advance?" → path `receive_question, retrieve, generate_answer`; top chunk `appointment-policy`; answer contains `50 USD`, `40 GBP`, and a Medicare/Medicaid mention.
  2. Grounding: US commercial insurers, new-patient documents, and referral escalation (`Marcus Reid`) return the BRIEFING facts.
  3. Routing: an off-topic question goes `retrieve` → `no_context_answer`, and `generate_answer` never runs.
  4. Routing: a blank question goes `receive_question` → `reject_question`, and `retrieve` never runs.
  5. Order: in every answered run, `retrieve` runs exactly once and before `generate_answer`.
  6. Trace integrity: every run is `completed`, step numbers are contiguous, and the SQLite store returns the same node sequence as the export.
- Single command: `uv run pytest tests/pipelines/test_agent_evals.py`.
- Mechanics tests with stubs in `tests/pipelines/test_agent_graph.py`: compile errors (orphan node, unknown edge, undeclared state key), routing, checkpoint list and resume after failure, trace on failure, and that generation receives exactly the chunks `retrieve` produced.

### Endpoint

`services/api/app/routers/agent.py`: `POST /agent/query` (JWT). The body is `question` (string, max 1000). Blank is allowed through so the graph's reject route decides. It calls `runner.run(question)` and returns `{answer, outcome, run_id}`. Error mapping only:

- `invalid_question` → 422 with the graph's message.
- `AgentRunFailed` caused by `KnowledgeBaseUnavailable` → 503 "The knowledge assistant is temporarily unavailable. Please try again. Reference: {run_id}".
- Any other `AgentRunFailed` → 500 "The knowledge assistant could not complete this request. Reference: {run_id}".

There is no stack trace and no exception text. `run_id` lets support find the trace.

## Steps

1. Dependencies (done in planning): `uv add`, then mirror in `services/api/requirements.txt`, and gitignore `services/knowledge_agent/.state/`.
2. `services/knowledge_agent/`: `state.py`, `nodes.py`, `graph.py`, `trace_store.py`, `runner.py`, `offline.py`, `__init__.py`, `README.md`.
3. API router, lifespan compile, conftest `AGENT_STATE_DIR` isolation, `services/api/tests/test_agent.py`.
4. Eval cases, recorder script, recorded fixture, `test_agent_evals.py`, `test_agent_graph.py`.
5. Docs: `docs/agent/langgraph-agent.md` (graph diagram, state justification, trace queries, run commands); `services/README.md` row.
6. Verify: new tests, existing `tests/pipelines/test_rag.py`, `services/api/tests/test_knowledge.py`, full API suite. Lint/tsc are not needed (no UI change).
7. Implementation stamp PLAN-105, then update `progress.md`. Present the "What We Will Evaluate" scores in chat. Save Results only after human approval (PLAN-106).

## Known limits

- This session has no `.env`, 4Geeks key, or Docker engine. The committed trace fixture is recorded `--offline` and labelled as such. Before opening the PR, re-record with `uv run python scripts/record_agent_traces.py --live` so the grounding gate runs against real model answers.
- Checkpoints hold full state (including the question) because resume needs it. They stay in the local gitignored `.state/` folder.

## Agent instructions

1. Implement exactly the nodes, edges, and state above. Do not add Part 2 tools.
2. Keep `/knowledge/query` and its tests untouched.
3. Do not save `memory-bank/evaluations/Results/LangGraphAgent-*.md` until the human approves the scores.
