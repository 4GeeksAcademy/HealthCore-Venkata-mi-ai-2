---
stamp: HC-MS4-PLAN-023
sequence: 23
milestone: MS4
date: 20260828
title: Error Handling Requirement Skills and Context Split
status: implemented
phase: docs
summary: Saved ErrorHandling Requirement.txt as Cursor skills plus shared policy/taxonomy context under .cursor/skills/, keeping HealthCore repo notes (UI isolation, FastAPI paths, PHI-safe reporting, demo auth). Docs only; no application error-handling code changes.
related_paths:
  - .cursor/skills/error-handling-audit/SKILL.md
  - .cursor/skills/error-handling-audit/policy.context.md
  - .cursor/skills/error-handling-audit/findings-taxonomy.context.md
  - .cursor/skills/error-handling-frontend/SKILL.md
  - .cursor/skills/error-handling-backend/SKILL.md
  - .cursor/skills/error-handling-scripts/SKILL.md
  - memory-bank/plans/INDEX.md
  - memory-bank/progress.md
do_not_repeat:
  - Rewrite root CONTEXT.md for error handling
  - Treat this stamp as implemented error-handling code in uis/ or services/api
  - Add unrelated features while applying the error-handling skills
  - Re-split ErrorHandling Requirement.txt into a different skill layout without a new stamp
---

# HC-MS4-PLAN-023 — Error Handling Requirement Skills and Context Split

## Decisions locked

- Requirement source is ErrorHandling Requirement.txt, split into four skills and two shared context files.
- Shared context lives beside the audit skill: `policy.context.md` and `findings-taxonomy.context.md`.
- Frontend, backend, and scripts skills link one level to those context files.
- HealthCore repo notes (public vs backoffice isolation, `services/api`, synthetic IDs, demo auth / generic forgot-password) stay in labeled sections; they do not replace the requirement text.
- This stamp is documentation/agent skills only — no UI, API, or script error-handling implementation.

## Agent instructions

1. Use `.cursor/skills/error-handling-audit/` to scan the entire repository and report findings before applying error-handling code changes.
2. Use the frontend, backend, or scripts skill when implementing layer-specific fixes; read policy and taxonomy first.
3. Do not treat this stamp as completed error-handling work in `uis/` or `services/api`.
4. Do not rewrite root `CONTEXT.md` for error handling.
5. Do not introduce features or refactors unrelated to error handling when those skills are applied.
6. Keep public (`uis/healthcore`) and backoffice (`uis/backoffice`) layouts isolated while applying frontend error handling.
