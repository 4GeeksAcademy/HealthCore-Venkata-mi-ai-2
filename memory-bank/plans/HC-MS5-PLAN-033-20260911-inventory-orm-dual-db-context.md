---
stamp: HC-MS5-PLAN-033
sequence: 33
milestone: MS5
date: 20260911
title: Inventory ORM Dual Database Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md — assignment CONTEXT locking SQLModel + TinyDB auth + Supabase inventory, /inventory/orders/* routes, current_stock, user_uuid, and HealthCore MedicalSupply examples. Docs only; no ORM or Supabase code.
related_paths:
  - docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Place CONTEXT-inventory-orm-dual-database.md directly under docs/
  - Treat this stamp as implemented SQLModel, Supabase, or inventory route changes
  - Replicate a user table in Supabase
  - Use POST /inventory/inbound instead of POST /inventory/orders/inbound
  - Store stock as a writable column or return raw ORM objects
  - Rewrite root CONTEXT.md or CONTEXT-MS5-inventory-backoffice.md
---

# HC-MS5-PLAN-033 — Inventory ORM Dual Database Context Document

## Decisions locked

- Context file path: `docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md`.
- Dual store: TinyDB for auth/users; Supabase/SQLModel for inventory writes.
- HealthCore product-equivalent ORM name: `MedicalSupply`; inbound `InboundOrder`; outbound `OutboundOrder`; FK `product_id`; extra fields `threshold`, `notes`.
- HTTP paths: `GET/POST /inventory/products`, `GET /inventory/products/{id}`, `POST /inventory/orders/inbound`, `POST /inventory/orders/outbound`, `GET /inventory/orders`.
- Response stock field: computed `current_stock`. Creator field: `user_uuid` (TinyDB user id string).
- Files: `database.py` + `get_db()`, `models.py`, `schemas.py`, `routers/inventory.py`.
- Docs only — no SQLModel engine, no Supabase schema, no route rewrites in this stamp.

## Agent instructions

1. Do not place `CONTEXT-inventory-orm-dual-database.md` directly under `docs/`.
2. Do not treat this stamp as implemented ORM, Supabase, or changed inventory routes.
3. Do not create a users table in Supabase or a global SQLModel session.
4. Implement later against this CONTEXT’s paths (`/inventory/orders/inbound`), not MS5 TinyDB `/inventory/inbound`.
5. Do not rewrite root `CONTEXT.md` or `CONTEXT-MS5-inventory-backoffice.md`.
6. Append a new stamp for implementation; do not rewrite this stamp.
