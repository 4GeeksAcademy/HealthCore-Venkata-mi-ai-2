---
stamp: HC-PLAN-002
sequence: 2
date: 2026-07-22
title: HealthCore Frontend Multi-App Workspace
status: implemented
phase: phase-2
summary: Scaffolded uis/healthcore public site, rewrote uis/index.html as thin entry, created uis/backoffice with welcome + migrated hiring tracker at /hiring, retired uis/talent-pipeline-tracker.
related_paths:
  - uis/healthcore/
  - uis/backoffice/
  - uis/index.html
  - uis/README.md
  - memory-bank/progress.md
do_not_repeat:
  - Re-scaffold uis/healthcore from create-next-app if the app already exists with public sections
  - Re-migrate talent-pipeline-tracker into backoffice
  - Recreate standalone uis/talent-pipeline-tracker
  - Restore the old full static marketing markup in uis/index.html
  - Share layout components between uis/healthcore and uis/backoffice
---

# HC-PLAN-002 — HealthCore Frontend Multi-App Workspace

## Decisions locked

- Public site is `uis/healthcore` (Next.js App Router) with typed sections: Home, Doctors, Locations, Services, Costs, Care, About, patient sign-up.
- `uis/index.html` is a thin developer/agent entry only — not a second marketing site.
- Internal app is `uis/backoffice` with isolated layout; `/` welcome; hiring tracker at `/hiring`.
- Former `uis/talent-pipeline-tracker` content lives in backoffice; standalone folder retired.
- Public runs on port 3000; backoffice on port 3001.

## Files / areas created or changed

- `uis/healthcore/**` — public Next.js app
- `uis/backoffice/**` — internal Next.js app (migrated hiring module)
- `uis/index.html` — rewritten thin entry
- `uis/README.md` — documents both apps
- Removed `uis/talent-pipeline-tracker/`

## Verification

- `npm run typecheck` and `npm run lint` passed in `uis/healthcore` and `uis/backoffice`.

## Agent instructions

1. Treat Phase 2 UI scaffolding as **done**. Do not reverse the migration or restore the standalone tracker.
2. Extend public pages inside `uis/healthcore` only; extend internal tools inside `uis/backoffice` only.
3. Keep layouts isolated — never import public marketing chrome into backoffice (or vice versa).
4. Next likely work: Monday ops dashboards (denials, no-shows, CME) under backoffice using `src/utils/` — stamp as HC-PLAN-003 when implemented.
5. Always append new stamps; never rewrite this file.
