---
stamp: HC-MS4-PLAN-017
sequence: 17
milestone: MS4
date: 20260826
title: Authentication Master Framework Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/auth_master_framework_Context.md — assignment CONTEXT locking AUTH-01/02/03 as sequential tasks on one JWT + TinyDB identity contract (User vs Profile, backoffice-only UI, public site untouched). Docs only; no auth API or login UI code.
related_paths:
  - docs/Project_Contexts/auth_master_framework_Context.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Create docs/Plans/ for this work
  - Place auth_master_framework_Context.md directly under docs/
  - Treat this stamp as implemented JWT, TinyDB users, or backoffice login
  - Rewrite root CONTEXT.md for authentication
  - Implement cookie/session auth from ARCHITECTURE_PROPOSAL.md
---

# HC-MS4-PLAN-017 — Authentication Master Framework Context Document

## Decisions locked

- Context file path: `docs/Project_Contexts/auth_master_framework_Context.md` (not `docs/` root).
- Plan archive: `memory-bank/plans/` only — no `docs/Plans/`.
- Root `CONTEXT.md` / `CONTEXT_temp.md` unchanged.
- AUTH-01, AUTH-02, AUTH-03 remain separate graded tasks; one shared identity contract.
- Stateless JWT Bearer only (overrides cookie/session note in `docs/ARCHITECTURE_PROPOSAL.md`).
- User/Profile/reset tokens in TinyDB `services/api/data/auth.json` only.
- Route prefixes `/auth`, `/users`, `/profiles`.
- Backoffice-only auth UI; `uis/healthcore` stays public.
- Docs only — no auth routers, no login pages, no email integration in this stamp.

## Agent instructions

1. Do not create `docs/Plans/`.
2. Do not place `auth_master_framework_Context.md` directly under `docs/`.
3. Do not treat this stamp as implemented auth code (JWT, TinyDB users, backoffice `/login`, Resend).
4. Do not rewrite root `CONTEXT.md` for authentication; use `docs/Project_Contexts/auth_master_framework_Context.md`.
5. Implementation must follow that CONTEXT: three sequential tasks, JWT + TinyDB, protect all eight supplier + incident routes, public site untouched.
6. Append new stamps for AUTH-01 / AUTH-02 / AUTH-03 implementation; do not rewrite this stamp.
