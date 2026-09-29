---
stamp: HC-MS5-PLAN-069
sequence: 69
milestone: MS5
date: 20260928
title: Inventory Backend Switch TinyDB Or Supabase
status: implemented
phase: implementation
summary: INVENTORY_BACKEND=tinydb|supabase switches inventory persistence. Auth/suppliers stay TinyDB. Supabase uses decrypted SUPABASE_DATABASE_URL and create_all for medical_supply and order tables.
related_paths:
  - services/api/app/inventory/repo.py
  - services/api/app/inventory_store.py
  - services/api/app/routers/inventory.py
  - services/api/app/database.py
  - services/api/app/core/config.py
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Move auth or suppliers into Supabase in this stamp
  - Commit .env or plaintext database passwords
  - Restore a writable stock column
  - Sync TinyDB inventory rows into Supabase automatically
---

# HC-MS5-PLAN-069 — Inventory Backend Switch TinyDB Or Supabase

## Decisions locked

- `INVENTORY_BACKEND=tinydb` → `services/api/data/inventory.json`.
- `INVENTORY_BACKEND=supabase` → SQLModel via `SUPABASE_DATABASE_URL` (supports `enc:v1:`) or `DATABASE_URL`.
- Auth and suppliers remain TinyDB.
- `/health` reports `inventory_backend`.

## Agent instructions

- After changing `INVENTORY_BACKEND` or `.env`, recreate the API container so env_file reloads.
- If Supabase returns password authentication failed, fix `SUPABASE_DATABASE_URL` and re-encrypt; do not log the URI.
- Run `python seed.py` after the first successful Supabase connect.
