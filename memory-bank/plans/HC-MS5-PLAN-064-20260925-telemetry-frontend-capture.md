---
stamp: HC-MS5-PLAN-064
sequence: 64
milestone: MS5
date: 20260925
title: Backoffice Telemetry Capture And Stub Receiver
status: implemented
phase: implementation
summary: Added an unauthenticated POST /telemetry/events stub and backoffice track() with batching, beacon flush, and instrumentation for the approved event catalogue plus web_vital_recorded.
related_paths:
  - services/api/app/routers/telemetry.py
  - services/api/app/models/telemetry.py
  - services/api/app/core/config.py
  - uis/backoffice/lib/telemetry.ts
  - docs/telemetry/event-schemas.json
  - docs/telemetry/telemetry-plan.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Persist telemetry events or require a JWT on the stub
  - Instrument uis/healthcore
  - Put email, name, password, notes, or CSV cells in event properties
  - Use login_failed reasons session_expired or network_error
  - Emit an event_type that is not in event-schemas.json
  - Rewrite PLAN-063 or TelemetryPlan-20260923.md
  - Close MS5 from this stamp
---

# HC-MS5-PLAN-064 — Backoffice Telemetry Capture And Stub Receiver

## Decisions locked

- Stub: `POST /telemetry/events` returns `{ "received": N }` and logs count plus `event_type` only. `Settings.telemetry_endpoint` is read and not used to forward.
- Browser URL is same-origin `NEXT_PUBLIC_TELEMETRY_ENDPOINT` or `/hc-api/telemetry/events`.
- Public capture function is `track()` in `uis/backoffice/lib/telemetry.ts`.
- `web_vital_recorded` is an identified performance event with `name`, `value`, and `path`.

## Agent instructions

- Keep the stub temporary. The next persistence project replaces the handler, not the `TelemetryEvent` envelope.
- Do not add properties outside the allowlist in `docs/telemetry/event-schemas.json`.
- Do not commit `.env` or `.env.local`.
- Do not mark MS5 complete from this capture work.
