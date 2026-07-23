---
stamp: HC-MS4-PLAN-005
sequence: 5
milestone: MS4
date: 2026-07-22
title: MS2 src/utils Ops Visible in Backoffice
status: implemented
phase: post-milestone
summary: Integrated Milestone 2 src/utils TypeScript into uis/backoffice with visible metrics on / and /ops; corrected MS4 eval mapping (MS2 is not the hiring tracker).
related_paths:
  - uis/backoffice/lib/milestone2-metrics.ts
  - uis/backoffice/lib/sample-ops-data.ts
  - uis/backoffice/components/ops/Milestone2OpsPanel.tsx
  - uis/backoffice/app/ops/page.tsx
  - uis/backoffice/app/page.tsx
  - uis/backoffice/next.config.ts
  - memory-bank/evaluations/MS4_Project_Eval.md
do_not_repeat:
  - Map Milestone 2 rubric item to talent-pipeline-tracker / hiring module
  - Remove Milestone2OpsPanel from backoffice home or /ops without human confirmation
  - Re-fail MS4 for missing literal uis/website folder
---

# HC-MS4-PLAN-005 — MS2 src/utils Ops Visible in Backoffice

## Decisions locked

- Milestone 2 for MS4 rubric = repo root `src/utils` (Node/TypeScript ops utilities).
- Visible output required: denial rate, no-show metrics, CME statuses on backoffice `/` and `/ops`.
- Hiring tracker is separate and does not satisfy rubric item #8.

## Agent instructions

1. Keep `@hc` alias pointing at repo `src/` for backoffice imports.
2. Keep MS4 eval mapping: website→healthcore; MS2→src/utils in backoffice UI.
3. Append new stamps for further work; do not rewrite this stamp.
