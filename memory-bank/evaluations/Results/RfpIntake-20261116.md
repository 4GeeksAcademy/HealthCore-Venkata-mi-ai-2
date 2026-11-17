# Agentic RFP Intake and Routing (Part 1) — Evaluation

**Date:** 2026-11-16  
**Rubric:** MS9 Agentic RFP Workflow, Part 1 — "What We Will Evaluate" (12 checks)  
**Implementation as of:** [HC-MS9-PLAN-126](../../plans/HC-MS9-PLAN-126-20261116-rfp-intake-impl.md)  
**Plan:** [HC-MS9-PLAN-125](../../plans/HC-MS9-PLAN-125-20261116-rfp-intake-plan.md)  
**Overall: 12/12 Pass.** This file does not close MS9.

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/MS9-Part1-Agentic-RFP-Workflow-.md`](../../../docs/Project_Contexts/MS9-Part1-Agentic-RFP-Workflow-.md) |
| Company briefing | [`docs/Project_Contexts/healthcore-rfp-BRIEFING.md`](../../../docs/Project_Contexts/healthcore-rfp-BRIEFING.md) |
| Handoff | [`data/pipelines/rfp_intake/HANDOFF.md`](../../../data/pipelines/rfp_intake/HANDOFF.md) |
| Graph | [`data/pipelines/rfp_intake/`](../../../data/pipelines/rfp_intake/) |
| API | [`services/api/app/routers/rfp.py`](../../../services/api/app/routers/rfp.py) |
| Backoffice | [`uis/backoffice/app/(internal)/rfp/page.tsx`](../../../uis/backoffice/app/(internal)/rfp/page.tsx) |
| Reprocess CLI | [`scripts/reprocess_rfp_ticket.py`](../../../scripts/reprocess_rfp_ticket.py) |
| Evidence tests | [`tests/pipelines/test_rfp_classifier.py`](../../../tests/pipelines/test_rfp_classifier.py), [`test_rfp_worker.py`](../../../tests/pipelines/test_rfp_worker.py), [`test_rfp_graph.py`](../../../tests/pipelines/test_rfp_graph.py), [`services/api/tests/test_rfp.py`](../../../services/api/tests/test_rfp.py) |

Saved after human approval on 2026-11-16. Same-day re-evals overwrite this file only.

## Method

- Dedicated graph `healthcore_rfp_intake` (`rfp-intake/1`) under `data/pipelines/rfp_intake/`. The existing FastAPI app exposes `POST /rfp/tickets` (202), `GET` poll, and reprocess. No second HTTP service.
- SQLModel tables `rfp_ticket`, `rfp_metadata`, and `rfp_department_section`. Runtime URL is `SUPABASE_DATABASE_URL` or a Postgres `DATABASE_URL`. TinyDB is not the source of truth for these rows.
- `.venv\Scripts\python.exe -m pytest tests/pipelines/test_rfp_classifier.py tests/pipelines/test_rfp_worker.py tests/pipelines/test_rfp_graph.py`: **18 passed** in 3.33s.
- `py -3 -m pytest tests/test_rfp.py` from `services/api`: **4 passed** in 1.90s.
- The three briefing PDFs pass through MarkItDown and the graph with a scripted model: request 1 and 2 reach `intake_complete` with Tom Callahan, Dr. Marcus Reid, and Claire Whitfield; request 3 is `discarded` / `vendor_pitch`.
- This re-run used the test database engine because the workspace had no Supabase URL. The three sample PDFs were scored with the scripted model inside the graph test.
- `.env` was not part of the evidence. The human commits.

## Rubric

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Same API only; pipeline under `data/pipelines/`; no second HTTP service | Pass | `rfp_router` is included on the existing FastAPI app. Graph `healthcore_rfp_intake` lives in `data/pipelines/rfp_intake/`. `test_graph_is_dedicated_rfp_intake` rejects knowledge-agent nodes. |
| 2 | Ticket, metadata, and key aspects in PostgreSQL (Supabase) via SQLModel | Pass | Tables `rfp_ticket`, `rfp_metadata`, and `rfp_department_section`. `resolve_url()` uses `SUPABASE_DATABASE_URL` or a Postgres `DATABASE_URL`. Tests wrote and read all three. TinyDB is not used for these rows. |
| 3 | PDFs stored under `data/raw/`; backoffice drives upload | Pass | Upload writes `data/raw/rfp/{ticket_id}.pdf`. `/rfp` posts `FormData` to `POST /rfp/tickets`. Briefing PDFs go through MarkItDown in `test_briefing_pdfs_flow_through_markitdown`. |
| 4 | Status is `analyzing`, then `intake_complete` or `discarded`; never `waiting_for_approval` | Pass | Formal and informal requests finish `intake_complete`. The vendor pitch finishes `discarded`. A model outage is `failed` / `classifier_unavailable`, not a discard. No `waiting_for_approval` in the RFP package. |
| 5 | Async upload: quick response, background run, pollable status | Pass | `POST /rfp/tickets` returns **202** and leaves the ticket `analyzing`. `enqueue` returns before the pipeline finishes. The page polls `GET /rfp/tickets/{id}`. |
| 6 | Non-RFPs are rejected without affecting other tickets | Pass | `test_vendor_discard_does_not_change_another_ticket`: Meridian stays `intake_complete`; the vendor pitch is `discarded` / `vendor_pitch`. |
| 7 | Metadata and readability stored per document | Pass | Request 1: Meridian Manufacturing, population 800, USD, word count, Flesch-Kincaid, Gunning Fog, and a cost band. |
| 8 | Orchestrator–worker–synthesizer on a dedicated `rfp_intake` graph | Pass | Required nodes are present. Revenue, clinical, and compliance run as separate workers. The revenue worker drops a population figure that is not in the extract. |
| 9 | Handoff carries `ticket_id` plus synthesizer / `key_aspects` | Pass | `handoff_json["ticket_id"]` and section `key_aspects` are stored. `handoff_ready` is true only on `intake_complete`. Contract is in `data/pipelines/rfp_intake/HANDOFF.md`. |
| 10 | Per-department key aspects and contacts match the briefing PDFs | Pass | Request 1 and 2: Tom Callahan, Dr. Marcus Reid, Claire Whitfield. US/BAA and UK/GBP. Request 3: `vendor_pitch`, `handoff_ready` false. |
| 11 | Unit tests for the classifier and at least one worker | Pass | Eight classifier tests and `test_revenue_worker_drops_invented_population`, plus the graph suite. **18 passed.** |
| 12 | Departments and RFP rules match the HealthCore briefing | Pass | Only `revenue`, `clinical`, and `compliance`. Compliance is on every accepted RFP. Unknown departments become open questions. PHI is redacted before the model sees the text. |

## Noted limits (accepted in this save)

1. This workspace had no Supabase URL, so the re-run persisted rows through the SQLModel test engine. The runtime resolver still targets Supabase or Postgres when that URL is set.
2. Sample PDFs were scored with the scripted model in `test_briefing_pdfs_flow_through_markitdown`. A live model call was not part of this save.
3. Signed-in browser click-through was not repeated for this save. The backoffice page posts the PDF and polls ticket status.

## Agent instructions

1. Canonical eval: this file. Official rubric score: **12/12 Pass**.
2. Same-day re-evals overwrite this file only. Do not append a second `RfpIntake-20261116` file.
3. Do not treat this as an MS9 milestone close. Part 2 and Part 3 are still open.
4. Do not rewrite PLAN-125 or PLAN-126.
5. Part 2 must read `handoff_json` from `data/pipelines/rfp_intake/HANDOFF.md` and must not re-parse the PDF.
6. The human commits. Do not commit on their behalf. Do not commit `.env` or `data/raw/rfp/` uploads.
