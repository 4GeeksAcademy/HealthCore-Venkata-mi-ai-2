---
stamp: HC-MS9-PLAN-125
sequence: 125
milestone: MS9
date: 2026-11-16
title: Agentic RFP Intake and Routing Plan
status: planned
phase: planning
summary: >
  Part 1 plan for HealthCore institutional RFP intake. A dedicated LangGraph
  under data/pipelines/rfp_intake/ converts each PDF with MarkItDown, screens
  PHI, classifies the document, and runs revenue, clinical, and compliance
  workers before a synthesizer. The existing FastAPI app accepts the upload,
  stores the PDF under data/raw/rfp/, returns 202, and runs the graph on a
  background thread. Tickets, metadata, readability, and key aspects live in
  PostgreSQL via SQLModel. The handoff row carries ticket_id plus the
  synthesizer payload for Part 2. Evaluation results stay unsaved until a
  human approves them.
related_paths:
  - docs/Project_Contexts/MS9-Part1-Agentic-RFP-Workflow-.md
  - docs/Project_Contexts/healthcore-rfp-BRIEFING.md
  - docs/Project_Contexts/rfp-requests/healthcore/
  - data/pipelines/rfp_intake/
  - services/api/app/routers/rfp.py
  - services/api/app/main.py
  - scripts/reprocess_rfp_ticket.py
  - tests/pipelines/test_rfp_classifier.py
  - tests/pipelines/test_rfp_worker.py
  - tests/pipelines/test_rfp_graph.py
  - services/api/tests/test_rfp.py
  - uis/backoffice/app/(internal)/rfp/page.tsx
do_not_repeat:
  - Add RFP nodes to services/knowledge_agent or the CX graph
  - Create a second HTTP service or a new frontend app
  - Persist tickets, metadata, or key aspects in TinyDB or a JSON file as the source of truth
  - Use ticket status waiting_for_approval in Part 1
  - Invent covered population, budget, clinic counts, or any patient identifier
  - Show PDF text, Markdown, or patient details in the backoffice or in logs
  - Commit files under data/raw/rfp/ or any .env file
  - Save the Part 1 evaluation Results file before the human approves it
  - Rewrite this stamp when the implementation stamp is added
---

# HC-MS9-PLAN-125 — Agentic RFP Intake and Routing Plan

## Problem

Tom Callahan (Revenue Cycle) receives institutional PDFs — occupational health, corporate wellness, and referral partnerships — and cannot see which departments must answer, or what each one needs, without reading the file. Part 1 stops at that routing. It does not draft the proposal.

Company rules are in [`docs/Project_Contexts/healthcore-rfp-BRIEFING.md`](../../docs/Project_Contexts/healthcore-rfp-BRIEFING.md) (archived from the syllabus `healthcore-BRIEFING.md`).

## Locked decisions

| Decision | Choice |
|----------|--------|
| Departments | `revenue` (Tom Callahan), `clinical` (Dr. Marcus Reid), `compliance` (Claire Whitfield). Compliance is on every accepted RFP. Revenue owns the ticket. Clinical reviews capacity. No other department gets a worker. |
| Graph | Dedicated LangGraph in `data/pipelines/rfp_intake/`. Routers only upload, query, and reprocess. |
| Async | In-process background thread. `POST` writes the PDF and the `analyzing` row, then returns **202** and `ticket_id`. Redis/Celery stays the reporting queue and is not required for intake. |
| Database | SQLModel on the same Supabase Postgres URL as inventory (`SUPABASE_DATABASE_URL`). Tests inject SQLite. TinyDB is not used. |
| Conversion | MarkItDown before any model call. Readability via `py-readability-metrics` (Flesch reading ease, Flesch-Kincaid, Gunning Fog) plus a token cost band. |
| Statuses | `analyzing`, `discarded`, `intake_complete`. `failed` is only for a crash or a model outage, never for "not an RFP". Never `waiting_for_approval`. |
| Samples | `healthcore-request-1.pdf` accept (Meridian, US, USD, BAA). `healthcore-request-2.pdf` accept (Thames Valley, UK, GBP, DPA). `healthcore-request-3.pdf` discard (EHR vendor pitch). Copies live under `docs/Project_Contexts/rfp-requests/healthcore/` for upload tests. Intake copies land in `data/raw/rfp/{ticket_id}.pdf` only. |

## Design answers

