---
stamp: HC-MS5-PLAN-044
sequence: 44
milestone: MS5
date: 20260916
title: Backoffice Home Lighthouse Performance
status: implemented
phase: implementation
summary: Unblocked authenticated home first paint — AuthGuard still calls fetchAuthMe but no longer replaces the page with Loading session. Home defers Milestone2OpsPanel (dynamic, ssr false) and disables nav prefetch so LCP is the welcome heading. Ops remain on /ops and still appear on home after load.
related_paths:
  - uis/backoffice/components/auth/AuthGuard.tsx
  - uis/backoffice/components/auth/BackofficeShell.tsx
  - uis/backoffice/components/ops/Milestone2OpsPanel.tsx
  - uis/backoffice/app/page.tsx
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Block home HTML behind Loading session while waiting for /auth/me
  - Statically import Milestone2OpsPanel on the welcome page
  - Skip fetchAuthMe on protected routes
  - Remove Monday ops from the home page entirely
---

# HC-MS5-PLAN-044 — Backoffice Home Lighthouse Performance

## Decisions locked

- Protected routes still call `fetchAuthMe`; a 401 still goes to `/login?reason=session`. Missing token still redirects.
- AuthGuard no longer swaps the tree for “Loading session” on `/` — first paint is the welcome page.
- Home loads `Milestone2OpsPanel` with `next/dynamic` and `ssr: false` so Milestone 2 JS is not in the critical path. `/ops` still imports the panel directly.
- Backoffice nav links use `prefetch={false}` to avoid pulling incidents/suppliers/inventory/hiring JS on home.

## Agent instructions

1. Do not restore a full-page Loading session gate on authenticated home.
2. Keep `fetchAuthMe` on protected routes; do not drop JWT checks.
3. Keep Monday ops visible on home after the deferred panel loads; keep the full panel on `/ops`.
4. Re-run Lighthouse on http://localhost:3001/ after login, with Next Ready. `next dev` still caps the score versus production.
5. Append a new stamp for later work; do not rewrite this file.
