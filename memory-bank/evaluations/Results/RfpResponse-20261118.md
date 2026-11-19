# Agentic RFP Response Generation (Part 2) — Evaluation

**Date:** 2026-11-18  
**Rubric:** MS9 Agentic RFP Workflow, Part 2 — "What We Will Evaluate" (9 checks)  
**Implementation as of:** [HC-MS9-PLAN-129](../../plans/HC-MS9-PLAN-129-20261118-rfp-response-impl.md)  
**Plan:** [HC-MS9-PLAN-128](../../plans/HC-MS9-PLAN-128-20261118-rfp-response-plan.md)  
**Overall: 9/9 Pass.** This file does not close MS9.

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/MS9-Part2-Agentic-RFP-Workflow.md`](../../../docs/Project_Contexts/MS9-Part2-Agentic-RFP-Workflow.md) |
| Company briefing | [`docs/Project_Contexts/healthcore-rfp-BRIEFING.md`](../../../docs/Project_Contexts/healthcore-rfp-BRIEFING.md) |
| Part 1 handoff | [`data/pipelines/rfp_intake/HANDOFF.md`](../../../data/pipelines/rfp_intake/HANDOFF.md) |
| Part 2 handoff | [`data/pipelines/rfp_response/HANDOFF.md`](../../../data/pipelines/rfp_response/HANDOFF.md) |
| Graph | [`data/pipelines/rfp_response/`](../../../data/pipelines/rfp_response/) |
| API | [`services/api/app/routers/rfp.py`](../../../services/api/app/routers/rfp.py) |
| Backoffice | [`uis/backoffice/app/(internal)/rfp/page.tsx`](../../../uis/backoffice/app/(internal)/rfp/page.tsx) |
| Draft CLI | [`scripts/draft_rfp_ticket.py`](../../../scripts/draft_rfp_ticket.py) |
| Evidence tests | [`tests/pipelines/test_rfp_generator.py`](../../../tests/pipelines/test_rfp_generator.py), [`test_rfp_evaluator.py`](../../../tests/pipelines/test_rfp_evaluator.py), [`test_rfp_response_graph.py`](../../../tests/pipelines/test_rfp_response_graph.py) |

Saved after human approval on 2026-11-18. Same-day re-evals overwrite this file only.

## Method

- Dedicated graph `healthcore_rfp_response` (`rfp-response/1`) under `data/pipelines/rfp_response/`. The existing FastAPI app gains `POST /rfp/tickets/{id}/draft` (202). No second HTTP service. The Part 1 intake graph is unchanged.
- Generators read `handoff_json` for an `intake_complete` ticket. PDF conversion is not an input.
- SQLModel columns `draft_content` and `evaluation_results` on `rfp_department_section`. `approval_status` stays empty. Runtime URL is still `SUPABASE_DATABASE_URL` or a Postgres `DATABASE_URL`.
- `uv run pytest` on the RFP intake and response pipeline tests: **31 passed** in 3.63s.
- Backoffice eslint on the RFP page: clean. `tsc --noEmit`: clean.
- This run used the SQLModel test engine (SQLite) because the workspace had no Supabase URL. API pytest was not run because FastAPI is not installed in this environment. `start_draft` is covered by the pipeline test. The backoffice page was not clicked through.
- `.env` was not part of the evidence. The human commits.

## Rubric

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Each department has its own generator | Pass | `GENERATORS` has `revenue`, `clinical`, and `compliance`, each with its own prompt marker. `test_each_department_has_its_own_generator`. |
| 2 | Part 2 consumes the Part 1 handoff and does not re-parse the PDF | Pass | Input is `ticket_id` plus `handoff_json`. `test_pass_uses_the_handoff_and_does_not_convert_the_pdf` fails the run if `convert_pdf` is called. |
| 3 | Evaluators run in parallel and do not block other departments | Pass | Three checkers on one section, and the three departments, each wait on a barrier. A serial run would time out. |
| 4 | Generator-evaluator loop, iteration limit, and `needs_human_review` | Pass | Limit 2. Six generator calls. The second revenue prompt contains the first round's feedback. Status `needs_human_review`. The ticket stays in the handoff. |
| 5 | Ticket reflects generation and evaluation progress | Pass | `status_trail` records `drafting`, then `under_evaluation`, then `needs_human_review` when the limit is hit. A full pass stays `under_evaluation` with `part2_outcome: passed`. The backoffice label is "Evaluation passed". `waiting_for_approval` and `done` are not set. |
| 6 | Structured `EvaluationResult` | Pass | Each section stores `readability`, `relevance`, `compliance` (`pass`, `rule_ids`, `violations`), `overall_pass`, and `feedback_for_generator`. |
| 7 | Drafts and evaluation results in PostgreSQL; one backend API | Pass | Same SQLModel tables and the same FastAPI app. `POST /rfp/tickets/{id}/draft` returns 202. Tests wrote and read `draft_content` and `evaluation_results`. TinyDB is not used for these rows. |
| 8 | Unit tests for success, a generic failure, and one briefing compliance failure | Pass | Full pass from the handoff. A short section fails readability. A US draft that refuses a Business Associate Agreement fails `HC-BAA-01`. |
| 9 | Guidelines and formats match the HealthCore briefing | Pass | Owners are Tom Callahan, Dr. Marcus Reid, and Claire Whitfield. US sections require a BAA. UK sections require a DPA that cites UK GDPR. Currency follows `client_country`. A missing headcount stays an open question. Patient text is redacted before it is stored. |

## Examples kept with this save

**Passes.** Revenue section for Meridian Manufacturing (US). Flesch reading ease 60.11. The section quotes USD, states the covered population of 800 from the handoff, and leaves the missing budget as an open question for Tom Callahan. `overall_pass` is true.

**Fails.** A US compliance draft that refuses a Business Associate Agreement and quotes GBP. `compliance.pass` is false. Violations are `HC-BAA-01` and `HC-CUR-01`. A draft that also contains a labeled patient name and diagnosis fails `HC-PHI-01`. After two rounds the stored text is redacted, the ticket is `needs_human_review`, and the ticket remains in the Part 3 handoff.

## Noted limits (accepted in this save)

1. This workspace had no Supabase URL, so the run persisted rows through the SQLModel test engine. The runtime resolver still targets Supabase or Postgres when that URL is set.
2. API pytest was not run. FastAPI is not installed in this environment. The draft route is a thin wrapper over `start_draft`, which the pipeline test covers.
3. Signed-in browser click-through was not done. The backoffice page was linted and typechecked. It labels drafting, evaluation, a passed outcome, and a provisional draft for Tom Callahan.
4. The optional knowledge base was not wired. Briefing rules are in the generator prompts and in the compliance checker.

## Agent instructions

1. Canonical eval: this file. Official rubric score: **9/9 Pass**.
2. Same-day re-evals overwrite this file only. Do not append a second `RfpResponse-20261118` file.
3. Do not treat this as an MS9 milestone close. Part 3 is still open.
4. Do not rewrite PLAN-128 or PLAN-129.
5. Part 3 reads `handoff_json` after `evaluation_closed` is true. Do not set `waiting_for_approval` from this file.
6. The human commits. Do not commit on their behalf. Do not commit `.env` or `data/raw/rfp/` uploads.
