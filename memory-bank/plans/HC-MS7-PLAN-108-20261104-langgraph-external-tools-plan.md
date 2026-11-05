---
stamp: HC-MS7-PLAN-108
sequence: 108
milestone: MS7
date: 2026-11-04
title: Coordinator Agent External Tools (Incidents and Inventory) Plan
status: planned
phase: planning
summary: >
  Plan for "Support Agent with LangGraph, Part 2 of 2: Tools Outside the RAG".
  Adds two single-responsibility, read-only, typed tools to the PLAN-105 graph:
  lookup_ticket (incident manager, required) and lookup_inventory (inventory
  manager, stretch). Both call the running HealthCore API over HTTP with a
  service-account JWT read from env, a 4.0-second numeric timeout, and an
  explicit tool_fallback node for timeout, outage, auth failure, bad input, or
  not found. A plan_sources node (LLM planner with a deterministic rules
  fallback) decides RAG, tool, or both; conditional edges route on that plan.
  Prerequisite: the incident manager only kept an aggregate of the last CSV,
  so it gains read-only GET /api/incidents and GET /api/incidents/{id} fed by
  its own POST /api/incidents/analyze upload path. Trace records sources in
  order; 11 new eval cases (tool routing, RAG routing, both, not found, outage,
  timeout, inventory).
related_paths:
  - docs/Project_Contexts/SupportAgentwithLangGraph_2.md
  - services/api/app/incident_analysis.py
  - services/api/app/incidents_store.py
  - services/api/app/models/incidents.py
  - services/api/app/routers/incidents.py
  - services/api/app/routers/agent.py
  - services/api/seed.py
  - services/api/tests/test_incidents.py
  - services/api/tests/test_agent.py
  - services/api/tests/test_agent_tools_live_api.py
  - services/knowledge_agent/
  - tests/pipelines/agent_eval_cases.json
  - tests/pipelines/test_agent_evals.py
  - tests/pipelines/test_agent_graph.py
  - tests/pipelines/test_agent_tools.py
  - tests/pipelines/fixtures/agent_traces.json
  - scripts/record_agent_traces.py
  - docs/agent/langgraph-agent.md
  - docs/agent/eval-output.txt
do_not_repeat:
  - Index tickets or stock into Qdrant (live operational data is a tool call, not RAG)
  - Read tickets from scripts/samples or any hardcoded/fake dataset inside the agent; the tool only reads the incident manager API
  - Let any tool issue POST/PUT/PATCH/DELETE against incident or inventory data (only POST /auth/login is allowed, for the token)
  - Combine ticket and inventory lookups in one tool
  - Hardcode a token, password, or API URL in code; read HEALTHCORE_API_URL, AGENT_SERVICE_EMAIL, AGENT_SERVICE_PASSWORD from env
  - Let the LLM phrase live ticket/stock facts (rendered verbatim from the tool output so a status can never be invented)
  - Accept a ticket id from the planner that does not appear in the question
  - Expose patient_id through the new incident GET endpoints or the agent
  - Retry tool calls beyond one token refresh (the 4.0 s bound must hold)
  - Change receive_question, retrieve, generate_answer, no_context_answer, or reject_question node behaviour
  - Edit data/ (protected), .env, or root lockfiles
  - Save the Results eval without human approval
---

# HC-MS7-PLAN-108 — Coordinator Agent External Tools Plan

## Problem

The PLAN-105 agent only searches the knowledge base. When a coordinator asks "what's the status of ticket 482?" it has no way to check, because tickets live in the incident manager, not in the policy documents. The tech lead's brief ([`SupportAgentwithLangGraph_2.md`](../../docs/Project_Contexts/SupportAgentwithLangGraph_2.md)) asks for a tool that queries the incident system live, an optional second tool for inventory stock, and an agent that decides on its own whether a question needs the RAG, a tool, or both.

## Pre-flight finding (blocks the brief as written)

The brief assumes `GET /api/incidents` and `GET /api/incidents/{id}` already exist. In this repo they do not. The incident manager from PLAN-011/012 exposes only `POST /api/incidents/analyze` and `GET /api/incidents/results/export`, and `ResultStore` keeps only the aggregate of the last upload. There is no per-ticket record to read.

Decision: extend **our own** incident manager, not the agent. The upload path that already validates rows will also upsert every **valid** row into a TinyDB store, and two read-only GET routes will serve them. This keeps one source of truth (the service), uses the same validation the analyzer already applies, and the tool reads it like any other client. Re-uploading a CSV with a changed status updates the record, which is exactly why this is a tool and not RAG.

