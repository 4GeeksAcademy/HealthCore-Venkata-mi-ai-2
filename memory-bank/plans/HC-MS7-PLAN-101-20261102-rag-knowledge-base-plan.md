---
stamp: HC-MS7-PLAN-101
sequence: 101
milestone: MS7
date: 2026-11-02
title: HealthCore Coordinator Knowledge Base RAG Plan
status: planned
phase: planning
summary: >
  Plan for Milestone 7 (RAG & Knowledge Base) from the HealthCore RAG briefing
  (English). Priya Nair's eight patient coordinators get a desk assistant that
  answers from four policy documents only. Qdrant collection
  healthcore_knowledge, four separated entrypoints (setup, embed, retrieve,
  query) plus generate_answer, POST /knowledge/query, backoffice /knowledge,
  mocked unit tests, Recall@3 >= 80 percent eval, and docs/rag/rag-design.md.
  Eval Results only after human confirm.
related_paths:
  - docs/Project_Contexts/Milestone7_RAG.md
  - docs/Project_Contexts/healthcore-rag-BRIEFING.en.md
  - docs/company-knowledge-base/
  - data/process/rag.py
  - data/pipelines/rag.py
  - data/eval/test-queries.json
  - scripts/eval_rag_recall.py
  - services/api/app/routers/knowledge.py
  - uis/backoffice/app/(internal)/knowledge/page.tsx
  - tests/pipelines/test_rag.py
  - docs/rag/rag-design.md
  - docker-compose.yml
  - pyproject.toml
  - services/api/requirements.txt
do_not_repeat:
  - Use LangChain, LlamaIndex, or any orchestration framework
  - Reuse the generation model ID for embeddings (or the reverse)
  - Return raw Qdrant hits, chunk lists, or scores from POST /knowledge/query
  - Duplicate retrieval or generation logic inside the FastAPI router
  - Chunk by fixed character count or cut a bullet, numbered step, or rule in half
  - Add any patient record, name, diagnosis, or member ID to the corpus, tests, eval, or logs
  - Log the question text server-side (it may contain PHI typed at the desk)
  - Use pip install or pipenv for new dependencies
  - Commit .env files, API keys, or base URLs
  - Edit CONTEXT.md, CONTEXT-healthcore.md, projectbrief.md, or techContext.md
  - Save the RAG Results eval without human confirmation
---

# HC-MS7-PLAN-101 — Coordinator Knowledge Base RAG Plan

## Problem

Priya Nair (Head of Patient Experience) has eight patient coordinators answering the same questions at the front desk and on the phone: accepted insurance, cancellation fees, referral timelines, and what a new patient must bring. New coordinators give inconsistent answers across the 12 clinics. Her memo asks for an assistant that answers **like the clinic's best service salesperson**: clear, empathetic, and never inventing coverage or policy.

Source of truth for this ticket: [`docs/Project_Contexts/Milestone7_RAG.md`](../../docs/Project_Contexts/Milestone7_RAG.md) plus the English RAG briefing (archived as `docs/Project_Contexts/healthcore-rag-BRIEFING.en.md`). Corpus is policy and procedure text only — no PHI.

## Locked decisions

