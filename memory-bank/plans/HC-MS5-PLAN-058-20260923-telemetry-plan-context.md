---
stamp: HC-MS5-PLAN-058
sequence: 58
milestone: MS5
date: 20260923
title: HealthCore Telemetry Plan Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/CONTEXT-telemetry-plan.md. Docs only. Two API gaps (reject direct stock fields, outbound threshold_crossed) must be implemented before docs/telemetry/.
related_paths:
  - docs/Project_Contexts/CONTEXT-telemetry-plan.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as instrumentation or as docs/telemetry/telemetry-plan.md
  - Add a route that writes current_stock
  - Put staff email, password, reset token, or order notes in a telemetry property
  - Instrument uis/healthcore
  - Document /auth/password-reset or /api/suppliers as live paths
  - Rewrite root CONTEXT.md or prior stamps
---

# HC-MS5-PLAN-058 — HealthCore Telemetry Plan Context Document

## Decisions locked

- Context path: `docs/Project_Contexts/CONTEXT-telemetry-plan.md`.
- Next code change is Gap A then Gap B in `services/api` only. Telemetry design files come after those gaps.
- Gap A: `POST /inventory/products` returns 400 `Stock cannot be modified directly. Register an inbound or outbound order.` when the raw JSON contains `stock` or `current_stock`. No insert.
- Gap B: `OutboundOrderResponse.threshold_crossed` is true only when live stock moves from `>= threshold` to `< threshold` on a successful outbound.
- `userId` for the later plan is TinyDB `user_uuid`. `created_by` email stays off events.

## Agent instructions

1. Do not write `docs/telemetry/` until Gaps A and B in the CONTEXT are implemented.
2. Do not add a product `PUT`/`PATCH` or a stored stock column while closing the gaps.
3. Do not emit telemetry events in the gap change.
4. Do not instrument `uis/healthcore`.
5. Do not rewrite this stamp when the gaps or the telemetry plan ship; append a new stamp.
