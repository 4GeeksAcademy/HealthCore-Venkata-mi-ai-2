---
stamp: HC-MS5-PLAN-030
sequence: 30
milestone: MS5
date: 20260909
title: MS5 Inventory API and Backoffice Implementation
status: implemented
phase: implementation
summary: Shipped authenticated TinyDB /inventory API plus four backoffice views (stock, inbound, outbound with available stock before quantity, order history). Central inventory-api module, readable 400s, pytest/Jest coverage. Eval 8/8 Pass.
related_paths:
  - services/api/app/routers/inventory.py
  - services/api/app/inventory_store.py
  - services/api/app/models/inventory.py
  - services/api/app/main.py
  - services/api/seed.py
  - services/api/tests/conftest.py
  - services/api/tests/test_inventory.py
  - uis/backoffice/lib/inventory-api.ts
  - uis/backoffice/lib/user-facing-error.ts
  - uis/backoffice/lib/authed-fetch.ts
  - uis/backoffice/types/inventory.ts
  - uis/backoffice/app/inventory/page.tsx
  - uis/backoffice/app/inventory/inbound/page.tsx
  - uis/backoffice/app/inventory/outbound/page.tsx
  - uis/backoffice/app/inventory/orders/page.tsx
  - uis/backoffice/components/inventory/ProductStockPanel.tsx
  - uis/backoffice/components/inventory/InboundOrderForm.tsx
  - uis/backoffice/components/inventory/OutboundOrderForm.tsx
  - uis/backoffice/components/inventory/OrderHistoryPanel.tsx
  - TESTING.md
  - memory-bank/evaluations/MS5_Project_Eval.md
  - memory-bank/evaluations/Results/InventoryBackoffice-20260909.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Scatter inventory fetch calls across pages
  - Hang inventory HTTP on lib/api-client.ts
  - Add inventory UI to uis/healthcore
  - Point pytest at live services/api/data/inventory.json
  - Invent a second auth pattern for inventory routes
  - Rewrite CONTEXT-MS5 or prior MS5 stamps
---

# HC-MS5-PLAN-030 — MS5 Inventory API and Backoffice Implementation

## Decisions locked

- Inventory persists in TinyDB `services/api/data/inventory.json` (gitignored), separate from suppliers/auth.
- Routes: `GET /inventory/products`, `POST /inventory/inbound`, `POST /inventory/outbound`, `GET /inventory/orders`. All require JWT.
- Seed SKUs: `HC-PPE-GLV-100` (12/24, low) and `HC-CLN-PAD-200` (80/30, OK).
- Insufficient stock returns **400** `Insufficient stock. Available: {n}. Requested: {m}.`
- Backoffice views: `/inventory`, `/inventory/inbound`, `/inventory/outbound`, `/inventory/orders` behind existing `AuthGuard`.
- One client module: `lib/inventory-api.ts` + `authedFetch`.
- Outbound UI shows available stock above the quantity field.
- Eval: [MS5_Project_Eval.md](../evaluations/MS5_Project_Eval.md) **8/8 Pass**.

## Agent instructions

1. Keep inventory HTTP in `lib/inventory-api.ts`. Do not use `lib/api-client.ts`.
2. Isolate pytest TinyDB; never write live `data/inventory.json` from tests.
3. Do not add inventory pages to `uis/healthcore`.
4. Do not remove outbound available-stock display or readable 400 handling.
5. Do not rewrite PLAN-028/029 or CONTEXT-MS5; append new stamps for later work.
