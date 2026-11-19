---
stamp: HC-MS9-PLAN-129
sequence: 129
milestone: MS9
date: 2026-11-18
title: Agentic RFP Response Generation Implementation
status: implemented
phase: implementation
summary: >
  Part 2 drafts are in place. A dedicated rfp_response graph reads the Part 1
  handoff and does not convert the PDF. Revenue, clinical, and compliance each
  have a generator. Readability, relevance, and briefing compliance run in
  parallel. A failed section returns to its generator at most twice. The last
  redacted draft and its EvaluationResult stay on the ticket. Exhausted
  sections become needs_human_review. A full pass stays under_evaluation with
  part2_outcome passed. Evaluation results are not saved until the human
  approves them.
related_paths:
  - memory-bank/plans/HC-MS9-PLAN-128-20261118-rfp-response-plan.md
  - data/pipelines/rfp_response/
  - data/pipelines/rfp_intake/store.py
  - data/pipelines/rfp_intake/service.py
  - data/pipelines/rfp_intake/HANDOFF.md
  - services/api/app/routers/rfp.py
  - services/api/tests/test_rfp.py
  - scripts/draft_rfp_ticket.py
  - tests/pipelines/test_rfp_generator.py
  - tests/pipelines/test_rfp_evaluator.py
  - tests/pipelines/test_rfp_response_graph.py
  - uis/backoffice/app/(internal)/rfp/page.tsx
do_not_repeat:
  - Add response nodes to the knowledge-agent graph or the Part 1 intake graph
  - Re-parse the PDF as the generator input
  - Set waiting_for_approval or done in this part
  - Invent headcount or store an unredacted patient name or diagnosis
  - Save the Part 2 evaluation Results file before the human approves the chat results
  - Rewrite PLAN-125, PLAN-126, PLAN-127, or PLAN-128
  - Commit data/raw/rfp uploads or .env files
  - Close MS9 from this stamp
---

# HC-MS9-PLAN-129 — Agentic RFP Response Generation Implementation

Implements [HC-MS9-PLAN-128](./HC-MS9-PLAN-128-20261118-rfp-response-plan.md).

## What shipped

- Graph `healthcore_rfp_response` version `rfp-response/1` under `data/pipelines/rfp_response/`.
- Generators `revenue`, `clinical`, and `compliance`. Evaluators for readability, relevance, and briefing rules `HC-PHI-01`, `HC-BAA-01`, `HC-DPA-01`, `HC-CUR-01`, and `HC-POP-01`.
- Iteration limit defaults to 2 (`RFP_DRAFT_MAX_ITERATIONS`).
- Same FastAPI app. `POST /rfp/tickets/{id}/draft` returns 202. A new upload that reaches `intake_complete` continues into this graph on the existing background thread.
- Drafts and `evaluation_results` are written on `rfp_department_section`. `approval_status` stays empty.
- Backoffice `/rfp` shows drafting, evaluation, a passed outcome, and a provisional banner for Tom Callahan.

## Checks in this session

- Pipeline pytest for the RFP intake and response tests: **31 passed**.
- Backoffice eslint on the RFP page: clean. `tsc --noEmit`: clean.
- API pytest was not run. This environment does not have FastAPI installed. `start_draft` is covered by the pipeline test.
- The backoffice was not clicked through. No API process was available to log in and open `/rfp`.

## Agent instructions

1. Do not bolt this work onto `services/knowledge_agent` or the Part 1 graph nodes.
2. Do not save `memory-bank/evaluations/Results/` for this part until the human approves the results in chat.
3. Part 3 must read `handoff_json` after `evaluation_closed` is true. Do not set `waiting_for_approval` from this stamp.
4. A `part2_guard` of `phi_review_required` must still draft nothing.
5. The human commits. Do not commit on their behalf.
6. Do not close MS9 from this stamp.
