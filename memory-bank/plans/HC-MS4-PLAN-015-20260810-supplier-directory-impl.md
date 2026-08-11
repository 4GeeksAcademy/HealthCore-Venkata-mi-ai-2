---
stamp: HC-MS4-PLAN-015
sequence: 15
milestone: MS4
date: 20260810
title: Supplier Directory TinyDB API and Backoffice Implementation
status: implemented
phase: implementation
summary: Implemented TinyDB supplier directory per CONTEXT — Pydantic models, seed.py, FastAPI /suppliers routes, backoffice /suppliers UI with filters/create/rate/status. Eval Pass for API/seeder (SupplierDirectory-20260810.md). Process to Run saved on cursor plan.
related_paths:
  - docs/Project_Contexts/SupplierDirectory_TinyDb_API.md
  - services/api/app/models/suppliers.py
  - services/api/app/suppliers_store.py
  - services/api/app/routers/suppliers.py
  - services/api/seed.py
  - services/api/app/main.py
  - services/api/requirements.txt
  - services/api/README.md
  - uis/backoffice/app/suppliers/page.tsx
  - uis/backoffice/components/suppliers/SupplierDirectoryPanel.tsx
  - uis/backoffice/lib/suppliers-api.ts
  - uis/backoffice/types/supplier.ts
  - memory-bank/evaluations/Results/SupplierDirectory-20260810.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Re-author SupplierDirectory_TinyDb_API.md field contract
  - Change rate field away from contract_rate
  - Remove or break incidents router
  - Move TinyDB path away from services/api/data/suppliers.json
  - Rewrite PLAN-013 or PLAN-014
---

# HC-MS4-PLAN-015 — Supplier Directory TinyDB API and Backoffice Implementation

## Decisions locked

- CONTEXT path remains `docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`.
- TinyDB: `services/api/data/suppliers.json` (gitignored); seed + API share `app/suppliers_store.py`.
- HTTP matrix: POST 201; GET/PATCH/DELETE 200; 404 missing; 422 invalid.
- Backoffice page: `/suppliers` with nav link; API default `http://localhost:8001`.
- Evaluation results: `memory-bank/evaluations/Results/SupplierDirectory-20260810.md`.

## Agent instructions

1. Do not rewrite CONTEXT field names, enums, or seed table without a new stamp.
2. Keep Incident Analyzer routes working on the same FastAPI app.
3. Do not commit `data/suppliers.json`.
4. Append new stamps for follow-up work; do not rewrite this stamp.
5. If lint/tsc was skipped due to npm TLS, run `npm run lint` and `npx tsc --noEmit` in `uis/backoffice` before commit when the registry is reachable.
