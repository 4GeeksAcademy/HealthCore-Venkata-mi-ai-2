---
stamp: HC-MS4-PLAN-004
sequence: 4
milestone: MS4
date: 2026-07-22
title: MS4 Eval Rubric Mapping Correction
status: implemented
phase: post-milestone
summary: Locked official-rubric mapping so uis/website equals uis/healthcore and Milestone 2 backoffice integration equals talent-pipeline-tracker migration; MS4_Project_Eval marked complete PASS 8/8.
related_paths:
  - memory-bank/evaluations/MS4_Project_Eval.md
  - memory-bank/evaluations/INDEX.md
  - memory-bank/progress.md
do_not_repeat:
  - Re-fail MS4 for missing uis/website folder name
  - Re-fail MS4 for missing src/utils ops dashboards in backoffice
  - Reopen MS4 as incomplete against the generic rubric wording without human confirmation
---

# HC-MS4-PLAN-004 — MS4 Eval Rubric Mapping Correction

## Decisions locked

- Rubric `./uis/website` → repo path `./uis/healthcore`.
- Rubric “Milestone 2 TypeScript in backoffice” → migrated `talent-pipeline-tracker` visible in `uis/backoffice` (`/` + `/hiring`).
- MS4 official scorecard is **8/8 Pass**; status **complete**.

## Agent instructions

1. When evaluating this repo against generic MS4 rubric text, always apply the mapping in `MS4_Project_Eval.md`.
2. Do not change MS4 to fail for `website` naming or `src/utils/` UI unless a human explicitly changes that mapping.
3. Append new stamps for new work; do not rewrite this stamp.
