---
stamp: HC-MS5-PLAN-032
sequence: 32
milestone: MS5
date: 20260909
title: Project Env Ignore Note and MS5 Re-run Evaluation
status: implemented
phase: docs
summary: Added project-level never-commit-.env policy in README.md and AGENTS.md. Re-ran MS5 tests (pytest 43, Jest 15, lint/tsc) and appended 8/8 Pass re-eval. No inventory product-code changes.
related_paths:
  - README.md
  - AGENTS.md
  - .gitignore
  - memory-bank/evaluations/MS5_Project_Eval.md
  - memory-bank/evaluations/Results/InventoryBackoffice-20260909.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Commit .env, .env.local, or .env.example
  - Rewrite PLAN-028–031 or replace the original MS5 scorecard
  - Point pytest at live data/inventory.json
---

# HC-MS5-PLAN-032 — Project Env Ignore Note and MS5 Re-run Evaluation

## Decisions locked

- Project-level rule: never commit `.env`, `.env.local`, `.env.example`, or `env.example`.
- Rule lives in root `README.md` and `AGENTS.md` (pre-commit + isolation reminders).
- `.gitignore` already ignores those paths; `services/api/.env.example` is untracked.
- MS5 re-run: 43 pytest, 15 Jest, lint/tsc pass, live health 200. Rubric still 8/8 Pass.

## Agent instructions

1. Never stage or commit `.env` files. Confirm `git check-ignore` before commits that touch env paths.
2. Do not rewrite the original MS5 8/8 scorecard; append re-runs only.
3. Keep inventory HTTP in `lib/inventory-api.ts`.
4. Append new stamps for later work; do not rewrite this stamp.
