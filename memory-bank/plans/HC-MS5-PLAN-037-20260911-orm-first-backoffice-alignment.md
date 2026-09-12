---
stamp: HC-MS5-PLAN-037
sequence: 37
milestone: MS5
date: 20260911
title: ORM-First Sequence Alignment and Dual Eval Re-run
status: implemented
phase: implementation
summary: Locked canonical order as Inventory ORM dual-database then MS5 backoffice. HTTP orders keep SQLModel user_uuid and add TinyDB created_by email for history. CONTEXTs, mapper tests, and both evals re-run Pass (12/12 and 8/8).
related_paths:
  - services/api/app/inventory/schemas.py
  - services/api/app/inventory/service.py
  - services/api/app/routers/inventory.py
  - services/api/tests/test_inventory.py
  - uis/backoffice/lib/inventory-api.ts
  - uis/backoffice/__tests__/inventory.test.ts
  - docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md
  - docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md
  - docs/README.md
  - TESTING.md
  - memory-bank/evaluations/Results/InventoryORM-20260911.md
  - memory-bank/evaluations/Results/InventoryBackoffice-20260909.md
  - memory-bank/evaluations/MS5_Project_Eval.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Restore TinyDB inventory_store.py or POST /inventory/inbound as the live write path
  - Store staff email on SQLModel/Supabase order tables instead of user_uuid
  - Put a users table in Supabase or a writable stock column
  - Rewrite PLAN-028–036 bodies
  - Commit .env or DATABASE_URL passwords
  - Add inventory UI to uis/healthcore
---

# HC-MS5-PLAN-037 — ORM-First Sequence Alignment and Dual Eval Re-run

## Decisions locked

- Canonical sequence: **(1)** CONTEXT-inventory-orm-dual-database, **(2)** CONTEXT-MS5-inventory-backoffice.
- SQLModel orders persist `user_uuid` only. HTTP may include `created_by` as TinyDB email for the backoffice creator column.
- UI calls `/inventory/orders/inbound` and `/inventory/orders/outbound`. Display stock comes from `current_stock`.
- PLAN-028–032 remain historical (TinyDB stand-in API). Do not rewrite those stamps.
- Eval: ORM **12/12 Pass**; MS5 UI **8/8 Pass** (appended re-run).

## Agent instructions

1. Treat ORM dual-database as the inventory API contract. Do not invent a second TinyDB inventory store.
2. Keep `user_uuid` on ORM rows. Do not copy a users table into Supabase.
3. Keep the backoffice on `lib/inventory-api.ts` with outbound available-stock and readable 400s.
4. Append a new stamp for later work; do not rewrite this file or PLAN-028–036.
