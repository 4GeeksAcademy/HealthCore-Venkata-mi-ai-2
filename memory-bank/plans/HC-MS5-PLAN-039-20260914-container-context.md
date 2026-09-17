---
stamp: HC-MS5-PLAN-039
sequence: 39
milestone: MS5
date: 20260914
title: MS5 Development Containerization Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/CONTEXT-MS5-container.md — assignment CONTEXT for ticket #infra-40 locking one UI container (healthcore:3000 + backoffice:3001), FastAPI with --reload on api:8001, named network healthcore, root .env, /hc-api rewrite, samples, and test cases. Docs only; no Dockerfiles or Compose yet.
related_paths:
  - docs/Project_Contexts/CONTEXT-MS5-container.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Place CONTEXT-MS5-container.md directly under docs/
  - Treat this stamp as implemented Dockerfiles, start.sh, or docker-compose.yml
  - Create uis/website or map the ticket website app to anything other than uis/healthcore
  - Hardcode secrets in Compose/Dockerfiles or commit .env
  - Use localhost as the UI-container-to-API host (must be http://api:8001)
  - Rewrite root CONTEXT.md or CONTEXT-MS5-inventory-backoffice.md
---

# HC-MS5-PLAN-039 — MS5 Development Containerization Context Document

## Decisions locked

- Context file path: `docs/Project_Contexts/CONTEXT-MS5-container.md` (not `docs/` root, not root `CONTEXT.md`).
- Ticket `#infra-40` `/uis/website` maps to **`uis/healthcore`**. Backoffice stays `uis/backoffice`. FastAPI stays `services/api` on port **8001**.
- Compose services: `ui` and `api` on named network `healthcore`.
- One UI container starts both Next.js apps (`3000` and `3001`) via `uis/start.sh`. API uses Uvicorn `--reload` on `0.0.0.0:8001`.
- Inter-service API URL is `http://api:8001`. Browser uses same-origin `/hc-api` rewritten in backoffice `next.config.ts`.
- All env names live in a gitignored root `.env` (`env_file`). No secrets in YAML or Dockerfiles.
- Bind-mount `uis/healthcore`, `uis/backoffice`, and repo-root `src/` for hot reload and `@hc`.
- Docs only — no Dockerfiles, `.dockerignore`, `start.sh`, or `docker-compose.yml` in this stamp.

## Agent instructions

1. Do not place `CONTEXT-MS5-container.md` directly under `docs/`.
2. Do not treat this stamp as implemented containerization. Docker files belong in a later stamp.
3. Do not create `uis/website`. Implement against `uis/healthcore` + `uis/backoffice` + `services/api`.
4. Do not put `localhost` as the host in UI→API container URLs; use `http://api:8001` plus `/hc-api` rewrite.
5. Do not commit `.env` or hardcode JWT/database/provider secrets in Compose or Dockerfiles.
6. Do not rewrite root `CONTEXT.md` or the inventory/auth CONTEXTs.
7. Append a new stamp for Docker implementation; do not rewrite this stamp.
