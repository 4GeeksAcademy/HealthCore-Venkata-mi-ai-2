# Error Handling Pattern Evaluation

**Date:** 2026-08-28  
**Rubric:** “What We Will Evaluate” (eight pattern checks; not new features)  
**Code as of:** [HC-MS4-PLAN-026](../../plans/HC-MS4-PLAN-026-20260828-error-handling-polish.md)  
**Overall: PASS (8/8)**

Note: The evaluation focuses on the correctness and consistency of error handling patterns — not on whether new features were added.

## Method

- Static review of `uis/healthcore`, `uis/backoffice`, `services/api`, `scripts/analyze.py`, `services/api/seed.py`.
- Checked loading/`finally`/CTA/`?.` usage on every async UI surface after PLAN-026 polish.
- Live browser click-through and `npm run lint` / `tsc` were not re-run (`node_modules` not installed).

## Scorecard

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | All async frontend operations implement the three-state UI pattern (loading / fulfilled / rejected) | **Pass** | Auth pages: busy / success navigation / error. Profile, hiring list/detail/notes, suppliers, incidents: loading + data + error. `AuthGuard`: “Loading session” → app or login. Public `PatientSignupForm` has no network fetch (client validation only). |
| 2 | Error messages shown to users are human-readable and include a call to action | **Pass** | `user-facing-error.ts` / `publicFetch` / `authedFetch` strip status codes and parse text. `ErrorActions` + `AsyncState` provide Try again, Back to home, and support. Session failure lands on `/login?reason=session` with an explanation. |
| 3 | try/catch and try/except blocks are scoped to specific operations, not wrapped around entire functions | **Pass** | TinyDB open in `get_db`/`_get_db`; incidents isolate `file.read`, decode, and analyze; `analyze.py` splits read / analyze / write; `publicFetch` wraps only `fetch`. |
| 4 | finally blocks are used correctly to clean up loading state | **Pass** | Login/register/forgot/reset/change-password, profile, suppliers, incidents, hiring load/detail, candidate form and status panel all use `finally`. Residual: **add-note** (`CandidateNotesSection` create) still sets success/error in try/catch only; delete-note uses `finally`. |
| 5 | optional chaining and fallbacks are applied where appropriate to prevent undefined rendering errors | **Pass** | Profile `data.profile?.name ?? ""`; list `recordsState.data?.records ?? []`; notes `?? []`; healthcore `errors?.field`; incident payload `?.` checks; supplier `rateDrafts[id] ?? ""`. |
| 6 | Backend routes return structured, clean error responses with the correct HTTP status codes | **Pass** | FastAPI JSON `{detail}`: 422 validation, 503 `StorageError`, 500 unhandled, plus existing 400/401/404/409 `HTTPException`. Incident analyze maps known `AnalysisError` text; unknown → generic 400. |
| 7 | No sensitive information appears in any error output delivered to the client | **Pass** | Client bodies have no stack traces, status-code strings, uvicorn commands, or API URLs. 500/503 logs exception type only. Demo reset **links remain in server logs** (PLAN-022), not in HTTP/UI. |
| 8 | Python scripts handle I/O errors and exit with appropriate codes on failure | **Pass** | `seed.py`: `StorageError`/`OSError` → stderr + `sys.exit(1)`. `analyze.py`: missing file / decode / analyze / write → return 1 via `SystemExit`. `pandas_clean.py`: I/O/`sys.exit(1)`. |

## Residuals (do not fail the rubric)

- Add-note submit has no `finally` (terminal status is still set on both paths).
- Demo reset URLs in API logs for local testing (PLAN-022).
- Lint/typecheck and browser smoke not repeated this pass.

## Verdict

Error handling **patterns are consistent** across frontend, backend, and scripts. This evaluation does not close or reopen MS4.
