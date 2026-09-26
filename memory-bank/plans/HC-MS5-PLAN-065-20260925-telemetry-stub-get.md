---
stamp: HC-MS5-PLAN-065
sequence: 65
milestone: MS5
date: 20260925
title: Telemetry Stub GET Explains POST-Only URL
status: implemented
phase: implementation
summary: GET /telemetry/events returns 200 HTML so a browser visit is visible. POST batch behavior is unchanged and still does not persist.
related_paths:
  - services/api/app/routers/telemetry.py
  - services/api/tests/test_telemetry.py
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Treat a browser GET of /hc-api/telemetry/events as a failed batch
  - Persist telemetry events
  - Require a JWT on the stub
  - Rewrite PLAN-064
---

# HC-MS5-PLAN-065 — Telemetry Stub GET Explains POST-Only URL

## Decisions locked

- Address-bar visits are GET and return 200 HTML explaining that batches are POST `{ "events": [...] }`.
- POST still returns `{ "received": N }` and does not store events.

## Agent instructions

- Verify batches in DevTools Network while using the backoffice, not by expecting this URL to render the app.
- Do not persist events in this stub.
