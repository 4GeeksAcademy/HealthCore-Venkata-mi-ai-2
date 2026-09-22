# Caching technical report

**Date:** 2026-09-21  
**Assignment:** [`docs/Project_Contexts/Performance_Optimisation_Caching.md`](./Project_Contexts/Performance_Optimisation_Caching.md)  
**Implementation stamp:** `HC-MS5-PLAN-055`

This is not a cache-everything pass. Each choice is scored on **cost × frequency × stability**, then on **freshness risk**. Shared cache keys are used only for staff-directory payloads that are identical for every authenticated HealthCore Digital user.

## How evidence was collected

1. **Timing middleware** in `services/api/app/main.py` logs `METHOD path → status | duration_ms` (path only; no query string, token, or email).
2. **Load seeder** `python seed_load.py` (from `services/api`) keeps the official CONTEXT catalog and adds synthetic load rows so TinyDB/SQL work is visible. Idempotent prefixes: `Load Clinic Vendor NNN`, SKU `HC-LOAD-*`.
3. **Isolated profiler** `python profile_cache.py` uses TestClient + ephemeral SQLite/TinyDB (same isolation as pytest). It never touches live `auth.json`, `suppliers.json`, or Supabase.

**Row counts used for timings**

| Store | Before (CONTEXT seed) | After load seed |
| --- | --- | --- |
| Suppliers (TinyDB) | 15 named vendors | **200** load vendors |
| Medical supplies | 2 SKUs | **40** load SKUs |
| Inbound + outbound orders | 3 seed movements | **1,280** load movements (20 inbound + 12 outbound per SKU) |

**Measured TestClient times (JWT still verified on every request)**

| Request | `X-Cache` | Time |
| --- | --- | --- |
| `GET /suppliers` first | MISS | **6.7 ms** |
| `GET /suppliers` second | HIT | **3.2 ms** |
| `GET /inventory/products` first | MISS | **8.7 ms** |
| `GET /inventory/products` second | HIT | **4.1 ms** |

Hits are ~half of misses. The remaining HIT cost is **JWT + TinyDB `get_current_user`**, which is intentionally not cached. In-process SQLite is fast even at 1,280 orders; the win is skipping TinyDB file scans and SQL `SUM` aggregations on repeated backoffice reads, not pretending the local lab is a 400 ms production query.

---

## Endpoint assessment (all FastAPI routes)

Legend: **C** = computation/I/O cost, **F** = how often backoffice calls it, **S** = how stable the payload is.

| Endpoint | C | F | S | Cache? |
| --- | --- | --- | --- | --- |
| `GET /health` | Tiny | Probes | Static `"ok"` | No — cheaper than a cache lookup |
| `POST /api/incidents/analyze` | High (CSV parse) | Per upload | Unique per file | No — POST, input-dependent |
| `GET /api/incidents/results/export` | Medium | After analyze | Last upload in process | No — last-analysis, not a shared catalog |
| `GET /suppliers` | TinyDB open + filter | Every supplier page + filter change | Catalog; writes are rare vs reads | **Yes** — TTL 60s, key `country`/`category` only |
| `GET /suppliers/{id}` | Single doc | Rare | Same catalog | No — low frequency |
| `POST /suppliers`, `PATCH …/rate`, `PATCH …/status`, `DELETE …` | Write | Occasional | Changes data | No — invalidate `suppliers:` instead |
| `GET /inventory/products` | SQL products + grouped inbound/outbound sums | Stock page, outbound form, inbound flow | Stock changes on orders | **Yes** — TTL 30s; **writes invalidate**; outbound qty check is live SQL |
| `GET /inventory/products/{id}` | Per-SKU sums | Rare | Same stock | No — low frequency |
| `POST /inventory/products`, `POST /inventory/orders/inbound`, `POST /inventory/orders/outbound` | Write + live stock check | Per clinic movement | Mutates stock | No — invalidate `inventory:products` after commit |
| `GET /inventory/orders` | Two tables + per-row TinyDB email lookup | Order history | Grows on every movement; includes `created_by` | **No** — see “What was not cached” |
| `POST /auth/login`, forgot/reset/change-password | Crypto + TinyDB | Session events | Tokens | No |
| `GET /auth/me`, `GET /profiles/me`, `PUT /profiles/me` | TinyDB | Every protected page | **Per user** | **No** — session-specific |
| `POST /users`, `GET /users`, `GET/PUT/DELETE /users/{id}` | TinyDB | Admin/register | Staff identities | **No** — not a shared catalog |

