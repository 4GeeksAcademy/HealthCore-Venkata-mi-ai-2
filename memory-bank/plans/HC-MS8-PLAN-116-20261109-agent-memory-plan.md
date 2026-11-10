---
stamp: HC-MS8-PLAN-116
sequence: 116
milestone: MS8
date: 2026-11-09
title: Agent Memory and Self-Improvement Part 1 Plan
status: planned
phase: planning
summary: >
  Plan for Agent Memory Part 1. The same coordinator agent gains an episodic
  SQLite memory beside the graph, not inside Qdrant healthcore_knowledge and
  not on the Celery Redis broker. A turn may propose one operational fact.
  The user must approve, reject, or edit it with a structured classifier.
  Silence and ambiguity reject. PHI never enters the store, the audit, or
  the model. Consolidation expires, dedupes, and re-checks PHI.
related_paths:
  - docs/Project_Contexts/AgentMemoryPart1.md
  - docs/Project_Contexts/healthcore-memory-BRIEFING.md
  - docs/agent/agent-memory.md
  - services/knowledge_agent/memory/
  - services/knowledge_agent/runner.py
  - services/api/app/routers/agent.py
  - tests/pipelines/test_agent_memory.py
do_not_repeat:
  - Write agent memory into the Qdrant collection healthcore_knowledge or any *_knowledge collection
  - Put agent memory keys on the Celery Redis broker
  - Bump GRAPH_VERSION or change the graph node path for ordinary desk questions
  - Store patient identifiers, clinical content, or the raw text of a PHI turn in memory, audit, or traces
  - Approve a pending proposal because the next message contains the letters yes
  - Hold two pending proposals in one conversation
  - Save memory-bank/evaluations/Results/AgentMemory-*.md before human approval
  - Close MS8 (Part 2 harness is still out of scope)
  - Commit on the human's behalf
  - Edit data/, .env, CONTEXT.md, projectbrief, techContext, or root lockfiles
---

# HC-MS8-PLAN-116 — Agent memory plan

Brief: [`docs/Project_Contexts/AgentMemoryPart1.md`](../../docs/Project_Contexts/AgentMemoryPart1.md). Company rules: [`docs/Project_Contexts/healthcore-memory-BRIEFING.md`](../../docs/Project_Contexts/healthcore-memory-BRIEFING.md).

## Locked decisions

| Decision | Choice |
|----------|--------|
| Milestone | MS8 Part 1. Does not close MS8. |
| Agent | The PLAN-105/109/113 coordinator. No second agent and no new graph nodes. `GRAPH_VERSION` stays `knowledge-agent/2`. |
| Memory kind | Episodic key-value. Discrete clinic protocols, incident patterns with no patient data, staff presentation preferences, and country admin exceptions. |
| Store | SQLite `agent_memory.sqlite` under `AGENT_STATE_DIR` (gitignored `.state/`). Explicit `MemoryStore` read and commit methods. |
| Ruled out | Qdrant (RAG stays read-only; cosine similarity is the wrong tool for a few auditable facts). Knowledge graph (no dependency edges to traverse). Fine-tuning (cannot selectively forget or show who approved). Redis (already the Celery broker on db 0 with `noeviction`). |
| Proposal | One structured `MemoryAssessment`. Most turns have `memory_proposal = null`. A proposal is a question at the end of the same answer. Nothing is written yet. |
| PHI | Deterministic gate before the user is asked and again at consolidate and commit. A hit is an explicit refusal. The identifier is not stored, logged, or sent to the model. The gate covers HIPAA identifiers and UK GDPR special-category health data with the same rules. |
| Decision | Pydantic label `approve` / `reject` / `edit` / `ambiguous`, plus confidence. Below 0.75, or any topic change, is a rejection. `"yes" in message` is not the test. |
| Pending | One per conversation. Unanswered after 24 hours is expired and rejected. |
| Poisoning | No write without a classified approve or edit. The edit is gated again. A fact that would contradict published Medicare/Medicaid no-show fees or confirm Humana is refused. Desk memory is labeled as not published policy. Actor is `staff:{id}` from the JWT, not an email and not a patient. |
| Consolidation | TTL 90/90/180/365 days by kind, exact-text dedupe, cap 40, PHI re-check. Rejected rows stay in the audit only. |
| Evidence | Two runner cycles: Manchester referral approved and reused; Diane Foster preference rejected and absent. |

## Agent instructions

1. Implement under PLAN-117. Do not reopen this decision table.
2. Do not write the AgentMemory Results file until the human approves the rubric in chat.
3. Do not close MS8. Do not bump `GRAPH_VERSION`.
4. Do not commit.
