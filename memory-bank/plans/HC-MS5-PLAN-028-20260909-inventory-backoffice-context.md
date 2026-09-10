---
stamp: HC-MS5-PLAN-028
sequence: 28
milestone: MS5
date: 20260909
title: MS5 Inventory Backoffice Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md — assignment CONTEXT locking four authenticated inventory views (stock, inbound, outbound with live available stock, order history), reuse of AUTH-02 JWT + AuthGuard, and readable 400 handling. Docs only; no inventory UI or API code.
related_paths:
  - docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Place CONTEXT-MS5-inventory-backoffice.md directly under docs/
  - Treat this stamp as implemented inventory pages or inventory API routes
  - Invent a second auth pattern (cookies, middleware, or hiring api-client)
  - Rewrite root CONTEXT.md for inventory
  - Add inventory UI to uis/healthcore
---

# HC-MS5-PLAN-028 — MS5 Inventory Backoffice Context Document

## Decisions locked

- Context file path: `docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md` (not `docs/` root, not root `CONTEXT.md`).
- Identity contract remains [`auth_master_framework_Context.md`](../../docs/Project_Contexts/auth_master_framework_Context.md): JWT Bearer, `localStorage`, client `AuthGuard`, 401 → `/login`.
- Company framing remains [`CONTEXT-healthcore-briefing.en.md`](../../docs/Project_Contexts/CONTEXT-healthcore-briefing.en.md).
- Existing module patterns: Supplier Directory and Incident File Analyzer CONTEXTs.
- Four views: product stock (color-coded vs threshold), inbound form, outbound form with available stock before submit, read-only order history.
- 400 responses must show a readable extracted message, never raw JSON.
- Confirm live `/inventory` OpenAPI before implementing payloads.
- Docs only — no inventory pages, no inventory API module, no `.env.local` in this stamp.

## Agent instructions

1. Do not place `CONTEXT-MS5-inventory-backoffice.md` directly under `docs/`.
2. Do not treat this stamp as implemented inventory UI or backend inventory routes.
3. Do not invent cookies, Next.js middleware auth, or hang inventory calls on `lib/api-client.ts`.
4. Do not rewrite root `CONTEXT.md` for inventory; use `docs/Project_Contexts/CONTEXT-MS5-inventory-backoffice.md`.
5. Implementation must follow that CONTEXT: four protected backoffice views, one inventory API module, outbound available-stock display, readable 400s, public site untouched.
6. Append a new stamp for inventory UI implementation; do not rewrite this stamp.
