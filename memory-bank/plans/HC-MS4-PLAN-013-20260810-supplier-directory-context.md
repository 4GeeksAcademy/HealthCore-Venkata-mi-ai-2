---
stamp: HC-MS4-PLAN-013
sequence: 13
milestone: MS4
date: 20260810
title: Company Supplier Directory TinyDB API Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/SupplierDirectory_TinyDb_API.md — assignment CONTEXT locking HealthCore supplier fields (contract_rate, active/suspended, product categories), seed suppliers, API/UI requirements, and evaluation checklist. Docs only; no TinyDB/API/backoffice code.
related_paths:
  - docs/Project_Contexts/SupplierDirectory_TinyDb_API.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Create docs/Plans/ for this work
  - Place SupplierDirectory_TinyDb_API.md directly under docs/
  - Treat this stamp as implemented seed.py / suppliers API / backoffice /suppliers page
  - Rewrite root CONTEXT.md for the supplier directory assignment
---

# HC-MS4-PLAN-013 — Company Supplier Directory TinyDB API Context Document

## Decisions locked

- Context file path: `docs/Project_Contexts/SupplierDirectory_TinyDb_API.md` (not `docs/` root).
- Plan archive: `memory-bank/plans/` only — no `docs/Plans/`.
- Root `CONTEXT.md` / `CONTEXT_temp.md` unchanged.
- Rate field name: `contract_rate` (positive float, USD).
- Statuses: `active` / `suspended`.
- Categories: `MEDICAL_SUPPLIES`, `LAB_CONSUMABLES`, `PPE`, `PHARMACEUTICALS`, `IT_EQUIPMENT`, `FACILITIES`, `DIAGNOSTIC_EQUIPMENT`.
- Categories field: `product_categories` (non-empty list).
- Seed: 6 synthetic suppliers; seeder dedupes by `name` + `country`.
- Frontend path in this monorepo: `uis/backoffice` (not `/src/backoffice`).
- Docs only — no TinyDB, FastAPI suppliers routes, `seed.py`, or backoffice page in this stamp.

## Agent instructions

1. Do not create `docs/Plans/`.
2. Do not place `SupplierDirectory_TinyDb_API.md` directly under `docs/`.
3. Do not treat this stamp as implemented supplier code (`seed.py`, `/suppliers` API, or backoffice `/suppliers` page).
4. Do not rewrite root `CONTEXT.md` for the supplier directory; use `docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`.
5. Implementation must match the CONTEXT field names, enums, and seed table exactly.
6. Append new stamps for implementation work; do not rewrite this stamp.
