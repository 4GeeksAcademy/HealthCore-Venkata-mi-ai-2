---
stamp: HC-MS9-PLAN-128
sequence: 128
milestone: MS9
date: 2026-11-18
title: Agentic RFP Response Generation Plan
status: planned
phase: planning
summary: >
  Part 2 plan for HealthCore proposal drafts. A dedicated graph under
  data/pipelines/rfp_response/ reads the Part 1 handoff and does not convert
  the PDF. Revenue, clinical, and compliance each have a generator. Three
  evaluators run in parallel on each section. A failed section returns to its
  generator with concrete feedback, at most twice. The last draft and its
  EvaluationResult are kept. Exhausted sections and the ticket become
  needs_human_review. A full pass stays under_evaluation with part2_outcome
  passed and does not set a Part 3 status. Evaluation results stay unsaved
  until a human approves them.
related_paths:
  - docs/Project_Contexts/MS9-Part2-Agentic-RFP-Workflow.md
  - docs/Project_Contexts/healthcore-rfp-BRIEFING.md
  - data/pipelines/rfp_intake/HANDOFF.md
  - data/pipelines/rfp_response/
  - data/pipelines/rfp_intake/store.py
  - services/api/app/routers/rfp.py
  - scripts/draft_rfp_ticket.py
  - tests/pipelines/test_rfp_generator.py
  - tests/pipelines/test_rfp_evaluator.py
  - tests/pipelines/test_rfp_response_graph.py
  - uis/backoffice/app/(internal)/rfp/page.tsx
do_not_repeat:
  - Add response nodes to services/knowledge_agent or to the Part 1 intake graph
  - Re-parse the PDF or call MarkItDown as the generator input
  - Set waiting_for_approval or done in this part
  - Invent a covered population, a fee, or any patient identifier
  - Store or show unredacted patient names or diagnoses
  - Persist drafts in TinyDB or a JSON file as the source of truth
  - Open a second HTTP service
  - Commit data/raw/rfp/ uploads or any .env file
  - Save the Part 2 evaluation Results file before the human approves the chat results
  - Rewrite PLAN-125, PLAN-126, or PLAN-127
---

# HC-MS9-PLAN-128 — Agentic RFP Response Generation Plan

Implements the Part 2 ticket in [`docs/Project_Contexts/MS9-Part2-Agentic-RFP-Workflow.md`](../../docs/Project_Contexts/MS9-Part2-Agentic-RFP-Workflow.md). Company rules are the HealthCore briefing, section 5: [`docs/Project_Contexts/healthcore-rfp-BRIEFING.md`](../../docs/Project_Contexts/healthcore-rfp-BRIEFING.md). The syllabus copy of that briefing is the same rule list.

## Problem

Part 1 tells Tom Callahan which departments must answer. Writing the pricing-proposal section for each department is still manual. Part 2 drafts those sections and reviews them before a person sees them. It does not approve them and it does not build the final document.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Entry | Ticket status `intake_complete` and `handoff_ready`. Input is `ticket_id` plus `handoff_json` from [`data/pipelines/rfp_intake/HANDOFF.md`](../../data/pipelines/rfp_intake/HANDOFF.md). |
| Graph | New LangGraph `healthcore_rfp_response` in `data/pipelines/rfp_response/`. The intake graph is not extended. The knowledge-agent graph is not extended. |
| Departments | The same three ids. `revenue_generator`, `clinical_generator`, and `compliance_generator` are separate callables. |
| Generators see | Shared metadata, that department's `key_aspects` and open questions, the owner, and `feedback_for_generator` on a retry. Not the PDF, not the Markdown, not the other departments' drafts. |
| Knowledge base | Not wired. Qdrant is optional for this part and is not graded. The briefing rules are in the generator prompts and in the compliance checker so a draft can pass without a live vector store. |
| Evaluators | Readability (`py-readability-metrics`), relevance, and compliance. All three run in a thread pool per section. Sections run in a second pool so one department does not wait for another. Evaluators return values. They do not write the database. |
| Loop | `RFP_DRAFT_MAX_ITERATIONS` defaults to 2. A failed section goes back to its own generator with the evaluation feedback. Other sections that already passed are not redrafted. |
| Exhausted | Keep the last draft and its `EvaluationResult`. Section `review_state` is `needs_human_review`. Ticket status is `needs_human_review`. The ticket stays in the Part 3 handoff. |
| All pass | Do not set `waiting_for_approval` or `done`. Ticket status stays `under_evaluation`. `handoff_json.part2_outcome` is `passed` and `evaluation_closed` is true. The backoffice label is "Evaluation passed". |
| PHI guard | `part2_guard` of `phi_review_required` drafts nothing. Each section gets a structured failure for rule `HC-PHI-01`. Ticket status is `needs_human_review`. |
| PHI in a draft | The evaluator sees the original text so `HC-PHI-01` can fail. The row and the UI store the redacted text only. |
| Status writes | Parent steps write `drafting`, then `under_evaluation`, then the terminal status. Parallel workers do not update the ticket row. |
| API | Same FastAPI app. `POST /rfp/tickets/{id}/draft` returns 202. A new upload that reaches `intake_complete` continues into this graph on the existing background thread. |
| Database | Same SQLModel tables. `draft_content` and `evaluation_results` are filled on `rfp_department_section`. `approval_status` stays empty. |

