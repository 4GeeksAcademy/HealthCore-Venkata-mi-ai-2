---
stamp: HC-MS9-PLAN-126
sequence: 126
milestone: MS9
date: 2026-11-16
title: Agentic RFP Intake and Routing Implementation
status: implemented
phase: implementation
summary: >
  Part 1 intake is in place. Backoffice /rfp uploads a PDF to the existing
  API, which stores it under data/raw/rfp/, returns 202, and runs the
  dedicated rfp_intake LangGraph on a background thread. Tickets, readability,
  metadata, and per-department key aspects are SQLModel rows. Compliance is
  always included. A non-RFP is discarded. A model outage fails the ticket
  instead of discarding it. The handoff JSON carries ticket_id and key aspects
  for Part 2. Evaluation results are not saved until the human approves them.
related_paths:
  - memory-bank/plans/HC-MS9-PLAN-125-20261116-rfp-intake-plan.md
  - docs/Project_Contexts/healthcore-rfp-BRIEFING.md
  - data/pipelines/rfp_intake/
  - services/api/app/routers/rfp.py
  - services/api/tests/test_rfp.py
  - tests/pipelines/test_rfp_classifier.py
  - tests/pipelines/test_rfp_worker.py
  - tests/pipelines/test_rfp_graph.py
  - scripts/reprocess_rfp_ticket.py
  - uis/backoffice/app/(internal)/rfp/page.tsx
do_not_repeat:
  - Add RFP nodes to the knowledge-agent graph
  - Persist these tickets in TinyDB
  - Set waiting_for_approval in Part 1
  - Invent headcount or store patient identifiers
  - Commit data/raw/rfp/ uploads or .env files
  - Save the Part 1 evaluation Results file before the human approves the chat results
  - Rewrite PLAN-125
---

# HC-MS9-PLAN-126 — Agentic RFP Intake and Routing Implementation

Implements [HC-MS9-PLAN-125](./HC-MS9-PLAN-125-20261116-rfp-intake-plan.md).

## What shipped

- Graph `healthcore_rfp_intake` version `rfp-intake/1` under `data/pipelines/rfp_intake/`.
- `POST /rfp/tickets` returns 202. `GET` polls. `POST /rfp/tickets/{id}/reprocess` retries a discarded or failed ticket.
- Tables `rfp_ticket`, `rfp_metadata`, `rfp_department_section` via SQLModel. Runtime URL is `SUPABASE_DATABASE_URL` when configured.
- Backoffice page `/rfp`.

## Checks in this session

- Pipeline pytest: **18 passed**.
- API pytest `tests/test_rfp.py`: **4 passed**.
- Backoffice eslint on the RFP page and layout: clean. `tsc --noEmit`: clean.
- No `OPENAI_API_KEY` and no Supabase URL in this session. A local API accepted the three briefing PDFs with 202 and then marked each `failed` / `classifier_unavailable`. That is the outage path, not a discard.
- The same three PDFs pass through MarkItDown and the graph with a scripted model: request 1 and 2 reach `intake_complete` with Tom Callahan, Dr. Marcus Reid, and Claire Whitfield; request 3 is `discarded` / `vendor_pitch`.

## Agent instructions

1. Do not bolt RFP work onto `services/knowledge_agent`.
2. Do not save `memory-bank/evaluations/Results/` for this part until the human approves the results in chat.
3. Part 2 must read `handoff_json` from `data/pipelines/rfp_intake/HANDOFF.md` and must not re-parse the PDF.
4. The human commits. Do not commit on their behalf.
5. Do not close MS9 from this stamp.
