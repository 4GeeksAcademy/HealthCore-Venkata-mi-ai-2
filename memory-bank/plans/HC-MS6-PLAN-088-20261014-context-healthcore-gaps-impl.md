---
stamp: HC-MS6-PLAN-088
sequence: 88
milestone: MS6
date: 2026-10-14
title: CONTEXT-healthcore Additive Gaps Implementation
status: implemented
phase: implementation
summary: >
  Closed CONTEXT-healthcore gaps additively: product category/expiry, order
  clinic/country/department, supply_expiry_flagged emitter, telemetry allowlist
  + schema extensions, richer seed (10 SKUs). Did not rename events or break
  inventory/job_runs contracts. Does not close MS6.
related_paths:
  - CONTEXT-healthcore.md
  - services/api/app/inventory/
  - services/api/app/inventory_store.py
  - services/api/app/database.py
  - uis/backoffice/lib/telemetry.ts
  - uis/backoffice/lib/inventory-api.ts
  - uis/backoffice/lib/clinic-context.ts
  - uis/backoffice/components/inventory/
  - docs/telemetry/telemetry-plan.md
  - docs/telemetry/event-schemas.json
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Redo seed expansion for the same ten SKUs without need
  - Rename existing inventory event types
  - Require clinic fields without defaults on legacy clients
  - Change GET /telemetry/report or analysis.py for this stamp
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-088 — CONTEXT-healthcore Additive Gaps Implementation

## Decisions locked

- Defaults: `consumable`, `us-tx-001`, `US`, `general_consultation`.
- Postgres migration adds columns with defaults; TinyDB stores optional keys.
- `supply_expiry_flagged` fires when `expiry_date` is within 30 UTC days.
- Pytest inventory+cache **21 passed**; jobs **8 passed**.

## Agent instructions

1. Keep Option A pipeline fixture until live tagged events are plentiful.
2. Do not remove existing glove/pad SKUs.
3. Do not close MS6 from this stamp.
