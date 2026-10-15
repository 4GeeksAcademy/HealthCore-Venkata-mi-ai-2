---
stamp: HC-MS6-PLAN-087
sequence: 87
milestone: MS6
date: 2026-10-14
title: CONTEXT-healthcore Additive Gaps Closure Plan
status: implemented
phase: planning
summary: >
  Plan to close CONTEXT-healthcore gaps additively: product category/expiry,
  order clinic/country/department, supply_expiry_flagged emitter, telemetry
  allowlist properties, richer seed. Must not break prior MS5/MS6 evals or
  rename existing event types/routes.
related_paths:
  - CONTEXT-healthcore.md
  - services/api/app/inventory/
  - uis/backoffice/lib/telemetry.ts
  - docs/telemetry/telemetry-plan.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Rename inbound_order_created or other existing event types
  - Merge job_runs into pipeline_runs
  - Require new fields without defaults on existing POST bodies
  - Change GET /telemetry/report or analysis.py for this stamp
  - Close MS6 from this stamp
---

# HC-MS6-PLAN-087 — CONTEXT-healthcore Additive Gaps Closure Plan

## Decisions locked

- Additive only: optional/defaulted columns and allowlist **extensions**.
- Defaults: `category=consumable`, `clinic_id=us-tx-001`, `country=US`, outbound `department=general_consultation`.
- Emit `supply_expiry_flagged` when product `expiry_date` is within 30 days (UTC).
- Enrich `SEED_ROWS` toward CONTEXT §5 without removing existing SKUs.
- Implementation stamp: PLAN-088.

## Agent instructions

1. Do not break TinyDB or Supabase inventory backends.
2. Keep public `uis/healthcore` untouched.
3. Run inventory/telemetry-related tests after changes.