Auth still runs **before** a cache read (`Depends(get_current_user)`). Unauthenticated callers never receive a cached body.

---

## Frontend decisions

### Lazy loading (two new `next/dynamic` splits)

**1. `IncidentAnalyzerPanel` on `/incidents`**

The incident analyzer is a client island: file input, drag-and-drop, `FormData` POST, breakdown cards, CSV export. None of that is needed to paint the server-rendered title and CONTEXT blurb. Deferring the chunk keeps the route header streaming while the analyzer JS loads. Fallback: “Loading incident analyzer…”.

**2. `SupplierDirectoryPanel` on `/suppliers`**

The directory is a large client module (filters, create form, editable rate table, status toggles). The procurement heading can paint without waiting on that bundle. Staff who never open `/suppliers` never download it from this page graph. Fallback: “Loading supplier directory…”.

`ssr` stays on (default) so the first client paint is not an empty hole beyond the loading status.

**Already in tree (not counted as new work):** `uis/healthcore` home lazy-loads `PatientSignupForm` below the fold. That form is unused until a visitor reaches the sign-up section; it is the same pattern and remains.

**Not lazy-loaded:** `Milestone2OpsPanel` on `/ops`. PLAN-046 kept denial / no-show / CME **headlines** in the first paint for Monday review. Splitting that panel would delay Tom/Marcus/Diane numbers for a Lighthouse-style JS saving that this assignment does not require.

### `useMemo` (non-trivial)

Typing a monthly rate in the supplier table re-renders the whole panel. Re-aggregating 200 vendors on every keystroke is wasted work.

`summarizeSupplierDirectory` (`uis/backoffice/lib/supplier-directory-metrics.ts`) walks the list once: active/suspended counts, USD vs GBP monthly totals, and overlapping category frequencies. `SupplierDirectoryPanel` memoizes it on `[suppliers]` only.

Second, justified the same way after load seed: `buildStockInsights` (`uis/backoffice/lib/inventory-stock-metrics.ts`) filters below-threshold SKUs, sorts by unit deficit, and sums units short. `ProductStockPanel` memoizes on `[products]`. Rate-draft typing on other pages does not apply here; inventory rows still re-render per product, but the sort/aggregate does not re-run unless the product list changes.

**Not memoized:** `PRODUCT_CATEGORIES` is a module constant (the previous `useMemo(() => PRODUCT_CATEGORIES, [])` was removed). `OutboundOrderForm`’s `products.find` for the selected SKU is a trivial scan.

---

## Backend decisions

In-process `TtlCache` (`app/core/ttl_cache.py`) — dictionary + `time.monotonic` expiry + prefix invalidation + a lock. No Redis: Compose today is `ui` + `api` only (`CONTEXT-MS5-container.md`); an extra cache service is out of scope.

Bodies stored as JSON-mode dicts (`model_dump(mode="json")`), rebuilt with Pydantic on HIT. `X-Cache: MISS|HIT` is for tests and timing, not for clients to branch on.

### `GET /suppliers`

| Axis | Decision |
| --- | --- |
| Cost | TinyDB open + full-table filter on every listing (and again when country/category changes). |
| Frequency | Supplier page load + every filter change from backoffice. |
| Stability | Named vendors (McKesson, Epic, …) plus load vendors. Rates/status change when Digital staff patch a row — not on a per-request basis. |
| TTL | **60 seconds** |
| Key | `suppliers:list:{country or *}:{category or *}` — **no user id**. Payload is the same directory for every JWT. |
| Invalidation | `invalidate_suppliers()` after successful create, rate patch, status patch, or delete. Failed 404 writes do not clear the cache. |

