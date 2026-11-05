# Support Agent with LangGraph — Part 2 Evaluation

**Date:** 2026-11-04  
**Rubric:** Support Agent with LangGraph, Part 2 of 2 — "What We Will Evaluate" (8 required checks + 1 stretch)  
**Implementation as of:** [HC-MS7-PLAN-109](../../plans/HC-MS7-PLAN-109-20261104-langgraph-external-tools.md)  
**Plan:** [HC-MS7-PLAN-108](../../plans/HC-MS7-PLAN-108-20261104-langgraph-external-tools-plan.md)  
**Overall: PASS (9/9)** against a **live** trace (real 4Geeks models, live incident and inventory HTTP tools, 4.0 s timeout).

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/SupportAgentwithLangGraph_2.md`](../../../docs/Project_Contexts/SupportAgentwithLangGraph_2.md) |
| Agent package | [`services/knowledge_agent/`](../../../services/knowledge_agent/) |
| Tools | [`services/knowledge_agent/tools/`](../../../services/knowledge_agent/tools/) |
| Incident GET routes | [`services/api/app/routers/incidents.py`](../../../services/api/app/routers/incidents.py) |
| Endpoint | [`services/api/app/routers/agent.py`](../../../services/api/app/routers/agent.py) (`POST /agent/query`, JWT) |
| Evals | [`tests/pipelines/test_agent_evals.py`](../../../tests/pipelines/test_agent_evals.py), [`tests/pipelines/agent_eval_cases.json`](../../../tests/pipelines/agent_eval_cases.json) |
| Trace export | [`tests/pipelines/fixtures/agent_traces.json`](../../../tests/pipelines/fixtures/agent_traces.json) |
| Eval output | [`docs/agent/eval-output.txt`](../../../docs/agent/eval-output.txt) |
| Design doc | [`docs/agent/langgraph-agent.md`](../../../docs/agent/langgraph-agent.md) (Part 2) |
| Part 1 eval | [LangGraphAgent-20261104](./LangGraphAgent-20261104.md) (**11/11 Pass**, live) |

Saved after human approval. Same-day re-evals overwrite this file only. Does not close MS7. Does not replace [LangGraphAgent-20261104](./LangGraphAgent-20261104.md).

## Method

- Recorded one traced run per eval case with `scripts/record_agent_traces.py --mode live`. Graph `knowledge-agent/2`. Models: `pplx-embed-v1-0.6b` (embeddings), `gpt-6-luna` (generation and planner). Tools: HTTP to the running HealthCore API with a service-account JWT from env, `TOOL_TIMEOUT_SECONDS = 4.0`.
- `uv run pytest tests/pipelines/test_agent_evals.py -v`: **101 passed, 10 skipped**. The skips are retrieval checks on routes that never call `retrieve` (blank question, ticket-only, inventory-only, fallbacks).
- Mechanics: `test_agent_tools.py` + `test_agent_graph.py` + `test_rag.py` **76 passed**. API suite `python -m pytest`: **87 passed**.
- AG15 and AG16 do not stub the tool: the recorder points it at a closed port (unreachable) and at a socket that accepts and never replies (timeout). AG16 `lookup_ticket` latency **4004.7 ms**, status `timeout`.
- Auth: both the incident and inventory services require a JWT. The agent signs in with `POST /auth/login` using `AGENT_SERVICE_EMAIL` / `AGENT_SERVICE_PASSWORD` from env (`HEALTHCORE_API_URL`, default `http://localhost:8001`). No token is hardcoded. If credentials are missing the tool returns `auth_failed` and the graph falls back.
- The incident manager had no read endpoints. Part 2 added `GET /api/incidents` and `GET /api/incidents/{id}` to **our own** service, fed by the existing analyze upload path and seed (94 valid rows from `scripts/samples/incidents-healthcore.csv`). Responses never include `patient_id`. The tool reads those routes over HTTP; it does not read the CSV.

