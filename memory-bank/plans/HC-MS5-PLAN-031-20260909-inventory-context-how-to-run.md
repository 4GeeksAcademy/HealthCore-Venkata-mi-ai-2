---
stamp: HC-MS5-PLAN-031
sequence: 31
milestone: MS5
date: 20260909
title: MS5 Inventory CONTEXT How to Run
status: implemented
phase: docs
summary: Expanded How to run in CONTEXT-MS5-inventory-backoffice.md with API seed/JWT, backoffice inventory URLs, tests, and public-site isolation. Docs only.
related_paths:
  - docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as new inventory UI or API routes
  - Rewrite PLAN-028, PLAN-029, or PLAN-030
  - Commit .env or live TinyDB JSON as part of documenting run steps
---

# HC-MS5-PLAN-031 — MS5 Inventory CONTEXT How to Run

## Decisions locked

- How-to-run lives in `docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md` (not root `CONTEXT.md`).
- API: `JWT_SECRET_KEY`, `python seed.py`, uvicorn `:8001`.
- Backoffice: `npm run dev` on `:3001` (`/inventory`, `/inbound`, `/outbound`, `/orders`).
- Tests: root pytest; backoffice lint / tsc / Jest.
- Public site remains on `:3000` with no inventory and no auth.

## Agent instructions

1. Do not treat this stamp as a second inventory implementation.
2. When telling operators how to run MS5, use the How to run section in CONTEXT-MS5.
3. Do not rewrite prior MS5 stamps.
4. Never commit `.env` or `services/api/data/inventory.json`.
