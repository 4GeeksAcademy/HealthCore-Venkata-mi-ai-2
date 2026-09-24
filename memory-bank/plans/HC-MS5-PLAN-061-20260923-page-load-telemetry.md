---
stamp: HC-MS5-PLAN-061
sequence: 61
milestone: MS5
date: 20260923
title: Add Backoffice Page Load Telemetry Event
status: implemented
phase: docs
summary: Added identified event page_load_recorded to the telemetry plan and draft-07 schema so backoffice load time is explicit beside API latency.
related_paths:
  - docs/telemetry/telemetry-plan.md
  - docs/telemetry/event-schemas.json
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Emit page_load_recorded with resource URLs or query strings
  - Instrument uis/healthcore for this event
  - Rewrite PLAN-060
---

# HC-MS5-PLAN-061 — Add Backoffice Page Load Telemetry Event

## Decisions locked

- `page_load_recorded` is an identified performance event, batch, throttled to one path per session per 60 seconds.
- `path` uses the same allowlist as `section_viewed`. `load_kind` is `navigate` or `reload`.

## Agent instructions

1. Do not add resource URLs or query strings to `page_load_recorded`.
2. Do not emit this event from `uis/healthcore`.
3. Do not rewrite PLAN-060. Append a new stamp for further telemetry design changes.