### `GET /inventory/products`

| Axis | Decision |
| --- | --- |
| Cost | `list_supplies` loads every SKU then `stock_map` (grouped `SUM` inbound − outbound). Cost grows with order history. |
| Frequency | `/inventory`, outbound product dropdown, inbound flow after redirect. |
| Stability | Stock is hotter than vendor rates, but many consecutive GETs between orders are identical. |
| TTL | **30 seconds** |
| Key | `inventory:products` — shared catalog + computed `current_stock`. No email, no `user_uuid`. |
| Invalidation | After successful product create, inbound commit, or outbound commit. |
| Safety | `POST /inventory/orders/outbound` calls **live** `current_stock_for` (SQL), never the cached listing. A stale HIT cannot over-issue. Pytest locks this with a forged 9999-stock cache entry that still returns `Available: 12`. |

---

## Tradeoffs acknowledged (freshness vs performance)

**Chosen staleness:** supplier listings may be up to **60s** old if a write in another process does not hit this API worker; inventory listings may be up to **30s** old in that same failure mode.

That is acceptable because:

1. **Normal Digital use invalidates immediately** on the write path in this process. TTL is a safety net, not the primary consistency mechanism.
2. **Supplier monthly rates** are procurement browsing numbers, not a bank balance. A colleague seeing last minute’s rate for under a minute does not change a clinic fill.
3. **Stock listings** can lag by at most 30s if invalidation is missed, but **issue control is not the listing**. Outbound still computes available quantity from SQL at submit time. Clinics cannot ship from a stale cache.
4. **Shorter TTLs** (e.g. 2s) would almost always miss under TestClient and still pay TinyDB/SQL on every poll. Longer TTLs (e.g. 10 minutes) without relying on invalidation would be wrong for stock.

In-process cache is **per uvicorn worker**. Two workers can disagree until TTL or a write on that worker. Redis would fix that; it is not in the MS5 Compose contract, so the tradeoff is documented rather than papered over.

---

## What was not cached, and why

**`GET /inventory/orders`** was the next-best performance candidate (joins + TinyDB `creator_email` per row) and was rejected.

- The JSON includes **`created_by` staff email** and `user_uuid`. Even though every Digital user sees the same history table, that is attribution data, not a public catalog. A shared key here is the leak pattern the assignment forbids if we ever vary the list by requester.
- Frequency of **writes** is the same as inbound/outbound. A 30s TTL would fight the invalidation storm; caching then clearing on every movement is close to no cache.
- Detail `GET /auth/me` was never a candidate: email, role, and profile are **session-specific**. Caching that under a shared key would leak one staff identity to another.

**`GET /health`** is a literal `status: ok` — not worth a TTL.

---

## Files

| Path | Role |
| --- | --- |
| `services/api/app/core/ttl_cache.py` | TTL dictionary |
| `services/api/app/core/response_cache.py` | Keys, TTLs, HIT/MISS helpers |
| `services/api/app/main.py` | Timing middleware |
| `services/api/app/routers/suppliers.py` | List cache + write invalidation |
| `services/api/app/routers/inventory.py` | Product-list cache + live outbound stock |
| `services/api/app/load_seed.py` / `seed_load.py` | Load dataset |
| `services/api/profile_cache.py` | Miss vs hit timings |
| `services/api/tests/test_cache.py` | HIT/MISS, filters, TTL, invalidation, auth, stale-stock safety |
| `uis/backoffice/app/(internal)/incidents/page.tsx` | Dynamic incident panel |
| `uis/backoffice/app/(internal)/suppliers/page.tsx` | Dynamic supplier panel |
| `uis/backoffice/lib/supplier-directory-metrics.ts` | Memoized directory aggregate |
| `uis/backoffice/lib/inventory-stock-metrics.ts` | Memoized low-stock ranking |
