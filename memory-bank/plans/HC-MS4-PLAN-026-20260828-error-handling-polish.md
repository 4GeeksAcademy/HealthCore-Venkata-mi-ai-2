---
stamp: HC-MS4-PLAN-026
sequence: 26
milestone: MS4
date: 20260828
title: Error Handling Residual Polish
status: implemented
phase: implementation
summary: Polished remaining error-handling gaps — AuthGuard session message, wrapped public auth fetch, hiring form CTAs and finally, mapped AnalysisError details, quieter server logs, CLI file-not-found without paths. Demo reset-link server logging kept per PLAN-022.
related_paths:
  - uis/backoffice/components/auth/AuthGuard.tsx
  - uis/backoffice/app/login/page.tsx
  - uis/backoffice/lib/auth-api.ts
  - uis/backoffice/components/async/ErrorActions.tsx
  - uis/backoffice/components/candidates/CandidateForm.tsx
  - services/api/app/main.py
  - services/api/app/routers/incidents.py
  - scripts/analyze.py
do_not_repeat:
  - Remove demo reset-link server logging required by PLAN-022
  - Restore silent AuthGuard redirects without a login reason
  - Print filesystem paths in analyze.py error output
  - Return unmapped str(exc) from incident analyze
---

# HC-MS4-PLAN-026 — Error Handling Residual Polish

## Decisions locked

- Expired or failed sessions redirect to `/login?reason=session` with a human-readable banner.
- Unauthenticated auth `fetch` is wrapped in `publicFetch` (network + HTTP errors).
- Hiring submit errors use shared `ErrorActions` (retry, home, support) and `finally` for terminal state.
- Incident analyze maps known `AnalysisError` text; unknown analysis errors get a generic 400 body.
- API handlers log exception type only (no traceback) on 500/503.
- `analyze.py` missing-file message does not include the path.
- PLAN-022 demo reset links remain in server logs for local verification.

## Agent instructions

1. Keep `/login?reason=session` messaging when the session check fails.
2. Do not unwrap `publicFetch` on login/register/forgot/reset.
3. Do not print filesystem paths in script error output.
4. Do not remove demo reset-link logging unless PLAN-022 is explicitly superseded.
