---
stamp: HC-MS8-PLAN-119
sequence: 119
milestone: MS8
date: 2026-11-13
title: Agent Harness and Guardrails Part 2 Plan
status: planned
phase: planning
summary: >
  Plan for MS8 Part 2 (#SEC-114). The same coordinator knowledge agent gains a
  multi-layer harness: secured system prompt, deterministic input and output
  guards (including PHI-on-output), RAG/tool content isolation, guardrail event
  logging with GET /agent/guardrails/summary, and CI-stable tests. Graph version
  bumps to knowledge-agent/3. Does not close MS8. Results wait for human approval.
related_paths:
  - docs/Project_Contexts/MS8-Harness_and_guardrails.md
  - docs/Project_Contexts/healthcore-harness-BRIEFING.md
  - docs/agent/agent-guardrails.md
  - services/knowledge_agent/guardrails/
  - services/knowledge_agent/graph.py
  - services/knowledge_agent/nodes.py
  - data/pipelines/rag.py
  - services/api/app/routers/agent.py
  - tests/pipelines/test_agent_guardrails.py
do_not_repeat:
  - Invent a second agent instead of hardening the Part 1 coordinator agent
  - Rely on a live LLM as the only acceptance gate for harness tests
  - Treat RAG or tool text as system instructions
  - Ship a single generic filter as the whole harness
  - Log raw PHI or full jailbreak payloads in guardrail events
  - Save memory-bank/evaluations/Results/HarnessGuardrails-*.md before human approval
  - Close MS8
  - Commit on the human's behalf
  - Edit CONTEXT.md, projectbrief, techContext, data/, .env, or root lockfiles
---

# HC-MS8-PLAN-119 — Agent harness and guardrails plan

Brief: [`docs/Project_Contexts/MS8-Harness_and_guardrails.md`](../../docs/Project_Contexts/MS8-Harness_and_guardrails.md).
Company rules: [`docs/Project_Contexts/healthcore-harness-BRIEFING.md`](../../docs/Project_Contexts/healthcore-harness-BRIEFING.md).

## Locked decisions

| Decision | Choice |
|----------|--------|
| Milestone | MS8 Part 2. Does not close MS8. |
| Agent | Same PLAN-105/109/117 coordinator. No parallel agent. |
| Graph | Nodes `input_guard` and `output_guard`. `GRAPH_VERSION` = `knowledge-agent/3`. |
| Input | After `receive_question`, before `plan_sources`. Classes: in_domain, casual, personal_task, jailbreak, identifiable_patient. |
| Output | After answer assembly. Format, instruction-leak, PHI scan (BRIEFING-mandated). |
| External | Sanitize + delimit RAG CONTEXT; tools stay out of the generation system role. |
| Observability | SQLite `guardrail_events`; JWT `GET /agent/guardrails/summary`. |
| Tests | Deterministic `tests/pipelines/test_agent_guardrails.py`. |
| Eval | Rubric in chat first; Results file only after human approval. |

## Agent instructions

1. Implement under PLAN-120. Do not reopen this decision table.
2. Do not write the HarnessGuardrails Results file until the human approves the rubric in chat.
3. Do not close MS8.
4. Do not commit.
