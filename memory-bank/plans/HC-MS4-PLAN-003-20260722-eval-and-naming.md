---
stamp: HC-MS4-PLAN-003
sequence: 3
milestone: MS4
date: 2026-07-22
title: MS4 Evaluation Archive and Milestone Plan Naming
status: implemented
phase: post-milestone
summary: Added memory-bank/evaluations with MS4_Project_Eval, always-on milestone evaluation rule, and required MS{N} token in new plan stamp filenames.
related_paths:
  - memory-bank/evaluations/
  - memory-bank/evaluations/MS4_Project_Eval.md
  - memory-bank/plans/README.md
  - AGENTS.md
  - .agents/rules/healthcore-milestone-evaluation.md
  - .agents/rules/healthcore-plan-archive.md
do_not_repeat:
  - Recreate memory-bank/evaluations from scratch if INDEX and MS4_Project_Eval already exist
  - Remove the MS{N} token from new plan stamp filenames
  - Skip milestone evaluations when closing future milestones
  - Rename or rewrite legacy HC-PLAN-001 / HC-PLAN-002 stamps
---

# HC-MS4-PLAN-003 — MS4 Evaluation Archive and Milestone Plan Naming

## Decisions locked

- Milestone evaluations live under `memory-bank/evaluations/` as `MS{N}_Project_Eval.md`.
- Every milestone from MS4 onward must record an evaluation when scoped work is complete.
- New plan stamps must be named `HC-MS{N}-PLAN-{NNN}-{YYYYMMDD}-{slug}.md`.
- Legacy `HC-PLAN-001` / `HC-PLAN-002` remain MS4 history and stay append-only / unrenamed.

## Files created or updated

- `memory-bank/evaluations/README.md`
- `memory-bank/evaluations/INDEX.md`
- `memory-bank/evaluations/MS4_Project_Eval.md`
- `.agents/rules/healthcore-milestone-evaluation.md`
- Updated `AGENTS.md`, `memory-bank/plans/README.md`, `.agents/rules/healthcore-plan-archive.md`

## Agent instructions

1. For new stamps, always include the milestone token (`MS4`, `MS5`, …) in the filename.
2. When a milestone completes, write `MS{N}_Project_Eval.md` before calling the milestone done in `progress.md`.
3. Read the relevant milestone eval at session start when the user names that milestone.
4. Do not rewrite this stamp or `MS4_Project_Eval.md` without human confirmation; append new stamps/evals instead.