Inventory already exposes `GET /inventory/products` (JWT). No change needed.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Branch | `feature/langgraph-external-tools` (already checked out) |
| Transport | **HTTP** to the running API (`HEALTHCORE_API_URL`). Same transport for both tools. Tests inject an `httpx.Client` (the FastAPI `TestClient` is one), so contract tests still hit the real routes. |
| Dependencies | None new. `httpx` 0.28.1 is already installed in both envs (OpenAI SDK, FastAPI TestClient). Listed explicitly in `services/api/requirements.txt`; root `pyproject.toml`/`uv.lock` untouched. |
| Auth | Both services need a JWT. A service account logs in with `POST /auth/login` using `AGENT_SERVICE_EMAIL` / `AGENT_SERVICE_PASSWORD` from env, the same bearer flow as `services/api/profile_cache.py`. Token cached in memory; one refresh on 401. Missing credentials → `auth_failed` fallback, never an unauthenticated call. |
| Timeout | `TOOL_TIMEOUT_SECONDS = 4.0`, passed as `timeout=` on every request (connect, read, write, pool). No retries other than the single token refresh. |
| Read-only | Tool HTTP goes through one `ReadOnlyApiSession` whose guard raises `ReadOnlyViolation` for any method other than `GET`, except `POST /auth/login`. Static test also scans tool sources. |
| Live facts | Ticket and stock answers are rendered verbatim from the typed tool output. The LLM never phrases a status or a stock count. The LLM only plans the route and generates RAG answers (unchanged). |
| PHI | New incident GET responses omit `patient_id`. Trace stores incident ids, SKUs, statuses, counts, latency, HTTP status, endpoint path only. |

## Prerequisite: incident manager read API (`services/api`)

- `app/incident_analysis.py`: split `parse_csv_rows(text)` out of `analyze_csv_text()` and add `valid_rows(rows)`. Analysis results stay identical (100 / 94 / 6).
- `app/incidents_store.py` (TinyDB `services/api/data/incidents.json`, gitignored): `upsert_incidents(rows, source_file)`, `list_incidents(filters, limit)`, `get_incident(id)`. Each record keeps `first_recorded_at` and `updated_at`.
- `app/models/incidents.py`: `IncidentRecord` (`incident_id`, `clinic_id`, `country`, `category`, `status`, `satisfaction_score`, `source_file`, `first_recorded_at`, `updated_at`) and `IncidentListResponse` (`total`, `items`).
- `app/routers/incidents.py`: `POST /analyze` also upserts valid rows. New `GET /api/incidents` (filters `status`, `category`, `clinic_id`, `country`, `limit` 1–200) and `GET /api/incidents/{incident_id}` (404 `Incident not found.`). Both JWT.
- `seed.py`: also ingests `scripts/samples/incidents-healthcore.csv` through the same parse/validate/upsert path.

## Typed tool contracts (`services/knowledge_agent/tools/contracts.py`, Pydantic)

| Contract | Fields |
|----------|--------|
| `TicketLookupInput` | `ticket_id` (`^INC-\d{4,6}$`) **or** at least one filter: `status` (`open`/`closed`/`discarded`), `category` (the six incident categories), `clinic_id`; `limit` ≤ 10 |
| `TicketRecord` | the `IncidentRecord` fields above |
| `TicketLookupOutput` | `status` (`ok`, `not_found`, `invalid_input`, `timeout`, `unavailable`, `auth_failed`, `bad_response`), `tickets`, `total`, `http_status`, `latency_ms`, `endpoint` |
| `InventoryLookupInput` | `product_query` (2–80 chars, name or SKU fragment) |
| `ProductStock` | `name`, `sku`, `category`, `current_stock`, `threshold`, `below_threshold` |
| `InventoryLookupOutput` | same status set, `products`, `http_status`, `latency_ms`, `endpoint` |

Tools never raise for expected failures: timeout, connection error, 401/403, 404, 5xx, and invalid response bodies all map to a status. Unexpected bugs still raise and surface as the existing `AgentRunFailed` 500.

## Graph changes (`GRAPH_VERSION = "knowledge-agent/2"`)

New state keys: `plan` (`sources` in order, `ticket_input`, `inventory_input`, `planner`), `tool_results` (one per tool call), `fallbacks` (tool, reason, honest message).

New nodes (single responsibility):

| Node | Does |
|------|------|
| `plan_sources` | Decides `ticket`, `inventory`, `knowledge_base` (one or more). LLM planner with JSON output, validated; on any failure the deterministic rules planner decides and `planner` records `rules_fallback`. A ticket id is only kept if it appears in the question. |
| `lookup_ticket` | Calls the incident manager once through `TicketLookupTool` |
| `lookup_inventory` | Calls the inventory manager once through `InventoryLookupTool` |
| `tool_fallback` | Turns a failed tool result into an honest message ("I couldn't confirm that ticket's status right now…"). Never a status. |
| `compose_answer` | Renders tool facts verbatim, plus the RAG answer when both were used |

