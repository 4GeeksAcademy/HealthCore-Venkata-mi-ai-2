# RAG & Knowledge Base Evaluation

**Date:** 2026-11-02  
**Rubric:** Milestone 7 — RAG & Knowledge Base — "What We Will Evaluate" (17 checks)  
**Implementation as of:** [HC-MS7-PLAN-102](../../plans/HC-MS7-PLAN-102-20261102-rag-knowledge-base-impl.md)  
**Saved after:** [HC-MS7-PLAN-103](../../plans/HC-MS7-PLAN-103-20261102-rag-eval-save.md)  
**Overall: PASS (17/17)**

| Doc | Path |
|-----|------|
| Challenge | [`docs/Project_Contexts/Milestone7_RAG.md`](../../../docs/Project_Contexts/Milestone7_RAG.md) |
| RAG briefing (English) | [`docs/Project_Contexts/healthcore-rag-BRIEFING.en.md`](../../../docs/Project_Contexts/healthcore-rag-BRIEFING.en.md) |
| Corpus | [`docs/company-knowledge-base/`](../../../docs/company-knowledge-base/) |
| Indexing | [`data/process/rag.py`](../../../data/process/rag.py) |
| Retrieval + generation | [`data/pipelines/rag.py`](../../../data/pipelines/rag.py) |
| Endpoint | [`services/api/app/routers/knowledge.py`](../../../services/api/app/routers/knowledge.py) |
| UI | [`uis/backoffice/app/(internal)/knowledge/page.tsx`](../../../uis/backoffice/app/(internal)/knowledge/page.tsx) |
| Tests | [`tests/pipelines/test_rag.py`](../../../tests/pipelines/test_rag.py), [`services/api/tests/test_knowledge.py`](../../../services/api/tests/test_knowledge.py) |
| Eval set | [`data/eval/test-queries.json`](../../../data/eval/test-queries.json) |
| Eval report | [`data/eval/rag_recall_report.md`](../../../data/eval/rag_recall_report.md) |
| Design doc | [`docs/rag/rag-design.md`](../../../docs/rag/rag-design.md) |

Saved after human approval. Same-day RAG re-evals overwrite this single 2026-11-02 Results file only. Does not close MS7. Does not replace any earlier Results file. The corpus is policy and procedure text only, with no patient fields.

## Method

- Confirmed the four corpus files are byte-identical (file hash) to `00-general-contexts/healthcore/*.en.md` in the syllabus repo.
- Ran `setup()` live: **14 chunks** in `healthcore_knowledge`.
- Ran `scripts/eval_rag_recall.py --min-score 0`, then at `0.30` with `--answers`, against the live 4Geeks models.
- Drove the real FastAPI app in-process (`TestClient`, no mocks, temporary TinyDB) against the live models and the real index.
- `python -m pytest tests/pipelines/test_rag.py services/api/tests/test_knowledge.py`: **17 passed**. Full API suite: **71 passed**. `tests/pipelines`: **27 passed**.
- Backoffice `npm run lint` clean; `npx tsc --noEmit` exit 0.

## Approved numbers

| Item | Value |
|------|------:|
| Collection | `healthcore_knowledge` |
| Chunks after `setup()` | 14 (appointment-policy 4, insurance-coverage 3, new-patient-checklist 3, referral-process 4) |
| Embeddings model | `downtown-miami/openrouter/perplexity/pplx-embed-v1-0.6b` (1024-d, cosine) |
| Generation model | `downtown-miami/openrouter/openai/gpt-6-luna` |
| `min_score` | 0.30 |
| Recall@3 (with `min_score`) | **100%** (16/16, all rank 1) |
| Lowest correct-chunk score | 0.504 |
| Highest off-topic top-1 score | 0.105 |

## Rubric

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Four entrypoints (`setup`, `embed`, `retrieve`, `query`) exist, separated, single responsibility | Pass |
| 2 | Generation in its own function; `query()` = `retrieve()` + `generate_answer()` | Pass |
| 3 | Source documents in `docs/company-knowledge-base/` are what `setup()` indexes | Pass |
| 4 | Chunking respects semantic units | Pass |
| 5 | Every chunk keeps `source_document` and `section` | Pass |
| 6 | `embed()` uses an embeddings model different from the generation model | Pass |
| 7 | `retrieve()` applies `min_score` and does not force k results | Pass |
| 8 | Endpoint answer is model-generated, not the raw vector result | Pass |
| 9 | Endpoint reuses `data/pipelines/` without duplicating logic | Pass |
| 10 | UI lets a user enter a question and see the answer | Pass |
| 11 | Unit tests cover `retrieve()` and `query()` with mocks and pass | Pass |
| 12 | Prompt uses the briefing's voice and audience and only retrieved context | Pass |
| 13 | Nothing above `min_score` → answer says there isn't enough information | Pass |
| 14 | `data/eval/test-queries.json` has ≥ 8 questions covering all documents | Pass |
| 15 | Recall@3 ≥ 80% | Pass |
| 16 | Company-specific values match the briefing | Pass |
| 17 | `docs/rag/rag-design.md` covers process, chunking, and embeddings with reasons | Pass |

### Evidence notes

1. `setup()`/`embed()` are in `data/process/rag.py`; `retrieve()`/`query()` are in `data/pipelines/rag.py`. Chunking helpers are separate functions.
2. `query()` body is `retrieve()`, a log line with chunk ids and scores, then `generate_answer()`.
4. The chunker splits on each document's own blocks (heading + list, `Label:` rule, standalone paragraph) and unwraps soft wraps. A test on the real corpus checks that every source line lives whole in exactly one chunk.
6. `assert_distinct_models()` raises an error when both ids match; tested. The two ids are different 4Geeks gateway models.
7. The filter runs in Python after the top-k search. Mocked tests return 2 of 4 hits, 1 of 3, and 0.
8. Live: response keys are `['answer']` only. The no-context path still calls the model.
10. `/knowledge` has a textarea, example desk questions, loading state, error with retry (503 shown as "temporarily unavailable"), an answer card, and page-scoped light/dark mode. The endpoint it calls was verified live (401 without token, 200 with JWT). The page itself was not rendered in a browser, because the sandbox stops long-running dev servers.
12. The system prompt addresses the patient coordinator in the "best service salesperson" voice and says to use only the CONTEXT block. It also requires the US/UK split, verification of unlisted insurers with billing (Tom Callahan), no no-show fee for Medicare/Medicaid, no patient identifiers, and a `Source:` line.
13. Live: "What is the Wi-Fi password for the staff network?" → "I don't have enough information in the HealthCore knowledge base to answer that."
16. Collection `healthcore_knowledge`; `source_document` values are the briefing slugs; payload `company="healthcore"`, `language="en"`.

## Sample answers (live `query()`)

- **"Is there a charge for cancelling 12 hours in advance?"** Private-pay patients pay 50 USD (or 40 GBP in the UK). Medicare/Medicaid patients are not charged, but the incident is logged. Source: appointment-policy › Cancellation policy.
- **"Do you accept Humana?"** The answer is split into US and UK. Humana is not on the documented list, so verify with the billing team (Tom Callahan) before confirming.
- **"A Medicaid patient missed their appointment without calling. Do we charge the no-show fee?"** No; the incident is logged in their record.

## Deviations

- PLAN-101 named `text-embedding-3-small` / `gpt-4o-mini`. The 4Geeks gateway returned 403 for this team, so the allowlisted ids above were used (recorded in PLAN-102).
- Qdrant ran in embedded local mode for the eval because Docker Desktop was not running. Compose service `qdrant` is added for server mode (`QDRANT_URL`).
