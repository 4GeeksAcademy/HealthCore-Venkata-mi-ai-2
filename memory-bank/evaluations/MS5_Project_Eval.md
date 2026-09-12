---
milestone: MS5
title: Milestone 5 Project Evaluation
date: 2026-09-09
status: complete
related_plans:
  - HC-MS5-PLAN-028-20260909-inventory-backoffice-context.md
  - HC-MS5-PLAN-029-20260909-inventory-context-eval-samples.md
  - HC-MS5-PLAN-030-20260909-inventory-backoffice-impl.md
summary: MS5 passes the inventory backoffice rubric — four authenticated views consume live /inventory data, with color-coded stock, outbound available-stock display, readable 400s, and empty states.
---

# MS5 — Project Evaluation

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Owner:** James Osei, CTO  

Checked against the official **“What We Will Evaluate”** list in [`docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md`](../../docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md). Task-level evidence: [Results/InventoryBackoffice-20260909.md](./Results/InventoryBackoffice-20260909.md).

---

## Rubric mapping (authoritative — do not re-fail)

| Rubric wording | HealthCore meaning | Do **not** reinterpret as |
|----------------|--------------------|---------------------------|
| Inventory backoffice views | **`uis/backoffice`** `/inventory`, `/inventory/inbound`, `/inventory/outbound`, `/inventory/orders` | A public page on `uis/healthcore` |
| Live inventory API | FastAPI `/inventory/*` on `:8001` with JWT | Hiring playground `lib/api-client.ts` |
| Auth redirect | Existing client `AuthGuard` → `/login` | New cookie/middleware auth |

---

## Official rubric scorecard

| # | Criterion | Rating | Evidence |
|---|-----------|--------|----------|
| 1 | Centralized API integration module | **Pass** | `uis/backoffice/lib/inventory-api.ts` |
| 2 | Product page stock + low-stock visual | **Pass** | `/inventory` + `stock-low` / `stock-ok` |
| 3 | Inbound form confirmation or error | **Pass** | Redirect `?notice=inbound`; form errors visible |
| 4 | Outbound shows available stock before quantity | **Pass** | Status line above quantity input |
| 5 | Insufficient-stock 400 readable in UI | **Pass** | Allowlisted `detail` string, not raw JSON |
| 6 | Order history columns (name, type, qty, date, creator) | **Pass** | `/inventory/orders` |
| 7 | Empty arrays → empty state | **Pass** | `AsyncState` empty copy; API `[]` |
| 8 | Four pages authenticated; else `/login` | **Pass** | `AuthGuard` + protected API routes |

**Rubric tally:** 8 / 8 Pass  

**Milestone verdict:** **COMPLETE — PASS**

---

## 1. Objectives

| ID | Rubric item | Repo target |
|----|-------------|-------------|
| I1 | One inventory client | `lib/inventory-api.ts` + `authedFetch` |
| I2–I4 | Stock / inbound / outbound views | `uis/backoffice/app/inventory/**` |
| I5 | Readable 400 | `user-facing-error` + outbound form |
| I6–I7 | History + empty states | `/inventory/orders` + `AsyncState` |
| I8 | Auth | Existing `AuthGuard`; API `get_current_user` |

---

## 2. Delivered

- CONTEXT + samples (PLAN-028, PLAN-029)
- TinyDB inventory API (`GET /inventory/products`, `POST /inventory/inbound`, `POST /inventory/outbound`, `GET /inventory/orders`)
- Seeded clinic-supply products (gloves low, pads OK)
- Four backoffice views + nav link
- Pytest (7 inventory cases) and Jest (low-stock + 400 message)

---

## 3. Verification

| Check | Result |
|-------|--------|
| `python -m pytest` | 43 passed |
| `uis/backoffice` lint / `tsc --noEmit` | Pass |
| `uis/backoffice` Jest | 15 passed |
| Live `/inventory/products` without token | 401 |
| Public site inventory UI | None (unchanged) |

---

## 4. Gaps / deferred (non-blocking)

- In-browser click-through was not run (no browser automation in this session).
- Raw clients without a Bearer header see FastAPI `Not authenticated`; the backoffice redirects before calling the API.

---

## 5. Agent instructions

1. Treat MS5 as **complete — PASS** for the inventory backoffice rubric above.
2. **Never** fail MS5 for missing inventory on `uis/healthcore`.
3. Do not remove outbound available-stock display or readable 400 handling without human confirmation.
4. Keep inventory HTTP centralized; do not hang it on `lib/api-client.ts`.
5. New work after MS5 needs a new stamp (`HC-MS{N}-PLAN-{NNN}-...`) and must not rewrite this eval.
6. Never commit `.env` files.

---

## Re-run verification (2026-09-09 evening)

Re-tested after the project-level env-file policy note (`README.md`, `AGENTS.md`).

| Check | Result |
|-------|--------|
| `python -m pytest` | 43 passed |
| Backoffice lint / `tsc --noEmit` | Pass |
| Backoffice Jest | 15 passed |
| Live API `/health` and backoffice `:3001` | 200 |

**Rubric tally (re-run):** 8 / 8 Pass. Verdict remains **COMPLETE — PASS**.

---

## Re-run (2026-09-11) — ORM-first alignment

The UI now consumes the dual-database API that should have shipped first. Paths: `POST /inventory/orders/inbound|outbound`. Wire `current_stock` maps to displayed stock. Order history shows TinyDB `created_by` email; SQLModel still stores `user_uuid`.

| Check | Result |
|-------|--------|
| `python -m pytest` | **46 passed** (10 inventory) |
| Backoffice lint / `tsc --noEmit` | Pass (coverage-report warning only) |
| Backoffice Jest | **18 passed** (mapper `current_stock` / `created_by`) |
| Central client | `lib/inventory-api.ts` → `/inventory/orders/*` |
| Creator column | TinyDB email, not numeric `user_uuid` |
| Public site inventory UI | None |

Official eight-item rubric: **8 / 8 Pass**. Verdict remains **COMPLETE — PASS**. Live inventory store is SQLModel/Supabase, not TinyDB `inventory.json`.
