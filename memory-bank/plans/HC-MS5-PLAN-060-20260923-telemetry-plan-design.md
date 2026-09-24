---
stamp: HC-MS5-PLAN-060
sequence: 60
milestone: MS5
date: 20260923
title: HealthCore Telemetry Plan And Event Schemas
status: implemented
phase: docs
summary: Design-only telemetry catalogue, envelope, stream versus batch, and draft-07 schemas under docs/telemetry. No emitters.
related_paths:
  - docs/telemetry/telemetry-plan.md
  - docs/telemetry/event-schemas.json
  - docs/README.md
  - docs/Project_Contexts/CONTEXT-telemetry-plan.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Instrument uis/healthcore
  - Put staff email, password, reset token, order notes, or error message text in event properties
  - Treat GET /inventory/products color state as stock_threshold_triggered
  - Document /auth/password-reset or /api/suppliers as live paths
  - Rewrite PLAN-058 or PLAN-059
---

# HC-MS5-PLAN-060 — HealthCore Telemetry Plan And Event Schemas

## Decisions locked

- Canonical design is `docs/telemetry/telemetry-plan.md` plus `docs/telemetry/event-schemas.json`.
- `schemaVersion` is `1.0.0`. `userId` is TinyDB user id or null.
- `stock_threshold_triggered` fires only when outbound `threshold_crossed` is true, using live before/after stock.
- This stamp does not add emitters.

## Agent instructions

1. Do not emit events until a later implementation task says to.
2. Validate emits against `event-schemas.json`. Drop invalid payloads without logging them.
3. Do not add `notes`, email, passwords, or reset tokens to `properties`.
4. Do not instrument `uis/healthcore`.
5. Append a new stamp for instrumentation. Do not rewrite this file.