Edges:

```
START → receive_question
receive_question  ─route_after_receive→  plan_sources | reject_question
plan_sources      ─route_next_source→    lookup_ticket | lookup_inventory | retrieve
lookup_ticket     ─route_after_tool→     tool_fallback | lookup_inventory | retrieve | compose_answer
lookup_inventory  ─route_after_tool→     tool_fallback | retrieve | compose_answer
tool_fallback     ─route_next_source→    lookup_inventory | retrieve | compose_answer
retrieve          ─route_after_retrieve→ generate_answer | no_context_answer      (unchanged)
generate_answer   ─route_after_answer→   compose_answer | END
no_context_answer ─route_after_answer→   compose_answer | END
compose_answer, reject_question → END
```

Order when several sources are needed: ticket, then inventory, then knowledge base. Sequential, so the trace order is the execution order. All new nodes and routes go into `default_spec()` and get the existing build-time validation.

Outcomes: `answered`, `no_context`, `invalid_question` (unchanged) plus `tool_fallback` (at least one requested tool could not give a confirmed answer). `POST /agent/query` returns 200 for `tool_fallback` and adds `sources` to the body.

## Tracing

- `lookup_*` steps record `tool`, `status`, `method` (`GET`), `endpoint`, `http_status`, `latency_ms`, the returned ids/SKUs with status or stock, and the validated input.
- `plan_sources` records `sources` and `planner`; `tool_fallback` records `tool` and `reason`.
- `TraceStore.source_sequence(run_id)` and the export's `sources_used` map steps to `incident_manager`, `inventory_manager`, `knowledge_base` in order.

## Evals (`tests/pipelines/`)

Existing eight cases keep their criteria; their expected path gains `plan_sources`, and RAG cases forbid `lookup_ticket` / `lookup_inventory`. New cases, recorded against the running API loaded with `scripts/samples/incidents-healthcore.csv` and the inventory seed:

| Case | Question gist | Expected |
|------|---------------|----------|
| AG09 ticket by id | status of INC-0042 | tool only; `closed`, WORKFORCE; no `retrieve` |
| AG10 ticket by short number | "ticket 63" | tool only; INC-0063 `open` BILLING |
| AG11 ticket filters | how many open billing incidents | tool only; total 6 |
| AG12 RAG, not tool | no-show fee for Medicare | RAG only; no tool node |
| AG13 both | INC-0007 status and the cancellation fee | ticket, then RAG; `closed` and `50 USD` |
| AG14 not found | status of ticket 482 | `tool_fallback`; honest; no status word |
| AG15 incident service down | INC-0042, API unreachable | `tool_fallback` reason `unavailable` |
| AG16 incident timeout | INC-0042, server that never answers | `tool_fallback` reason `timeout`; latency ≈ 4 s |
| AG17 inventory stock | stock of nitrile exam gloves | inventory tool only; stock number from the API |
| AG18 inventory not found | stock of MRI contrast agent | `tool_fallback` reason `not_found` |
| AG19 invalid ticket in CSV | status of INC-0095 (rejected by the analyzer) | `not_found` — the agent does not read the raw CSV |

New assertions: `sources_used` matches the expected order; answers contain exactly the status/stock the tool step recorded; fallback answers contain no status words; the timeout step's latency is within 4.0–5.5 s; every tool step's method is `GET`.

Mechanics tests (stubs, no network): contracts, rules planner table, LLM planner parsing and ticket-id grounding, read-only guard, 4.0 s default, every failure status → fallback, both-path ordering, compiled-graph edge set. API tests: new GET routes, upsert updates status on re-upload, no `patient_id`, and the real tools against `TestClient(app)` with the incident/inventory stores unchanged afterwards.

## Steps

1. Incident manager read API + tests.
2. `services/knowledge_agent/tools/` (contracts, session, two tools), `planner.py`, state, nodes, graph, runner, trace store.
3. Update existing graph/API tests for the new path; add tool, planner, and API contract tests.
4. Eval cases, recorder (case-level overrides for outage and timeout), live recording against the running API, eval run.
5. Docs: `docs/agent/langgraph-agent.md` Part 2 section, `services/knowledge_agent/README.md`, eval output.
6. Implementation stamp PLAN-109, `progress.md`. Present "What We Will Evaluate" in chat; save Results only after human approval.

## Agent instructions

1. Implement exactly the contracts, nodes, and edges above. Keep the five Part 1 nodes unchanged.
2. The incident GET routes are part of the incident manager, not the agent. They must not expose `patient_id`.
3. Record the PR traces live (LLM planner) when the 4Geeks key is available; label offline traces.
4. Do not save `memory-bank/evaluations/Results/LangGraphExternalTools-*.md` until the human approves.
