---
stamp: HC-MS5-PLAN-059
sequence: 59
milestone: MS5
date: 20260923
title: Inventory Direct Stock Rejection And Threshold Cross
status: implemented
phase: implementation
summary: POST /inventory/products returns 400 when the raw JSON contains stock or current_stock and does not insert. Successful outbound responses include threshold_crossed from live before/after stock.
related_paths:
  - services/api/app/inventory/service.py
  - services/api/app/inventory/schemas.py
  - services/api/app/routers/inventory.py
  - services/api/tests/test_inventory.py
  - docs/Project_Contexts/CONTEXT-telemetry-plan.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Add a product PUT or PATCH that writes current_stock
  - Treat the stock-page color chip as the threshold alert
  - Emit telemetry events in this gap
  - Rewrite PLAN-058
---

# HC-MS5-PLAN-059 — Inventory Direct Stock Rejection And Threshold Cross

## Decisions locked

- Gap A detail string is `Stock cannot be modified directly. Register an inbound or outbound order.`
- Forbidden keys on `POST /inventory/products` are `stock` and `current_stock`, checked on the raw JSON before insert.
- Gap B field is `OutboundOrderResponse.threshold_crossed`. True only when live stock moves from `>= threshold` to `< threshold`.
- Inbound responses do not carry the flag. A 400 insufficient-stock body does not carry it.

## Agent instructions

1. Do not add a route that sets `current_stock`.
2. Do not drop `threshold_crossed` from the outbound 201 body.
3. Keep the direct-stock 400 detail string stable; the telemetry plan maps that response to `direct_stock_edit_rejected`.
4. Append a new stamp for further inventory or telemetry work. Do not rewrite this file.
