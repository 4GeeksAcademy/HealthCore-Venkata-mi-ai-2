---
stamp: HC-MS5-PLAN-063
sequence: 63
milestone: MS5
date: 20260925
title: Frontend Telemetry Capture Context Document
status: implemented
phase: docs
summary: Authored docs/Project_Contexts/CONTEXT-telemetry-frontend-capture.md. Docs only. Capture uses the approved plan, backoffice lib/telemetry.ts, and POST /telemetry/events on port 8001 via /hc-api.
related_paths:
  - docs/Project_Contexts/CONTEXT-telemetry-frontend-capture.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat this stamp as TelemetryService or POST /telemetry/events
  - Instrument uis/healthcore
  - Persist telemetry events
  - Hardcode port 8000 or the endpoint URL inside track()
  - Put email, name, or password in event properties
  - Rewrite the approved telemetry plan, PLAN-062, or TelemetryPlan-20260923.md
  - Use login_failed reasons session_expired or network_error
---

# HC-MS5-PLAN-063 — Frontend Telemetry Capture Context Document

## Decisions locked

- Context path: `docs/Project_Contexts/CONTEXT-telemetry-frontend-capture.md`.
- Service path for the next session: `uis/backoffice/lib/telemetry.ts`.
- Stub: `POST /telemetry/events` on `services/api` (listen **8001**). Browser env: `http://localhost:3001/hc-api/telemetry/events`.
- Event names stay those in `docs/telemetry/event-schemas.json`.

## Agent instructions

1. Do not treat this stamp as implemented capture. Stub, service, and instrumentation are a later stamp.
2. Do not create `uis/backoffice/src/services/`.
3. Do not instrument `uis/healthcore` or persist events.
4. Do not hardcode the telemetry URL or use port 8000.
5. Do not rewrite PLAN-060, PLAN-061, or PLAN-062.
