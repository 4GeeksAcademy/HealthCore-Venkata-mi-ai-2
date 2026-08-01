---
stamp: HC-MS4-PLAN-008
sequence: 8
milestone: MS4
date: 20260731
title: Architecture Proposal Project Cleanup
status: implemented
phase: docs
summary: Cleaned docs/ARCHITECTURE_PROPOSAL.md for HealthCore-only fit—linked src/utils and UI ports, locked backoffice session/cookie auth, clarified public site does not call ops/hiring APIs, removed vendor fluff, shortened summary; single progress today’s entry refreshed.
related_paths:
  - docs/ARCHITECTURE_PROPOSAL.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Add a second “Today’s update” block for 2026-07-31 in progress.md
  - Reintroduce bearer-vs-cookie optionality or public ops API consumers without human confirmation
---

# HC-MS4-PLAN-008 — Architecture Proposal Project Cleanup

## Decisions locked

- No `[Insert …]` placeholders; all company/domain facts from project brief.
- Auth: session/cookie for `uis/backoffice` staff only; no public patient auth API.
- `uis/healthcore` does not consume ops/hiring FastAPI routes.
- Progress.md keeps one consolidated 2026-07-31 update; PLAN-008 is latest.

## Agent instructions

1. On further proposal edits before sign-off, revise the single today’s progress entry—do not add another day’s section for the same date.
2. Append new stamps; do not rewrite PLAN-006/007/008.
3. Do not scaffold FastAPI unless the user explicitly requests implementation.
