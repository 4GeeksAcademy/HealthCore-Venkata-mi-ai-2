---
stamp: HC-MS5-PLAN-042
sequence: 42
milestone: MS5
date: 20260916
title: MS5 Container Runbook Browse After Compose Up
status: implemented
phase: docs
summary: Expanded CONTEXT-MS5-container.md how-to-run with browse-after-containers-up instructions — localhost URLs in a host browser, not Docker Desktop; /health JSON may look blank; virtualization and docker-not-recognized troubleshooting. Docs only.
related_paths:
  - docs/Project_Contexts/CONTEXT-MS5-container.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as a Docker/code change
  - Tell squad to browse the apps inside Docker Desktop
  - Treat a blank /health tab as an API failure without checking JSON
  - Rewrite PLAN-041
---

# HC-MS5-PLAN-042 — MS5 Container Runbook Browse After Compose Up

## Decisions locked

- After `docker compose up`, squad members use a host browser on `localhost:3000`, `:3001`, `:8001/docs`, and `:8001/health`.
- Docker Desktop is the engine UI only; it is not the HealthCore website.
- `GET /health` returning JSON can render as a blank page; `/docs` or View Source is the check.
- Docs only — no Dockerfile or Compose edits in this stamp.

## Agent instructions

1. Keep browse instructions in [`CONTEXT-MS5-container.md`](../../docs/Project_Contexts/CONTEXT-MS5-container.md) How to run, section 6.
2. Do not send users to open the Next apps inside Docker Desktop.
3. Do not treat a blank `/health` tab as a failed API without a JSON/docs check.
4. Append a new stamp for later work; do not rewrite this file.
