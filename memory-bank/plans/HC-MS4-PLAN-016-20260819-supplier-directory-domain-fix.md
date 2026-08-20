---
stamp: HC-MS4-PLAN-016
sequence: 16
milestone: MS4
date: 20260819
title: Supplier Directory Official CONTEXT Domain Fix
status: implemented
phase: implementation
summary: Domain-only fix for teacher rejection — monthly_rate, currency USD/GBP paired with USA/UK, categories field, 15 seeds including McKesson and Epic. Routes, TinyDB path, idempotent seed, filters, and rate/status patches unchanged. Prior stamps and accepted submissions not rewritten.
related_paths:
  - docs/Project_Contexts/SupplierDirectory_TinyDb_API.md
  - services/api/app/models/suppliers.py
  - services/api/app/suppliers_store.py
  - services/api/app/routers/suppliers.py
  - services/api/README.md
  - uis/backoffice/types/supplier.ts
  - uis/backoffice/lib/suppliers-api.ts
  - uis/backoffice/components/suppliers/SupplierDirectoryPanel.tsx
  - uis/backoffice/app/suppliers/page.tsx
  - memory-bank/evaluations/Results/SupplierDirectory-20260819.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Revert monthly_rate to contract_rate
  - Revert country USA to US
  - Restore the six synthetic vendors (MediSupply Austin, etc.)
  - Rewrite PLAN-013, PLAN-014, or PLAN-015
  - Rewrite MS4_Project_Eval or Incident Analyzer files
  - Change supplier HTTP routes or TinyDB path
---

# HC-MS4-PLAN-016 — Supplier Directory Official CONTEXT Domain Fix

## Decisions locked

- Teacher accepted structure (idempotent TinyDB seed, filters, rate/status patches). Only the domain was rejected.
- Field contract: `monthly_rate`, `currency` (`USA`→`USD`, `UK`→`GBP`), `country` `USA`/`UK`, `categories` (same allowed values as before).
- Seed: 15 suppliers including McKesson and Epic. Legacy TinyDB rows with `contract_rate` / `US` / `product_categories` are truncated once, then idempotent insert by name+country resumes.
- CONTEXT surgical patch in `docs/Project_Contexts/SupplierDirectory_TinyDb_API.md` only. Root `CONTEXT.md` unchanged.

## Agent instructions

1. Do not revert `monthly_rate`, `USA`/`UK`, or `currency` pairing.
2. Do not restore the six custom synthetic vendors.
3. Do not rewrite prior plan stamps, MS4 eval, or Incident Analyzer work.
4. Keep `/suppliers` HTTP matrix, TinyDB path, and incident routes.
5. Append new stamps for follow-up; do not rewrite this stamp.
6. If backoffice `npm run lint` / `npx tsc --noEmit` was skipped due to npm TLS, run them when the registry is reachable before commit.
