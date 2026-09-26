---
stamp: HC-MS5-PLAN-067
sequence: 67
milestone: MS5
date: 20260925
title: Telemetry URL Comes From Environment Only
status: implemented
phase: implementation
summary: track() reads NEXT_PUBLIC_TELEMETRY_ENDPOINT and no longer falls back to a URL in source. The value stays /hc-api/telemetry/events so batches, login, and inventory behavior are unchanged.
related_paths:
  - uis/backoffice/lib/telemetry.ts
  - docker-compose.yml
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Put the telemetry URL back inside telemetry.ts
  - Change event_type names, property allowlists, or the stub response
  - Rewrite TelemetryPlan-20260923.md or the capture scorecard
  - Commit .env or .env.local
---

# HC-MS5-PLAN-067 — Telemetry URL Comes From Environment Only

## Decisions locked

- `endpoint()` returns `process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT` only.
- The configured value remains `/hc-api/telemetry/events`.

## Agent instructions

- Do not change the approved event catalogue while adjusting this URL.
- Do not commit `.env` or `.env.local`.
