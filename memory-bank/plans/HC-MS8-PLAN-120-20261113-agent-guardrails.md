---
stamp: HC-MS8-PLAN-120
sequence: 120
milestone: MS8
date: 2026-11-13
title: Agent Harness and Guardrails Part 2 Implementation
status: implemented
phase: implementation
summary: >
  MS8 Part 2 (#SEC-114). The same coordinator agent gains multi-layer
  input/output/security guardrails, secured system prompt, RAG isolation,
  PHI-on-output, GuardrailStore, and GET /agent/guardrails/summary. Graph
  version is knowledge-agent/3. Pytest pipelines agent suites 198 passed,
  10 skipped; API agent tests 12 passed. Rubric results stay in chat until
  the human approves. Does not close MS8.
related_paths:
  - docs/Project_Contexts/healthcore-harness-BRIEFING.md
  - docs/agent/agent-guardrails.md
  - services/knowledge_agent/guardrails/
  - services/knowledge_agent/graph.py
  - services/knowledge_agent/nodes.py
  - services/knowledge_agent/runner.py
  - services/knowledge_agent/state.py
  - services/knowledge_agent/memory/phi.py
  - data/pipelines/rag.py
  - services/api/app/routers/agent.py
  - tests/pipelines/test_agent_guardrails.py
do_not_repeat:
  - Invent a second agent for harness work
  - Rely on a live LLM as the only harness acceptance gate
  - Treat RAG or tool text as system instructions
  - Collapse the harness into a single generic filter
  - Log raw PHI or full jailbreak payloads in guardrail events
  - Save memory-bank/evaluations/Results/HarnessGuardrails-*.md before human approval
  - Close MS8
  - Commit on the human's behalf
  - Rewrite PLAN-119
---

# HC-MS8-PLAN-120 — Agent harness and guardrails implementation

Follows [HC-MS8-PLAN-119](./HC-MS8-PLAN-119-20261113-agent-guardrails-plan.md). Design: [`docs/agent/agent-guardrails.md`](../../docs/agent/agent-guardrails.md).

## What shipped

- Package `services/knowledge_agent/guardrails/` — input classifier, output validator, external sanitizer, canned refusals, `GuardrailStore`.
- Graph nodes `input_guard` and `output_guard`; `GRAPH_VERSION` = `knowledge-agent/3`.
- Hardened `SYSTEM_PROMPT` + untrusted CONTEXT delimiters in `build_prompt`.
- PHI scan extended with quasi-identifiers; used on output before return.
- JWT `GET /agent/guardrails/summary`.
- Deterministic tests in `tests/pipelines/test_agent_guardrails.py`.

## Verification

`python -m pytest tests/pipelines/test_agent_guardrails.py tests/pipelines/test_agent_graph.py tests/pipelines/test_agent_memory.py tests/pipelines/test_agent_tools.py tests/pipelines/test_agent_evals.py`: **198 passed, 10 skipped**.

`cd services/api && python -m pytest tests/test_agent.py`: **12 passed**.

## Agent instructions

1. Do not write the HarnessGuardrails Results file until the human approves the rubric in chat.
2. Do not close MS8.
3. Do not commit.
4. Do not rewrite PLAN-119.
