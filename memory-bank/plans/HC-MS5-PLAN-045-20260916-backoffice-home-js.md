---
stamp: HC-MS5-PLAN-045
sequence: 45
milestone: MS5
date: 20260916
title: Backoffice Home Reduce Client JS For Lighthouse
status: implemented
phase: implementation
summary: Home now server-renders a slim Monday ops snapshot (same src/utils numbers) instead of shipping Milestone2OpsPanel to the client. Removed Geist webfont (system fonts). AuthGuard still calls fetchAuthMe via a deferred import. Full ops panel remains on /ops.
related_paths:
  - uis/backoffice/app/page.tsx
  - uis/backoffice/app/layout.tsx
  - uis/backoffice/app/globals.css
  - uis/backoffice/components/ops/HomeOpsSummary.tsx
  - uis/backoffice/components/auth/AuthGuard.tsx
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Load Milestone2OpsPanel on the client for the welcome page
  - Restore next/font Geist on every backoffice request
  - Skip fetchAuthMe on protected routes
  - Remove Monday ops numbers from home
---

# HC-MS5-PLAN-045 — Backoffice Home Reduce Client JS For Lighthouse

## Decisions locked

- Welcome page uses server-only `HomeOpsSummary` (denial %, Miami no-show cost, CME at-risk count) from `buildMilestone2OpsSnapshot`.
- Full `Milestone2OpsPanel` stays on `/ops`.
- Backoffice uses system fonts (`Segoe UI` / `system-ui`), not Geist.
- `fetchAuthMe` still runs on protected routes; the auth-api module is imported inside the effect.

## Agent instructions

1. Do not put `Milestone2OpsPanel` on the home client bundle.
2. Keep snapshot metrics on home; keep the detailed panel on `/ops`.
3. Keep JWT + `/auth/me` on protected routes.
4. Lighthouse on `next dev` in Docker will still be below a production `next start` score.
5. Append a new stamp for later work; do not rewrite this file.
