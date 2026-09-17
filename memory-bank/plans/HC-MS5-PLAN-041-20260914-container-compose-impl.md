---
stamp: HC-MS5-PLAN-041
sequence: 41
milestone: MS5
date: 20260914
title: MS5 Development Docker Compose Implementation
status: implemented
phase: implementation
summary: Dockerized HealthCore for local dev per CONTEXT-MS5-container.md — one UI container (healthcore:3000 + backoffice:3001 via start.sh), FastAPI uvicorn --reload as api:8001, named network healthcore, root env_file, /hc-api rewrite to http://api:8001, bind-mount src. .env gitignored. Compose not executed here (Docker CLI not installed on the agent machine).
related_paths:
  - uis/Dockerfile
  - uis/start.sh
  - uis/.dockerignore
  - services/Dockerfile
  - services/.dockerignore
  - docker-compose.yml
  - uis/backoffice/next.config.ts
  - docs/Project_Contexts/CONTEXT-MS5-container.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Create uis/website or a second UI container
  - Put localhost as the UI-container-to-API host (keep http://api:8001)
  - Hardcode JWT/database/provider secrets in Compose or Dockerfiles
  - Commit .env
  - Drop the src/ bind mount or named node_modules volumes
  - Use production next start as the Compose command
  - Point turbopack.root at uis/backoffice only
  - Rewrite PLAN-039 or PLAN-040
---

# HC-MS5-PLAN-041 — MS5 Development Docker Compose Implementation

## Decisions locked

- Files: `uis/Dockerfile` (Node 22 Alpine, both apps, `CMD` `start.sh`), `uis/start.sh`, `uis/.dockerignore`, `services/Dockerfile` (`uv pip install --system "-r" requirements.txt`, uvicorn `--reload` on `0.0.0.0:8001`), `services/.dockerignore`, root `docker-compose.yml`.
- Compose services `ui` and `api` on named network `healthcore`. Ports 3000, 3001, 8001.
- Inter-service URL `HEALTHCORE_API_INTERNAL_URL=http://api:8001`. Backoffice rewrites `/hc-api` to that host. Browser uses `/hc-api`, not `http://api:8001`.
- Bind mounts: `uis/healthcore`, `uis/backoffice`, `src/`, `services/api`. Named volumes for Alpine `node_modules`.
- Env via gitignored root `.env` (`env_file`). No secrets in YAML/Dockerfiles.
- Docker Desktop / `docker` CLI was not available on the implementing machine; `docker compose up` was not run here. Squad verification is the CONTEXT runbook.

## Agent instructions

1. Do not create `uis/website`. Keep healthcore `:3000` and backoffice `:3001` in one `ui` container.
2. Do not set UI→API container URLs to `localhost`. Keep `http://api:8001` plus `/hc-api`.
3. Do not commit `.env` or put secrets in Compose/Dockerfiles.
4. Keep the `src/` bind mount and `turbopack.root` at the monorepo (`/workspace` in the UI container).
5. After Docker Desktop is installed, verify with `docker compose up --build` and TC-C01–TC-C18 in the container CONTEXT.
6. Append a new stamp for later work; do not rewrite this file.