1. **Unknown department.** The orchestrator allowlists `revenue`, `clinical`, and `compliance`. A mention of People, Technology, Patient Experience, Executive, or any other name becomes an open question on the ticket. It does not create a worker.
2. **What each worker receives.** Metadata (client, country, program, population, deadline, budget, currency) plus the paragraphs that match that department. Not the whole Markdown. If a figure is absent, the worker records an open question and the sanitizer drops any number that is not in the metadata or the extract.
3. **Not an RFP.** A document is an RFP only when an institution is asking HealthCore for a proposal, price, or partnership (formal or informal). A vendor selling to HealthCore, a patient record, or an unclear document is `discarded` with a reason code. A model outage is `failed`, not `discarded`, so a false negative from an outage can be retried. A confident miss stays visible as `discarded` with `uncertain` or `vendor_pitch` and can be reprocessed from the CLI or the UI. Other tickets are separate rows.
4. **Contradictions.** Workers may disagree on country, population, budget, or currency. The synthesizer records a conflict with `resolution: unresolved_for_part3` and does not pick a winner. Metadata extracted before the workers stays the canonical metadata. Part 3 arbitration is out of scope.
5. **Crashes.** Each node touches `updated_at` while status is `analyzing`. An exception sets `failed` and a fixed `pipeline_error_code` (no document text, no path, no connection string). A poll that still sees `analyzing` after 15 minutes (`RFP_STALE_AFTER_SECONDS`) sets `failed` / `pipeline_interrupted` with a conditional update so a finished ticket is not overwritten. `scripts/reprocess_rfp_ticket.py` runs the graph again.

## PHI

Screen and redact before the classifier and the workers. Patterns cover SSN, MRN, NHS numbers, dates of birth, and lines that label a patient name or a diagnosis. Matches are replaced with `[REDACTED]`. The ticket stores `phi_detected` only. Logs store the ticket id and the error type. The UI never renders the PDF or the Markdown. The Part 2 handoff includes `phi_detected` and `part2_guard: phi_review_required` when set, so drafting must not start from raw text.

## Graph

`convert` → `readability` → `screen_phi` → `classify` → (`persist_discard` → END) or (`extract_metadata` → `orchestrate` → parallel `department_worker` → `synthesize` → `persist_complete` → END).

Worker calls are three agents selected by `department_id`: `revenue_worker`, `clinical_worker`, `compliance_worker`. The synthesizer writes the Sales brief from those sections only.

## Handoff for Part 2

On `intake_complete`, `handoff_ready` is true and `handoff_json` holds `ticket_id`, metadata, per-department `key_aspects`, owners, open questions, conflicts, the sales summary, and the PHI guard. Part 2 must read that payload and must not re-parse the PDF. Contract: `data/pipelines/rfp_intake/HANDOFF.md`.

## API and UI

- `POST /rfp/tickets` multipart PDF, JWT, **202** `{ticket_id, status: analyzing}`
- `GET /rfp/tickets` and `GET /rfp/tickets/{ticket_id}`
- `POST /rfp/tickets/{ticket_id}/reprocess` for `failed` or `discarded`
- Backoffice `/rfp`: upload, poll while `analyzing`, per-department key aspects and who to ask, discard reason, PHI banner, retry and home on errors

## Tests

- `tests/pipelines/test_rfp_classifier.py` — formal accept, informal accept, vendor reject, outage is not a discard
- `tests/pipelines/test_rfp_worker.py` — revenue worker does not invent a missing population
- `tests/pipelines/test_rfp_graph.py` — parallel workers, unknown department, contradiction, PHI redaction, discard leaves the other ticket alone
- `services/api/tests/test_rfp.py` — 202, poll, non-PDF 400, auth 401

## Out of scope

Part 2 drafting, Part 3 approval, and the `phi-detected` / `baa-dpa-mismatch` / `capacity-vs-population` arbiter nodes. Columns for `draft_content`, `evaluation_results`, and `approval_status` exist and stay empty.

## Agent instructions

1. Implement this stamp under `data/pipelines/rfp_intake/` and the existing FastAPI app. Do not extend `services/knowledge_agent`.
2. Keep department ids and the three sample expectations exactly as in the HealthCore RFP briefing.
3. Do not invent volumes or write patient identifiers into tickets, logs, or the UI.
4. Do not commit `data/raw/rfp/` artifacts or `.env` files.
5. Do not save the evaluation Results file until the human approves the results shown in chat.
6. Do not rewrite this plan file; add a later stamp for the implementation.
