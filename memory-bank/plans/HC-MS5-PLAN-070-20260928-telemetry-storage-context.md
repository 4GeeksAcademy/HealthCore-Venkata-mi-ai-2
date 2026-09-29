---
stamp: HC-MS5-PLAN-070
sequence: 70
milestone: MS5
date: 2026-09-28
title: Telemetry Storage CONTEXT Document
status: implemented
phase: docs
summary: >
  Added docs/Project_Contexts/CONTEXT-telemetry-storage.md for Company's Telemetry
  Storage (Supabase telemetry_events, bulk insert, per-event validation). Linked from
  docs/README.md. No code changes in this stamp — implementation is a follow-on plan.
related_paths:
  - docs/Project_Contexts/CONTEXT-telemetry-storage.md
  - docs/README.md
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Do not re-create CONTEXT-telemetry-storage.md; update in place only if the assignment brief changes.
  - Do not implement the storage endpoint under this stamp; wait for an execution plan after human review.
---

# HC-MS5-PLAN-070 — Telemetry Storage CONTEXT Document

## Goal

Archive the storage assignment brief under `docs/Project_Contexts/` so agents can implement Supabase persistence without re-deriving the course README.

## Done

- Wrote `CONTEXT-telemetry-storage.md` (phases, mapping, eval checklist, HealthCore bindings).
- Linked it from `docs/README.md`.

## Agent instructions

1. Next: implement storage only after human approves the execution plan shown in chat.
2. Prerequisite remains capture stub **200**; frontend must stay untouched; `TelemetryEvent` fields stay unchanged.
3. Evaluation Results must not be written until the human says **save**.
