---
stamp: HC-MS4-PLAN-014
sequence: 14
milestone: MS4
date: 20260810
title: Supplier Directory TinyDB CONTEXT Evaluation Tighten
status: implemented
phase: docs
summary: Tightened docs/Project_Contexts/SupplierDirectory_TinyDb_API.md with HTTP status matrix (POST 201), PATCH 404, country US/UK enum, AND filters, TinyDB path data/suppliers.json, exact seeder message, sample JSON, and frontend required fields. Docs only; no TinyDB/API/UI code.
related_paths:
  - docs/Project_Contexts/SupplierDirectory_TinyDb_API.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Rewrite HC-MS4-PLAN-013
  - Rewrite root CONTEXT.md for the supplier directory
  - Treat this stamp as implemented seed.py / suppliers API / backoffice /suppliers page
  - Invent alternate rate/status/category field names
---

# HC-MS4-PLAN-014 — Supplier Directory TinyDB CONTEXT Evaluation Tighten

## Decisions locked

- HTTP: POST **201**; GET/PATCH/DELETE success **200**; DELETE body `{"ok": true, "id": ...}`.
- PATCH rate/status → **404** when id missing.
- `country` Enum/Literal: `US` | `UK` only → **422** otherwise.
- Combined `country` + `category` query → **AND**.
- `status` required on create (no default).
- Seeder prints exactly `Inserted N supplier(s).`
- TinyDB path: `services/api/data/suppliers.json` (gitignore in impl stamp).
- Frontend required client fields: name, country, product_categories, contract_rate, status.
- Sample JSON section added for valid/invalid payloads.
- Docs only — implementation remains a later stamp.

## Agent instructions

1. Do not rewrite PLAN-013 or root `CONTEXT.md`.
2. Do not treat this stamp as supplier implementation code.
3. Implementation must match the tightened CONTEXT (HTTP matrix, path, enums, AND filters, seeder message).
4. Append new stamps for implementation; do not rewrite this stamp.
