---
stamp: HC-MS8-PLAN-117
sequence: 117
milestone: MS8
date: 2026-11-09
title: Agent Memory and Self-Improvement Part 1 Implementation
status: implemented
phase: implementation
summary: >
  The coordinator agent proposes one operational fact per conversation and
  writes it only after a classified approve or edit. Memory is SQLite
  agent_memory.sqlite. Qdrant healthcore_knowledge and the Celery Redis
  broker are untouched. PHI is refused before it is shown or stored.
  Graph version stays knowledge-agent/2. Pytest memory, graph, and tools
  79 passed. Agent API and recorded evals 111 passed, 10 skipped. Rubric
  results stay in chat until the human approves them. Does not close MS8.
related_paths:
  - docs/agent/agent-memory.md
  - docs/Project_Contexts/healthcore-memory-BRIEFING.md
  - services/knowledge_agent/memory/
  - services/knowledge_agent/runner.py
  - services/api/app/routers/agent.py
  - services/api/tests/test_agent.py
  - tests/pipelines/test_agent_memory.py
  - docs/agent/langgraph-agent.md
do_not_repeat:
  - Write agent memory into healthcore_knowledge or any other knowledge collection
  - Put desk-memory keys on the Celery Redis broker
  - Bump GRAPH_VERSION or change ordinary desk-question node paths
  - Store patient identifiers or the raw text of a PHI turn in memory, audit, or traces
  - Treat a message as approval because it contains the letters yes
  - Allow two pending proposals in one conversation
  - Save memory-bank/evaluations/Results/AgentMemory-*.md before human approval
  - Close MS8
  - Commit on the human's behalf
  - Call stage_legacy_fact from the agent turn
---

# HC-MS8-PLAN-117 — Agent memory implementation

Follows [HC-MS8-PLAN-116](./HC-MS8-PLAN-116-20261109-agent-memory-plan.md). Design: [`docs/agent/agent-memory.md`](../../docs/agent/agent-memory.md).

## What shipped

- `MemoryStore` reads matching facts and commits a fact only from an approve or edit that passes the PHI gate again.
- `assess_message` returns a structured `memory_proposal` or a `phi` / `policy` block. Most turns return neither.
- `classify_decision` returns `approve`, `reject`, `edit`, or `ambiguous`. Below confidence 0.75 the proposal is rejected.
- One pending row per conversation. A pending row older than 24 hours is expired as a rejection.
- Consolidation expires by kind (90 / 90 / 180 / 365 days), drops exact duplicates, re-checks PHI and redacts the stored text, and caps active facts at 40.
- `POST /agent/query` accepts `conversation_id` and returns it with `memory_event`. The actor stored on a write is `staff:{id}`.

## Verification

`python -m pytest tests/pipelines/test_agent_memory.py tests/pipelines/test_agent_graph.py tests/pipelines/test_agent_tools.py`: **79 passed**.

`python -m pytest services/api/tests/test_agent.py tests/pipelines/test_agent_evals.py`: **111 passed, 10 skipped**.

No browser pass. This change is the agent API, and the desk has no chat page.

## Agent instructions

1. Do not write the AgentMemory Results file until the human approves the rubric in chat.
2. Do not close MS8. Do not bump `GRAPH_VERSION`.
3. Do not add a direct write from the turn into `stage_legacy_fact`.
4. The human commits. Do not commit on their behalf.
