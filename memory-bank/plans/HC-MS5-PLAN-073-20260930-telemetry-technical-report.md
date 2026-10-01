---
stamp: HC-MS5-PLAN-073
sequence: 73
milestone: MS5
date: 2026-09-30
title: Telemetry Technical Report
status: implemented
phase: implementation
summary: >
  Added services/telemetry/analysis.py (volume, error rate, latency, login failure
  rate) and GET /telemetry/report with a 60-second cache. Backoffice /telemetry
  shows the same operational metrics. Brief saved under docs/Project_Contexts.
  Pytest 64 passed. Evaluation results are not written until the human says save.
related_paths:
  - docs/Project_Contexts/Telemetry_technical_report.md
  - docs/README.md
  - services/telemetry/analysis.py
  - services/api/app/routers/telemetry.py
  - services/api/requirements.txt
  - docker-compose.yml
  - uis/backoffice/app/(internal)/telemetry/page.tsx
  - services/api/tests/test_telemetry.py
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Do not calculate the report inside the endpoint on every request.
  - Do not group timestamps as strings. Convert with utc=True first.
  - Do not use user_login_failed names. HealthCore events are login_failed and login_succeeded.
  - Do not add purchasing or revenue metrics to this report.
  - Do not write Results/TelemetryReport-*.md until the human says save.
---

# HC-MS5-PLAN-073 — Telemetry Technical Report

## Decisions locked

- Analysis file path matches the brief: `services/telemetry/analysis.py`.
- The API container mounts that directory at `/opt/healthcore-telemetry`.
- Date window is resolved once in `GET /telemetry/report` (default last 7 days UTC).
- Cache key is the window. TTL is 60 seconds via `TtlCache`.
- Company context remains `CONTEXT-healthcore.md`. No PHI and no clinic-purchasing KPIs.

## Agent instructions

- Show the rubric score in chat. Wait for **save** before writing an evaluation Results file.
- After changing `requirements.txt`, rebuild the API image so pandas is installed.
- Do not commit `.env`.
