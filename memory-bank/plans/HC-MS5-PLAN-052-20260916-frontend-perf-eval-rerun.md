---
stamp: HC-MS5-PLAN-052
sequence: 52
milestone: MS5
date: 20260916
title: Close Frontend Performance Rubric Fails And Re-evaluate
status: implemented
phase: implementation
summary: Skill-guided public webfont/code-split and backoffice useAuthToken hydration fix. Lighthouse CLI desktop scores committed as PNG + scores.json. Session eval overwritten to 7/7 Pass.
related_paths:
  - uis/backoffice/hooks/useAuthToken.ts
  - uis/backoffice/components/auth/SessionActions.tsx
  - uis/healthcore/app/layout.tsx
  - uis/healthcore/app/globals.css
  - uis/healthcore/app/page.tsx
  - uis/healthcore/next.config.ts
  - docs/audit.md
  - docs/report.md
  - docs/EVALUATION.md
  - docs/lighthouse/scores.json
  - docs/lighthouse/healthcore-home-before.png
  - docs/lighthouse/healthcore-home-after.png
  - docs/lighthouse/backoffice-login-after.png
  - memory-bank/evaluations/INDEX.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Restore Source_Sans_3 on the public root layout
  - Read localStorage during SessionActions SSR
  - Invent Lighthouse after-scores
---

# HC-MS5-PLAN-052 — Close Frontend Performance Rubric Fails And Re-evaluate

## Decisions locked

- Canonical session eval remains [`docs/EVALUATION.md`](../../docs/EVALUATION.md) (**7/7 Pass** after this re-run).
- Lab evidence lives under [`docs/lighthouse/`](../../docs/lighthouse/).
- Skills used: core-web-vitals, performance, web-perf, healthcore-web-performance.

## Agent instructions

1. Same-day re-evals overwrite `docs/EVALUATION.md` only.
2. Do not restore Geist / Source_Sans_3 on these apps without a measured reason.
3. Append a new stamp for later work; do not rewrite this file.
