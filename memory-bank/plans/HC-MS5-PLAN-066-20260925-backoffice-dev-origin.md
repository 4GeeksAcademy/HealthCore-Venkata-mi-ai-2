---
stamp: HC-MS5-PLAN-066
sequence: 66
milestone: MS5
date: 20260925
title: Allow 127.0.0.1 For Backoffice Dev Assets
status: implemented
phase: implementation
summary: Backoffice next.config.ts allows 127.0.0.1 so Next dev serves hydration scripts. Login and Register were reloading the page instead of submitting.
related_paths:
  - uis/backoffice/next.config.ts
  - memory-bank/progress.md
  - memory-bank/plans/INDEX.md
do_not_repeat:
  - Remove allowedDevOrigins while staff open the app at 127.0.0.1
  - Treat a GET /register? reload as a successful registration
---

# HC-MS5-PLAN-066 — Allow 127.0.0.1 For Backoffice Dev Assets

## Decisions locked

- `allowedDevOrigins` includes `127.0.0.1` in `uis/backoffice/next.config.ts`.
- The UI container must be restarted after that config change.

## Agent instructions

- If Login or Register reloads without an error, check the dev log for blocked cross-origin `/_next` requests before changing the form.
