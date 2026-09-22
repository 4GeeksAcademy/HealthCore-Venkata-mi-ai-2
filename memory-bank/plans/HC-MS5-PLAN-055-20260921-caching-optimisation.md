---
stamp: HC-MS5-PLAN-055
sequence: 55
milestone: MS5
date: 20260921
title: Performance Optimisation Caching Implementation
status: implemented
phase: implementation
summary: Timing middleware, in-process TTL cache on GET /suppliers and GET /inventory/products with write invalidation, load seeder, two next/dynamic panels, non-trivial useMemo aggregations, CACHING_REPORT.md.
related_paths:
  - docs/Project_Contexts/Performance_Optimisation_Caching.md
  - docs/CACHING_REPORT.md
  - docs/README.md
  - services/api/app/core/ttl_cache.py
  - services/api/app/core/response_cache.py
  - services/api/app/main.py
  - services/api/app/routers/suppliers.py
  - services/api/app/routers/inventory.py
  - services/api/app/load_seed.py
  - services/api/seed_load.py
  - services/api/profile_cache.py
  - services/api/tests/test_cache.py
  - services/api/tests/conftest.py
  - uis/backoffice/app/(internal)/incidents/page.tsx
  - uis/backoffice/app/(internal)/suppliers/page.tsx
  - uis/backoffice/components/suppliers/SupplierDirectoryPanel.tsx
  - uis/backoffice/components/inventory/ProductStockPanel.tsx
  - uis/backoffice/lib/supplier-directory-metrics.ts
  - uis/backoffice/lib/inventory-stock-metrics.ts
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Cache GET /auth/me, GET /profiles/me, or GET /users under a shared key
  - Serve outbound available-stock checks from the product-list cache
  - Add Redis or a Compose cache service for this assignment
  - Lazy-load Milestone2OpsPanel headlines on /ops
  - Restore useMemo(() => PRODUCT_CATEGORIES, [])
---

# HC-MS5-PLAN-055 — Performance Optimisation Caching Implementation

## Decisions locked

- Cache **only** `GET /suppliers` (60s TTL, filter-scoped keys) and `GET /inventory/products` (30s TTL).
- Authenticate first; shared keys contain **no user id**. Supplier directory and product stock are identical for every Digital JWT.
- Invalidate on successful writes. Outbound quantity uses live SQL `current_stock_for`.
- Lazy-load `IncidentAnalyzerPanel` and `SupplierDirectoryPanel`. Memoize `summarizeSupplierDirectory` and `buildStockInsights`.
- Canonical write-up is [`docs/CACHING_REPORT.md`](../../docs/CACHING_REPORT.md).

## Agent instructions

1. Do not put session or staff-identity JSON in `response_cache` under a shared key.
2. Keep timing logs to method, path, status, and ms — no tokens, query strings, or emails.
3. Re-run `python -m pytest` in `services/api` after cache-key or invalidation changes.
4. Load data: `python seed_load.py`. Timings: `python profile_cache.py` (isolated stores).
5. Same-day caching re-evals overwrite `memory-bank/evaluations/Results/Caching-20260921.md` only.