## Briefing rules the compliance evaluator enforces

These are checks, not a style opinion.

| Rule id | Rule |
|---------|------|
| `HC-PHI-01` | No section may contain a patient name, diagnosis, or other patient identifier. |
| `HC-BAA-01` | A US compliance section must include a Business Associate Agreement (BAA) clause. A sentence that refuses the clause fails. |
| `HC-DPA-01` | A UK compliance section must include a Data Processing Agreement (DPA) clause that references UK GDPR. A refusal fails. |
| `HC-CUR-01` | Revenue quotes USD for a US client and GBP for a UK client. The other currency code must not appear. |
| `HC-POP-01` | A headcount in a draft must match `covered_population`. If that field is null, the draft must not introduce one. |

## Readability and relevance

- Readability passes when the section has at least 80 words, Flesch reading ease is at least 30 when it can be computed, and Gunning fog is at most 22 when it can be computed. A short section fails with the word count in the feedback.
- Relevance passes when each Part 1 `key_aspect` is reflected in the section, the client name appears, and the department topic appears (currency, clinic capacity, or the country-correct privacy clause). `missing_aspects` lists what is absent.

## EvaluationResult

```text
section_id / department_id
readability: { pass, score, details }
relevance: { pass, missing_aspects[] }
compliance: { pass, rule_ids[], violations[] }
overall_pass: bool
feedback_for_generator: string
contains_phi: bool
review_state: passed | needs_human_review
provisional: bool
iterations_used: int
iteration_limit: int
```

`feedback_for_generator` names the failed rule, the missing aspect, or the readability numbers. It is empty of patient details.

## Design answers

1. Each evaluator receives that section's draft, the department id, the shared metadata, and that department's key aspects. It does not receive the PDF or the other drafts.
2. Evaluators do not write shared state. The parent step writes every `evaluation_results` value in one transaction after the pools finish.
3. A provisional section is labeled in the backoffice for Tom Callahan: the draft is not ready to send, the owner is named, and the feedback says what failed. The ticket status is `needs_human_review`.
4. Feedback quotes the missing aspect or the rule id and what to change. It does not say only "try again".

## Ticket progress

`intake_complete` → `drafting` (generators) → `under_evaluation` (evaluators) → `needs_human_review` if any section exhausts the limit. A full pass remains `under_evaluation` with `part2_outcome: passed`. `status_trail` on the handoff records the writes. `updated_at` changes on each write so a poll can see the stage.

## Part 3 handoff

`handoff_json.part` becomes 2 and `next` becomes `part3_approval`. Every department has `draft_content` (redacted if needed) and `evaluation_result`. Conflicts stay `unresolved_for_part3`. Discarded and failed tickets are not drafted.

## Tests

- `tests/pipelines/test_rfp_generator.py` — revenue generator quotes USD, does not invent a missing population, and sends feedback only to that department's prompt.
- `tests/pipelines/test_rfp_evaluator.py` — short text fails readability; a US draft that refuses a BAA fails `HC-BAA-01`; the three evaluators and the three sections run concurrently.
- `tests/pipelines/test_rfp_response_graph.py` — full pass from the handoff without converting the PDF; the loop stops at the iteration limit, keeps the last redacted draft, and sets `needs_human_review`; a PHI guard writes no draft.
- `services/api/tests/test_rfp.py` — `POST /draft` returns 202 for `intake_complete` and 409 otherwise.

## Out of scope

Part 3 approval, `waiting_for_approval`, `done`, and the arbiter nodes `phi-detected`, `baa-dpa-mismatch`, and `capacity-vs-population`.

## Agent instructions

1. Implement this stamp under `data/pipelines/rfp_response/` and the existing FastAPI app. Do not extend `services/knowledge_agent` or the Part 1 graph nodes.
2. Read `handoff_json`. Do not convert the PDF.
3. Keep the five briefing rule ids and the three department generators separate.
4. Do not set `waiting_for_approval` or `done`.
5. Do not store or display an unredacted patient name or diagnosis.
6. Do not save `memory-bank/evaluations/Results/` for this part until the human approves the results in chat.
7. Do not commit `data/raw/rfp/` artifacts or `.env` files.
8. Do not rewrite this plan file. Add a later stamp for the implementation.
9. Do not close MS9 from this stamp.
