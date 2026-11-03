---
stamp: HC-MS7-PLAN-102
sequence: 102
milestone: MS7
date: 2026-11-02
title: HealthCore Coordinator Knowledge Base RAG Implementation
status: implemented
phase: implementation
summary: >
  Implements PLAN-101. Four briefing policy documents indexed into Qdrant
  healthcore_knowledge (14 semantic chunks, 3-4 per document). setup/embed in
  data/process/rag.py; retrieve/generate_answer/query in data/pipelines/rag.py;
  POST /knowledge/query (JWT, answer only); backoffice /knowledge with loading,
  error, light/dark. Live Recall@3 100 percent (16/16) at min_score 0.30.
  Models switched to the 4Geeks team allowlist (pplx-embed-v1-0.6b embeddings,
  gpt-6-luna generation). Eval Results pending human approval. Does not close MS7.
related_paths:
  - docs/company-knowledge-base/
  - docs/Project_Contexts/healthcore-rag-BRIEFING.en.md
  - data/process/rag.py
  - data/pipelines/rag.py
  - services/api/app/routers/knowledge.py
  - services/api/app/main.py
  - uis/backoffice/app/(internal)/knowledge/page.tsx
  - uis/backoffice/app/(internal)/layout.tsx
  - uis/backoffice/app/globals.css
  - tests/pipelines/test_rag.py
  - services/api/tests/test_knowledge.py
  - data/eval/test-queries.json
  - data/eval/rag_recall_report.md
  - scripts/eval_rag_recall.py
  - docs/rag/rag-design.md
  - docker-compose.yml
  - pyproject.toml
  - services/api/requirements.txt
do_not_repeat:
  - Switch back to text-embedding-3-small or gpt-4o-mini (403 for this 4Geeks team)
  - Use glm-5.3-flash (listed by the gateway but returns 400 invalid model)
  - Hard-code a 1536 vector size (pplx-embed-v1-0.6b returns 1024; setup sizes from the vectors)
  - Raise min_score above about 0.45 or below about 0.15 without re-running scripts/eval_rag_recall.py --min-score 0
  - Run setup or the eval while the API holds the embedded local Qdrant store (single-process lock); use the Compose qdrant service instead
  - Return chunks or scores from the endpoint, or log the question text
  - Save the RAG Results eval without human confirmation
  - Rewrite PLAN-101
---

# HC-MS7-PLAN-102 — Coordinator Knowledge Base RAG Implementation

## What shipped

| Piece | Location |
|-------|----------|
| Corpus (verbatim, English) | `docs/company-knowledge-base/healthcore-{insurance-coverage,appointment-policy,referral-process,new-patient-checklist}.en.md` |
| Chunking, `embed()`, `setup()` + CLI | `data/process/rag.py` (`uv run python -m data.process.rag`) |
| `retrieve()`, `build_prompt()`, `generate_answer()`, `query()` | `data/pipelines/rag.py` |
| `POST /knowledge/query` | `services/api/app/routers/knowledge.py` (calls `query()` only; 503 on `KnowledgeBaseUnavailable`) |
| Backoffice page | `/knowledge` "Knowledge assistant" + nav link; scoped dark mode in `globals.css` |
| Qdrant | Compose service `qdrant` (6333, volume `qdrant_storage`); API gets `QDRANT_URL`. Without `QDRANT_URL`, embedded store at `data/process/.qdrant/` (gitignored) |
| Tests | `tests/pipelines/test_rag.py` (13), `services/api/tests/test_knowledge.py` (4) |
| Eval | `data/eval/test-queries.json` (16 + 4 negatives), `scripts/eval_rag_recall.py` → `data/eval/rag_recall_report.md` |
| Design doc | `docs/rag/rag-design.md` |

## Deviation from PLAN-101

PLAN-101 named `text-embedding-3-small` / `gpt-4o-mini`. The 4Geeks gateway (`llm.4geeks.ai`) returned **403** for this team. The allowlisted ids are now the defaults and `.env` values:

- Embeddings: `downtown-miami/openrouter/perplexity/pplx-embed-v1-0.6b` (1024-d)
- Generation: `downtown-miami/openrouter/openai/gpt-6-luna`

They are still two different 4Geeks-provided models, and `assert_distinct_models()` enforces that.

## Verification (2026-11-02)

- `setup()`: **14 chunks** (appointment-policy 4, insurance-coverage 3, new-patient-checklist 3, referral-process 4).
- Recall@3: **100%** (16/16, all rank 1), both with ranking only and with `min_score=0.30`. Lowest correct-chunk score 0.504; highest off-topic top-1 score 0.105.
- Sample answers: 12h cancellation → 50 USD / 40 GBP private-pay, with a Medicare/Medicaid exemption. Humana → split by country and verify with Tom Callahan. Wi-Fi password → not-enough-information sentence. Every answer ends with a `Source:` line.
- Live in-process `TestClient` against real models and the real index: no token → 401; with JWT → 200 `{"answer"}` only. The server log has chunk ids and scores, never the question.
- `python -m pytest tests/pipelines/test_rag.py services/api/tests/test_knowledge.py`: 17 passed. Full API suite: 71 passed. `tests/pipelines`: 27 passed.
- Backoffice `npm run lint` clean; `npx tsc --noEmit` exit 0.
- Not done: no live browser render of `/knowledge`. The sandbox stops long-running dev servers.

## Agent instructions

1. Present the "What We Will Evaluate" scores in chat. Write `memory-bank/evaluations/Results/RAGKnowledgeBase-20261102.md` only after human approval (next stamp).
2. When re-tuning `min_score`, run `uv run python scripts/eval_rag_recall.py --min-score 0` first and keep the value between the off-topic ceiling and the lowest correct-chunk score.
3. Do not close MS7 from this stamp.
