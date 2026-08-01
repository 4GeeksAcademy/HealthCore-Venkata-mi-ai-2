---
stamp: HC-MS4-PLAN-006
sequence: 6
milestone: MS4
date: 20260731
title: FastAPI Architecture Proposal Document
status: implemented
phase: docs
summary: Authored docs/ARCHITECTURE_PROPOSAL.md — Layered/Clean FastAPI modular monolith for HealthCore Digital (billing denials, no-shows, CME, hiring), FE/BE separation, industry standards, and risks.
related_paths:
  - docs/ARCHITECTURE_PROPOSAL.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Rewrite ARCHITECTURE_PROPOSAL.md from scratch without human confirmation
  - Treat this stamp as an implemented FastAPI backend (doc-only proposal)
---

# HC-MS4-PLAN-006 — FastAPI Architecture Proposal Document

## Decisions locked

- Pattern: Layered Architecture with Clean Architecture principles (API → Services → Domain → Infrastructure).
- Company context embedded from project brief (HealthCore, 12 clinics, ~600 visits/week, 200+ staff, four primary domains).
- Routers conceptual only under `/api/v1` by domain; no Python endpoint code in the proposal.
- Monorepo `backend/` preferred beside `uis/healthcore` and `uis/backoffice`.

## Agent instructions

1. Do not rewrite prior plan stamps; append new ones for further architecture work.
2. Do not scaffold a real FastAPI backend from this stamp unless the user explicitly requests implementation.
3. Keep public vs backoffice isolation language consistent with techContext (hiring never on public site).
