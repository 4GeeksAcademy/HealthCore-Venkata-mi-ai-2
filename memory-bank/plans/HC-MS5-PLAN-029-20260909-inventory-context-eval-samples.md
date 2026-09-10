---
stamp: HC-MS5-PLAN-029
sequence: 29
milestone: MS5
date: 20260909
title: MS5 Inventory CONTEXT Evaluation Rubric and Samples
status: implemented
phase: docs
summary: Updated CONTEXT-MS5-inventory-backoffice.md with the official eight-item evaluation rubric and HealthCore sample JSON for products, inbound/outbound orders, 400 insufficient stock, empty arrays, and 401. Docs only; no inventory UI code.
related_paths:
  - docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as implemented inventory pages or inventory API routes
  - Rewrite HC-MS5-PLAN-028
  - Invent a second sample field set that drops name/sku/stock/threshold or order created_by
  - Dump raw 400 JSON in the UI when implementing later
---

# HC-MS5-PLAN-029 — MS5 Inventory CONTEXT Evaluation Rubric and Samples

## Decisions locked

- Official evaluation list is the eight bullets in CONTEXT-MS5 (central API module, color-coded stock, inbound confirm/error, outbound available stock before quantity, readable insufficient-stock 400, order history columns, empty-array empty state, auth redirect to `/login`).
- Sample product fields: `id`, `name`, `sku`, `stock`, `threshold`. Low stock = `stock` < `threshold`.
- Sample order write body: `product_id`, `quantity`, `notes`.
- Sample order read fields: `id`, `product_id`, `product_name`, `quantity`, `type` (`inbound` \| `outbound`), `notes`, `created_at`, `created_by`.
- Suggested paths: `GET /inventory/products`, `POST /inventory/inbound`, `POST /inventory/outbound`, `GET /inventory/orders`. Confirm aliases in live OpenAPI.
- Insufficient-stock sample detail: `Insufficient stock. Available: 12. Requested: 20.`
- Docs only — no inventory UI in this stamp.

## Agent instructions

1. Do not treat this stamp as shipped inventory UI.
2. Do not rewrite PLAN-028; this stamp extends the CONTEXT.
3. When implementing, follow the eight-item rubric and the sample payloads in `docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md`.
4. Surface 400 `detail` as readable text; never render the raw JSON object.
5. Append a new stamp for UI implementation; do not rewrite this stamp.