| Decision | Choice |
|----------|--------|
| Briefing | `07-trainning-rag/healthcore-BRIEFING.en.md` (human chose English). Archived verbatim. |
| Corpus | The four `.en.md` files copied verbatim from `00-general-contexts/healthcore/` into `docs/company-knowledge-base/`. `setup()` reads only that folder. |
| `source_document` | Briefing slugs: `insurance-coverage`, `appointment-policy`, `referral-process`, `new-patient-checklist` (filename minus `healthcore-` prefix and `.en.md`). |
| Collection | `healthcore_knowledge` (exact briefing name). |
| Payload | `company="healthcore"`, `source_document`, `section`, `language="en"`, `chunk_index`, `text`. |
| Chunking | Semantic blocks, not character counts. Unwrap soft line breaks; keep every bullet and numbered step whole. A heading line ending in `:` plus its list is one chunk (section = that heading). A `Label: sentence` paragraph uses the label as section. A one-line lead-in ending in `:` merges into the next block. Other paragraphs are their own chunk with section = document title. Expected 3–4 chunks per document (briefing minimum 3). |
| Idempotency | **Clear-and-reload**: `setup()` deletes and recreates the collection, then upserts. Point IDs are also deterministic `uuid5(source_document:chunk_index)` so a partial re-run never duplicates. |
| Embedding text | `embed()` embeds exactly what it is given. `setup()` passes `"{document title} — {section}\n{text}"` so short chunks keep their topic; queries pass the raw question. Same `embed()` both times. |
| Models | 4Geeks OpenAI-compatible gateway. Embeddings `text-embedding-3-small` (1536-d). Generation `gpt-4o-mini`. Separate env vars `RAG_EMBEDDING_MODEL` / `RAG_GENERATION_MODEL`; code refuses to run if they are equal. Key and base URL from gitignored `.env` (`OPENAI_API_KEY`, `OPENAI_BASE_URL`). |
| Distance | Cosine in Qdrant. |
| `min_score` | Tuned from eval: lowest in-domain top-1 score vs highest off-topic top-1 score; pick a value between them and document it. Default env `RAG_MIN_SCORE`. Filter is applied in Python after the search so fewer than `k` (or zero) can return. |
| Qdrant runtime | Compose service `qdrant` (`qdrant/qdrant`, port 6333, named volume). Code uses `QDRANT_URL`; if unset, falls back to embedded local storage at `data/process/.qdrant/` (gitignored) so the eval can run without Docker. |
| Generation | `generate_answer(question, context)` holds prompt assembly + LLM call. `query()` is literally `retrieve()` + `generate_answer()`. With zero context the model is still called and told to say the knowledge base has not enough information. Temperature 0. |
| Prompt rules | Coordinator audience, best-service-salesperson voice; only retrieved context; US vs UK split when country is not given; unlisted insurer → verify with billing (Tom Callahan), never confirm; no no-show fee for Medicare/Medicaid; never ask for or repeat patient identifiers; end with source line (`document › section`) for traceability. |
| API | `POST /knowledge/query` `{question}` → `{answer}`. JWT required (staff tool, same as `/reporting`). Router only calls `query()`. 503 with a safe message when Qdrant or the LLM is unavailable. Server logs chunk ids + scores only, never the question. |
| UI | Backoffice `/knowledge` ("Knowledge assistant") with textarea, example questions from the briefing, loading, error + retry, answer card. Light and dark mode scoped to this page via `prefers-color-scheme`. Public site untouched. |
| Tests | `tests/pipelines/test_rag.py`: fake Qdrant client and fake embed for `retrieve()`; mocked `retrieve()` and mocked LLM for `query()`. Plus chunking tests on the real corpus (≥3 chunks per doc, bullets intact, payload fields). API router test in `services/api/tests/test_knowledge.py` with `query()` monkeypatched. |
| Eval | `data/eval/test-queries.json`: ≥12 in-domain questions (3 per document) with expected `source_document` + `chunk_index`, plus off-topic negatives for threshold tuning. `scripts/eval_rag_recall.py` measures Recall@3 and writes `data/eval/rag_recall_report.md`. Target ≥ 80%. |
| Dependencies | `uv add qdrant-client openai python-dotenv` at root; mirror `qdrant-client` and `openai` in `services/api/requirements.txt` for the API image. |

## Implementation phases

1. Archive briefing, copy four source docs, add Qdrant to Compose, add deps with `uv add`.
2. `data/process/rag.py`: `load_documents`, `chunk_document`, `embed`, `setup` (+ CLI).
3. `data/pipelines/rag.py`: `retrieve`, `build_prompt`, `generate_answer`, `query`.
4. `services/api/app/routers/knowledge.py` + register in `main.py`.
5. Backoffice `/knowledge` page + nav link.
6. Unit tests (pipelines + API).
7. `data/eval/test-queries.json`, recall script, run it live, tune `min_score`.
8. `docs/rag/rag-design.md`.
9. Lint/tsc/pytest, implementation stamp, progress.

## Out of scope

- Conversation memory, LangGraph agent, re-ranking, hybrid search
- Spanish corpus (human chose the English briefing)
- Public `uis/healthcore` changes
- Changes to inventory, telemetry, reporting, Celery, or forecast code
- Writing the Results eval before human approval

## Agent instructions

1. Execute this plan, then stamp the implementation (next sequence) after files ship.
2. Present the "What We Will Evaluate" scores in chat. Write `memory-bank/evaluations/Results/` only after human approval.
3. Do not invent a Recall@3 number. If the live gateway or Qdrant is unreachable, report it as not measured.
4. Keep the corpus to the four verbatim policy documents.
