---
stamp: HC-MS5-PLAN-035
sequence: 35
milestone: MS5
date: 20260911
title: Inventory Table Editor Readable Names and Product Labels
status: implemented
phase: implementation
summary: Renamed mashed SQLModel tables to medical_supply / inbound_order / outbound_order, stored product_name and sku on orders, added inventory_order view, and backfilled labels so Supabase Table Editor matches the backoffice UI.
related_paths:
  - services/api/app/database.py
  - services/api/app/inventory/models.py
  - services/api/app/inventory/service.py
  - services/api/app/routers/inventory.py
  - services/api/tests/test_inventory.py
  - docs/Project_Contexts/CONTEXT-inventory-orm-dual-database.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Restore mashed table names medicalsupply / inboundorder / outboundorder as the live schema
  - Drop EduTrack leftover tables (students, courses, enrollments)
  - Put users in Supabase or add a writable stock column
  - Point pytest at live Supabase
  - Commit .env or DATABASE_URL passwords
  - Rewrite PLAN-034 or MS5_Project_Eval.md
---

# HC-MS5-PLAN-035 — Inventory Table Editor Readable Names and Product Labels

## Decisions locked

- Postgres table names are `medical_supply`, `inbound_order`, `outbound_order`.
- Order rows store denormalized `product_name` and `sku` for Table Editor readability. Stock remains computed (`SUM(inbound) − SUM(outbound)`).
- Combined history for Table Editor is view `inventory_order` with `type` inbound|outbound.
- Startup migration adopts leftover mashed names and empty snake_case `create_all` tables without dropping seed data.
- HTTP routes and dual-store contract from PLAN-034 are unchanged.

## Agent instructions

1. Keep snake_case inventory table names and denormalized order labels.
2. Do not drop `students` / `courses` / `enrollments` if they exist in the same Supabase project.
3. Do not restore TinyDB inventory or a writable stock column.
4. Keep pytest on isolated SQLite.
5. Append a new stamp for later work; do not rewrite this file or PLAN-034.
