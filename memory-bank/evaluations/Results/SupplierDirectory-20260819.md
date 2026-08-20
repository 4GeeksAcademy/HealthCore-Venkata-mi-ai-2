# Supplier Directory TinyDB — Domain Fix Evaluation

**Date:** 2026-08-19  
**CONTEXT:** [`docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`](../../../docs/Project_Contexts/SupplierDirectory_TinyDb_API.md)  
**Stamp:** HC-MS4-PLAN-016  
**Scope:** Teacher rejection only (domain). Structure from PLAN-015 is unchanged.  
**Overall: PASS** (domain checks)

Does **not** rewrite [`SupplierDirectory-20260810.md`](./SupplierDirectory-20260810.md) (prior structure eval).

## Method

- Seeder: `python seed.py` twice under `services/api`
- API: FastAPI `TestClient` against `app.main:app`
- Frontend: static review of `uis/backoffice` suppliers types/panel (labels + payload fields)
- `npm run lint` / `npx tsc --noEmit` in `uis/backoffice` skipped this session (npm registry TLS `UNABLE_TO_VERIFY_LEAF_SIGNATURE`)

## Domain (rejected items)

| Criterion | Result | Evidence |
|-----------|--------|----------|
| `monthly_rate` not `contract_rate` | **Pass** | Create/response/PATCH body use `monthly_rate`; `monthly_rate: 0` → 422 |
| `country` `USA` / `UK` not `US` / `UK` | **Pass** | Seed countries only USA/UK; POST `country: "US"` → 422 |
| `currency` pairing | **Pass** | USA→USD, UK→GBP on all 15 seeds; POST USA+GBP → 422 |
| `categories` field | **Pass** | List/filter/create use `categories`; existing category enum unchanged |
| 15 seeds incl. McKesson and Epic | **Pass** | Fresh-or-legacy seed `Inserted 15 supplier(s).`; re-run `Inserted 0`; names include McKesson and Epic |

## Structure (unchanged — still Pass)

| Criterion | Result | Evidence |
|-----------|--------|----------|
| Idempotent seed | **Pass** | Second run `Inserted 0 supplier(s).` |
| GET filters AND | **Pass** | `country=USA`, `category=IT_EQUIPMENT`, both |
| PATCH rate / 404 / 422 | **Pass** | `monthly_rate` 16.0 → 200; missing id → 404; 0 → 422 |
| POST 201 | **Pass** | Create returns id + system `updated_at` |
| Incidents routes | **Pass** | `/api/incidents/analyze` in OpenAPI |
| Backoffice wiring | **Pass** | `/suppliers` panel still filters, creates, patches rate/status; currency shown next to rate |

## Verdict

Teacher rejection addressed: official HealthCore supplier domain (`monthly_rate`, currency pairing, USA/UK, 15 syllabus-style suppliers). Previously accepted API/UI structure left in place.
