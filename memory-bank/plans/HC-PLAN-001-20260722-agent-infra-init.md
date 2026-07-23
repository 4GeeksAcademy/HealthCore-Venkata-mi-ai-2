---
stamp: HC-PLAN-001
sequence: 1
date: 2026-07-22
title: HealthCore Agent Infrastructure Init
status: implemented
phase: phase-1
summary: Created HealthCore memory bank, stamped plan archive, root AGENTS.md, always-active clinical and plan-archive rules, and Monday ops readiness skill. Phase 2 UI work not started.
related_paths:
  - memory-bank/projectbrief.md
  - memory-bank/techContext.md
  - memory-bank/progress.md
  - memory-bank/plans/README.md
  - memory-bank/plans/INDEX.md
  - AGENTS.md
  - .agents/rules/healthcore-clinical-data.md
  - .agents/rules/healthcore-plan-archive.md
  - .agents/skills/monday-ops-readiness.md
do_not_repeat:
  - Recreate memory-bank/projectbrief.md or techContext.md from scratch
  - Recreate AGENTS.md session-start / 4-step pre-commit / protected zones from scratch
  - Recreate .agents/rules/healthcore-clinical-data.md or healthcore-plan-archive.md
  - Recreate .agents/skills/monday-ops-readiness.md
  - Start Phase 2 (uis/healthcore, uis/backoffice, index.html rewrite, tracker migration) without explicit human confirmation that Phase 1 was verified
---

# HC-PLAN-001 — HealthCore Agent Infrastructure Init

## Decisions locked

- HealthCore domain context (12 clinics, Tom/Marcus/Diane stakeholders, James Osei CTO) is encoded in the memory bank.
- Agents must read memory bank + latest stamp at every session start.
- Pre-commit requires exactly four steps: linting, type-checking, state sync, change logging.
- Plan stamps live under `memory-bank/plans/` with monotonic `HC-PLAN-NNN` ids; existing stamps are append-only.
- Public (`uis/healthcore`) and backoffice (`uis/backoffice`) remain layout-isolated when Phase 2 runs.
- Hiring tracker migrates into backoffice; `uis/index.html` is rewritten — both deferred to Phase 2.

## Files created

- `memory-bank/projectbrief.md`
- `memory-bank/techContext.md`
- `memory-bank/progress.md`
- `memory-bank/plans/README.md`
- `memory-bank/plans/INDEX.md`
- `AGENTS.md`
- `.agents/rules/healthcore-clinical-data.md` (always active)
- `.agents/rules/healthcore-plan-archive.md` (always active)
- `.agents/skills/monday-ops-readiness.md`

## Verification

- Phase 1 documentation artifacts present at the paths above.
- No `uis/healthcore` or `uis/backoffice` scaffolding performed in this stamp.
- Human verification required before Phase 2.

## Agent instructions

1. Treat Phase 1 agent infrastructure as **done**. Do not recreate the files listed in `do_not_repeat`.
2. Before any UI scaffolding, wait for explicit human approval that Phase 1 was verified.
3. When Phase 2 is approved, implement `uis/healthcore`, rewrite `uis/index.html`, create `uis/backoffice` with migrated hiring tracker, retire `uis/talent-pipeline-tracker`, then create **HC-PLAN-002** (or next free sequence).
4. Always append new stamps; never rewrite this file.
5. Keep public and backoffice layouts isolated; never put the hiring tracker on the public site.
