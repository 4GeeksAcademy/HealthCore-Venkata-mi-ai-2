---
stamp: HC-MS5-PLAN-071
sequence: 71
milestone: MS5
date: 2026-09-28
title: Telemetry Storage Supabase Bulk Persist
status: implemented
phase: implementation
summary: >
  Replaced stub POST /telemetry/events with per-event TelemetryEvent.model_validate,
  single-transaction bulk insert into Supabase telemetry_events, and response
  {received, stored, rejected}. TelemetryEvent fields unchanged; frontend untouched.
  tags JSONB holds allowlisted properties plus envelope ids. Pytest 61 passed.
related_paths:
  - docs/Project_Contexts/CONTEXT-telemetry-storage.md
  - docs/telemetry/telemetry-plan.md
  - services/api/app/telemetry/models.py
  - services/api/app/telemetry/store.py
  - services/api/app/routers/telemetry.py
  - services/api/app/models/telemetry.py
  - services/api/app/main.py
  - services/api/tests/test_telemetry.py
  - services/api/tests/conftest.py
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Do not type the request body as list[TelemetryEvent] (whole-batch 422).
  - Do not modify TelemetryEvent field definitions for this storage phase.
  - Do not change uis/backoffice telemetry client for this phase.
  - Do not add UPDATE/DELETE for telemetry_events.
  - Do not write Results/TelemetryStorage-*.md until the human says save.
---

# HC-MS5-PLAN-071 — Telemetry Storage Supabase Bulk Persist

## Decisions locked

- Loose envelope `TelemetryBatchEnvelope.events: list[Any]`; validate each item with unchanged `TelemetryEvent`.
- One `session.add_all` + commit per batch.
- `tags` = properties + `eventId` / `sessionId` / `userId` / `schemaVersion` / `requestId` (documented in `telemetry-plan.md`).
- Telemetry uses `SUPABASE_DATABASE_URL` when set, else `DATABASE_URL` (SQLite in pytest).
- Startup migrates `tags` to JSONB and creates GIN index when on Postgres.

## Agent instructions

1. Evaluation checklist is in CONTEXT-telemetry-storage.md §5 — show Pass/Fail in chat; wait for **save** before Results file.
2. After `.env` / schema changes, recreate or restart the API container.
3. Do not commit `.env` or secrets.
