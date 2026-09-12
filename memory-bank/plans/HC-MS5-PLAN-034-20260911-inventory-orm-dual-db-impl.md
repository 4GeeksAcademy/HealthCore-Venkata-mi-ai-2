---
stamp: HC-MS5-PLAN-034
sequence: 34
milestone: MS5
date: 20260911
title: Inventory ORM Dual Database Implementation
status: implemented
phase: implementation
summary: Replaced TinyDB inventory with SQLModel (Supabase via DATABASE_URL, SQLite in tests). MedicalSupply/InboundOrder/OutboundOrder, computed current_stock, user_uuid, /inventory/orders/* routes, seed net 12/80. Pytest 45, Jest 15. Eval 12/12 Pass.
related_paths:
  - services/api/app/database.py
  - services/api/app/inventory/models.py
  - services/api/app/inventory/schemas.py
  - services/api/app/inventory/service.py
  - services/api/app/routers/inventory.py
  - services/api/app/main.py
  - services/api/app/core/config.py
  - services/api/seed.py
  - services/api/requirements.txt
  - services/api/tests/conftest.py
  - services/api/tests/test_inventory.py
  - uis/backoffice/lib/inventory-api.ts
  - docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md
  - memory-bank/evaluations/Results/InventoryORM-20260911.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Restore TinyDB inventory_store.py as the live inventory store
  - Put users in Supabase or a writable stock column on MedicalSupply
  - Point pytest at live Supabase or data/inventory.json
  - Commit .env or DATABASE_URL passwords
  - Rewrite MS5_Project_Eval.md or PLAN-033
---

# HC-MS5-PLAN-034 — Inventory ORM Dual Database Implementation

## Decisions locked

- Dual store: TinyDB auth; SQLModel engine from `DATABASE_URL` for inventory.
- ORM names: `MedicalSupply`, `InboundOrder`, `OutboundOrder`; FK `product_id`.
- HTTP: `GET/POST /inventory/products`, `GET /inventory/products/{id}`, `POST /inventory/orders/inbound`, `POST /inventory/orders/outbound`, `GET /inventory/orders`.
- `current_stock` computed; `user_uuid` from TinyDB user id string.
- Tests use `sqlite://` + StaticPool; schema via `create_all` on startup.
- Backoffice client maps new fields/paths so existing `/inventory` pages still work.
- Eval: [InventoryORM-20260911.md](../evaluations/Results/InventoryORM-20260911.md) 12/12 Pass.

## Agent instructions

1. Do not restore TinyDB as the inventory write path.
2. Do not add a users table in Supabase or a client-writable stock field.
3. Keep pytest on isolated SQLite; do not use live `DATABASE_URL` in unit tests.
4. Do not rewrite this stamp or MS5 UI eval.
5. Append a new stamp for later work (including a dedicated product-create UI if requested).
