---
stamp: HC-MS7-PLAN-109
sequence: 109
milestone: MS7
date: 2026-11-04
title: Coordinator Agent External Tools (Incidents and Inventory) Implementation
status: implemented
phase: implementation
summary: >
  Implements PLAN-108 ("Support Agent with LangGraph, Part 2 of 2"). The incident
  manager gains read-only GET /api/incidents and GET /api/incidents/{id}, fed by
  its own analyze upload path and seed (no patient_id in responses). The agent
  gains typed, read-only, single-responsibility tools ticket_lookup and
  inventory_lookup (HTTP, service-account JWT from env, 4.0 s deadline), a
  plan_sources node (LLM planner, rules fallback), tool_fallback and
  compose_answer nodes, and source-order tracing. Evals AG09-AG19 added; live
  trace: 101 passed, 10 skipped. Mechanics 76 passed, API 87 passed.
related_paths:
  - services/api/app/incident_analysis.py
  - services/api/app/incidents_store.py
  - services/api/app/models/incidents.py
  - services/api/app/routers/incidents.py
  - services/api/app/routers/agent.py
  - services/api/seed.py
  - services/api/requirements.txt
  - services/api/tests/
  - services/knowledge_agent/
  - tests/pipelines/agent_eval_cases.json
  - tests/pipelines/test_agent_evals.py
  - tests/pipelines/test_agent_graph.py
  - tests/pipelines/test_agent_tools.py
  - tests/pipelines/fixtures/agent_traces.json
  - scripts/record_agent_traces.py
  - docs/agent/langgraph-agent.md
  - docs/agent/eval-output.txt
  - .gitignore
do_not_repeat:
  - Send a full mixed question to the knowledge base; retrieve/generate get plan.knowledge_question when the plan has one
  - Let the planner SDK retry more than once (max_retries=1, 8 s timeout) or block the tool deadline on it
  - Require planner == "llm" for every live case; a slow gateway legitimately yields rules_fallback, and the eval checks the LLM planned at least one tool and one RAG case
  - Every PLAN-108 do_not_repeat item still applies
---

# HC-MS7-PLAN-109 — Coordinator Agent External Tools Implementation

Implements [PLAN-108](./HC-MS7-PLAN-108-20261104-langgraph-external-tools-plan.md) as planned. Design and commands: [`docs/agent/langgraph-agent.md`](../../docs/agent/langgraph-agent.md) (Part 2 section).

## What shipped

- **Incident manager read API.** `incidents_store.py` (TinyDB, gitignored `services/api/data/incidents.json`) upserts the valid rows of each analyzed CSV and of the seed sample (94 rows). `GET /api/incidents` supports the filters status, category, clinic_id, and country, with a limit. `GET /api/incidents/{id}` returns 404 "Incident not found." Both need a JWT, and neither returns `patient_id`.
- **Tools.** `tools/contracts.py` holds the Pydantic input and output models. `tools/session.py` holds `ReadOnlyApiSession`: GET only (plus the login POST), a 4.0 s deadline for the whole call, and one token refresh. `tools/incidents.py` and `tools/inventory.py` each have one responsibility.
- **Graph `knowledge-agent/2`.** It adds the nodes `plan_sources`, `lookup_ticket`, `lookup_inventory`, `tool_fallback`, and `compose_answer`, plus the conditional routes from PLAN-108. Outcome `tool_fallback` returns 200. `POST /agent/query` returns `sources`.
- **Trace.** Each tool step records tool, status, method, endpoint, http_status, latency_ms, and the returned ids or SKUs. `sources_used` and `TraceStore.source_sequence()` give the source order.
- **Evals.** AG09–AG19 cover tool routing, knowledge-base routing, both, not found, unreachable, timeout, inventory, and rejected rows. The recorder calls the real tools against the running API, a closed port, and a silent socket.

## Deviations from PLAN-108

1. `SourcePlan.knowledge_question`. In a mixed question, `retrieve` and `generate_answer` get only the policy clause. Sending the whole question returned no context for AG13. Pure knowledge-base runs still use the question unchanged.
2. In a mixed answer, `compose_answer` labels the RAG part "From the HealthCore knowledge base:".
3. The planner uses `max_retries=1`. The SDK default of 2 retries pushed planning past 13 s.
4. Live evals accept `planner: rules_fallback` for some cases, because the gateway was slow (3 of 18 in the latest recording). A separate eval checks that the LLM planned both a tool route and a RAG route.

## Verification

- Live recording: 19 runs. Evals: **101 passed, 10 skipped** (the skips are cases with no `retrieve` step). AG16 timeout: 4009 ms. AG17: gloves stock 12, threshold 24.
- Mechanics (`test_agent_tools`, `test_agent_graph`, `test_rag`): **76 passed**. API suite: **87 passed**.

## Agent instructions

1. The "What We Will Evaluate" scorecard is shown in chat. Save `memory-bank/evaluations/Results/LangGraphExternalTools-*.md` only after human approval.
2. Re-recording needs the API running at `HEALTHCORE_API_URL` and the env vars `AGENT_SERVICE_EMAIL` / `AGENT_SERVICE_PASSWORD`. Never commit them.
3. Does not close MS7.