## Rubric

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Typed ticket tool reads the real incident manager, with auth if the service requires it | Pass | `TicketLookupInput` / `TicketLookupOutput` in `tools/contracts.py` (`ticket_id` `^INC-\d{4,6}$`, extra fields forbidden). `TicketLookupTool` calls `GET /api/incidents/{id}` or `GET /api/incidents` with filters. Service-account JWT from env; one refresh on 401. `services/api/tests/test_agent_tools_live_api.py` hits the real routes. AG09: `GET /api/incidents/INC-0042` → 200, `closed`, WORKFORCE, 228.7 ms. |
| 2 | Tools are read-only | Pass | `ReadOnlyApiSession` allows only `GET` plus `POST /auth/login`. Any other method raises `ReadOnlyViolation` before a request is sent. Static scan of tool sources. Live API test leaves incident and inventory data unchanged. Every tool step in the live trace has `"method": "GET"`. |
| 3 | Explicit numeric timeout | Pass | `TOOL_TIMEOUT_SECONDS = 4.0` is the deadline for the whole tool call, including login. AG16 against a silent server: `status: timeout`, latency 4004.7 ms. Eval asserts timeout latency is within 4.0–5.5 s. |
| 4 | Verifiable fallback; no made-up answers | Pass | `tool_fallback` node. Example: "I couldn't confirm ticket INC-0042's status right now: the incident manager did not respond in time…" Ticket and stock facts are rendered verbatim from the tool output; the LLM never phrases a status or a stock figure. AG14 not found, AG15 unreachable, AG16 timeout, AG18 unknown product, AG19 rejected CSV row (`INC-0095`). Evals assert fallback answers contain no status words. Outcome `tool_fallback` returns HTTP 200. |
| 5 | Routes between RAG and tool(s) from the question, without user instruction | Pass | `plan_sources` (LLM JSON plan, 8 s timeout, one retry; `rules_plan` on failure, recorded as `planner: rules_fallback`). A ticket id is kept only if it appears in the question. Live: LLM planned 15 of 18 cases; AG10/AG15/AG16 used `rules_fallback` because the gateway was slow, and the routes were still correct. A separate eval checks the LLM planned at least one tool case and one RAG case. |
| 6 | Single responsibility per tool | Pass | `ticket_lookup` only reads incidents. `inventory_lookup` only reads stock. Separate nodes, contracts, and files. A mechanics test forbids a combined tool. |
| 7 | Trace shows which sources were used and in what order | Pass | `sources_used` on each run; `TraceStore.source_sequence(run_id)`; `POST /agent/query` returns `sources`. Tool steps record `tool`, `status`, `method`, `endpoint`, `http_status`, `latency_ms`, and returned ids or SKUs. No tokens or URLs. AG09 `['incident_manager']`; AG12 `['knowledge_base']`; AG13 `['incident_manager', 'knowledge_base']`. |
| 8 | At least 2 new evals verifying RAG vs tool routing | Pass | AG09–AG11 tool not RAG; AG12 RAG not tool (plus AG01–AG07 now forbid tool nodes); AG13 both; AG14–AG16 and AG19 fallback. 11 new cases total (AG09–AG19). |
| 9 | (Stretch) Inventory tool follows the same contract, timeout, and fallback | Pass | `InventoryLookupInput` / `InventoryLookupOutput`; same session, 4.0 s deadline, same fallback statuses. AG17: `GET /inventory/products`, nitrile exam gloves SKU `HC-PPE-GLV-100`, stock 12, threshold 24. AG18 unknown product → `tool_fallback` / `not_found`. |

## PR artifacts (live trace)

Ticket-tool run (**AG09**):

```
path:          receive_question → plan_sources → lookup_ticket → compose_answer
sources_used:  ['incident_manager']
planner:       llm
tool_call:     GET /api/incidents/INC-0042 → 200, status ok, 228.7 ms
               tickets: [{incident_id: INC-0042, status: closed, category: WORKFORCE}]
source_line:   Source: HealthCore incident manager (live)
```

RAG run (**AG12**):

```
path:          receive_question → plan_sources → retrieve → generate_answer
sources_used:  ['knowledge_base']
planner:       llm
retrieve:      appointment-policy › Cancellation policy (0.60), …
source_line:   Source: appointment-policy › Cancellation policy
```

Both sources (**AG13**, extra):

```
path:          receive_question → plan_sources → lookup_ticket → retrieve → generate_answer → compose_answer
sources_used:  ['incident_manager', 'knowledge_base']
planner:       llm
tool_call:     GET /api/incidents/INC-0007 → 200, closed, APPOINTMENT
answer:        Ticket INC-0007 is closed. … From the HealthCore knowledge base:
               … cancelling less than 24 hours ahead costs 50 USD …
```

Timeout fallback (**AG16**, extra):

```
path:          receive_question → plan_sources → lookup_ticket → tool_fallback → compose_answer
sources_used:  ['incident_manager']
tool_call:     GET /api/incidents/INC-0042 → status timeout, 4004.7 ms
fallback:      {tool: ticket_lookup, reason: timeout}
```

Eval console output: [`docs/agent/eval-output.txt`](../../../docs/agent/eval-output.txt) (**101 passed, 10 skipped**).

The live trace export is the PR artifact. `.env` stays local and gitignored. The export contains no key, token, password, or API URL.

## Noted deviations from PLAN-108 (accepted)

1. Mixed questions send only the policy clause (`plan.knowledge_question`) to retrieve and generate. Sending the full mixed question returned no context for AG13.
2. Mixed answers label the RAG part "From the HealthCore knowledge base:".
3. Planner uses `max_retries=1` (SDK default of 2 retries pushed planning past 13 s).
4. Live evals accept `planner: rules_fallback` on some cases when the gateway is slow; they still require the LLM to have planned at least one tool route and one RAG route in the recording.

## Agent instructions

1. Canonical eval: this file. Official rubric score: **9/9 Pass** on a live trace.
2. Same-day re-evals overwrite this file only. Do not append a second `LangGraphExternalTools-20261104` file.
3. Do not treat this as an MS7 milestone close.
4. Do not rewrite PLAN-108 or PLAN-109.
5. Re-recording needs the API at `HEALTHCORE_API_URL` and `AGENT_SERVICE_EMAIL` / `AGENT_SERVICE_PASSWORD` in the environment. Never commit them.
6. PR label: `langgraph-external-tools`. Include the AG09 ticket trace, the AG12 RAG trace, and `docs/agent/eval-output.txt`.
