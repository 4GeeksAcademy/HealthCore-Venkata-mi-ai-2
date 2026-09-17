---
stamp: HC-MS5-PLAN-040
sequence: 40
milestone: MS5
date: 20260914
title: MS5 Container CONTEXT Audit Scope Runbook
status: implemented
phase: docs
summary: Audited CONTEXT-MS5-container.md against ticket #infra-40. Tightened in/out of scope, dropped seed-on-boot and Compose pytest as requirements, replaced Alpine wget samples with node fetch, and added a post-implementation Docker Desktop runbook. Docs only; Docker still not implemented.
related_paths:
  - docs/Project_Contexts/CONTEXT-MS5-container.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as implemented Dockerfiles or docker-compose.yml
  - Require services/start.sh or seed.py on API boot for #infra-40
  - Use wget/ping inside the Node Alpine ui image as the official inter-service check
  - Add extra Compose services, prod TLS, or new error-handling UI for this ticket
  - Rewrite PLAN-039 or root CONTEXT.md
---

# HC-MS5-PLAN-040 — MS5 Container CONTEXT Audit Scope Runbook

## Decisions locked

- `#infra-40` file list stays: `uis/Dockerfile`, `uis/start.sh`, `uis/.dockerignore`, `services/Dockerfile`, `services/.dockerignore`, root `docker-compose.yml`, gitignored root `.env`.
- HealthCore mappings stay: `website` → `uis/healthcore`, API `services/api` port 8001, network `healthcore`, services `ui`/`api`, `/hc-api` rewrite to `http://api:8001`, bind-mount `src/`.
- Seed-on-boot, extra Compose services, pytest-in-Compose, and new 502 UI are **out of scope**.
- Inter-service sample checks use `node fetch` or the API Python image (Alpine has no wget/ping).
- Post-implementation runbook starts at Docker Desktop download, then engine check, `.env`, `docker compose up --build`, URLs, service-name verify, hot reload, `down`.

## Agent instructions

1. Do not treat PLAN-039 or this stamp as implemented containers.
2. Implement later only against [`CONTEXT-MS5-container.md`](../../docs/Project_Contexts/CONTEXT-MS5-container.md) in/out of scope lists.
3. Do not add seed-on-boot or extra services for `#infra-40`.
4. Do not document `wget`/`ping` as the `ui` container health check.
5. Do not rewrite PLAN-039. Append a new stamp for Docker implementation.
