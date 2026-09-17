---
stamp: HC-MS5-PLAN-046
sequence: 46
milestone: MS5
date: 20260916
title: Milestone 2 Ops Dashboard Lighthouse Performance
status: implemented
phase: implementation
summary: Split backoffice into (auth)/(internal) route groups so /ops nav is server-rendered. Slimmed Milestone2OpsPanel (headline metrics visible; detail lists in details/summary; content-visibility). URLs unchanged. Full src/utils metrics still on /ops.
related_paths:
  - uis/backoffice/app/layout.tsx
  - uis/backoffice/app/(internal)/layout.tsx
  - uis/backoffice/app/(auth)/layout.tsx
  - uis/backoffice/app/(internal)/ops/page.tsx
  - uis/backoffice/components/ops/Milestone2OpsPanel.tsx
  - uis/backoffice/app/globals.css
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Wrap /ops in a client BackofficeShell that re-renders the whole nav
  - Expand every payer/location/CME list on first paint
  - Remove Monday ops metrics from /ops
  - Skip fetchAuthMe on protected routes
---

# HC-MS5-PLAN-046 — Milestone 2 Ops Dashboard Lighthouse Performance

## Decisions locked

- Internal chrome lives in `app/(internal)/layout.tsx` (server Links + client `SessionActions` + `AuthGuard`).
- Auth pages live under `app/(auth)/` with no top nav. URLs stay `/ops`, `/login`, etc.
- `/ops` still uses `Milestone2OpsPanel` and `buildMilestone2OpsSnapshot` (`src/utils`). Headline numbers stay visible; long lists are in `<details>`.
- `BackofficeShell` removed.

## Agent instructions

1. Keep `/ops` as the full Milestone 2 dashboard with `src/utils` numbers.
2. Do not move nav markup back into a client shell that wraps the ops page.
3. Keep JWT + `fetchAuthMe` on internal routes.
4. Re-run Lighthouse on http://localhost:3001/ops after a hard refresh. `next dev` still limits the ceiling.
5. Append a new stamp for later work; do not rewrite this file.
