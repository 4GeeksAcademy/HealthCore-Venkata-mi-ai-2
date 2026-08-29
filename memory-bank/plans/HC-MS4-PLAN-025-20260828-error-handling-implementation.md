---
stamp: HC-MS4-PLAN-025
sequence: 25
milestone: MS4
date: 20260828
title: Error Handling Layered Implementation
status: implemented
phase: implementation
summary: Implemented scoped error handling across FastAPI, backoffice/public UI, and Python scripts from PLAN-024 audit — structured JSON errors, three-state UI with CTAs, script sys.exit(1). No new product features.
related_paths:
  - services/api/app/main.py
  - services/api/app/core/errors.py
  - services/api/app/suppliers_store.py
  - services/api/app/stores/auth_store.py
  - services/api/app/routers/users.py
  - services/api/app/routers/incidents.py
  - services/api/seed.py
  - scripts/analyze.py
  - uis/backoffice/lib/user-facing-error.ts
  - uis/backoffice/components/async/AsyncState.tsx
  - uis/healthcore/components/PatientSignupForm.tsx
  - memory-bank/evaluations/Results/ErrorHandling-20260828.md
do_not_repeat:
  - Re-add raw HTTP status strings to user-facing fetch errors
  - Show uvicorn commands or internal API URLs in incident error UI
  - Wrap entire FastAPI routers or UI components in one catch-all
  - Return Python tracebacks in API JSON bodies
  - Let seed.py fail with exit code 0
---

# HC-MS4-PLAN-025 — Error Handling Layered Implementation

## Decisions locked

- Backend: `StorageError` maps to HTTP 503; unhandled exceptions to generic 500 JSON; validation to 422 without raw parser text.
- Frontend: sanitize via `user-facing-error.ts`; `AsyncState` includes Try again, Back to home, and support hint.
- Public vs backoffice layouts remain isolated.
- PLAN-022 demo reset-link **server logs** unchanged (not sent to client).
- Scripts: `seed.py` and `analyze.py` print to stderr and return/exit 1 on I/O failure.

## Agent instructions

1. Keep client error bodies free of stack traces, status-code strings, and JSON parse text.
2. Do not leak `localhost` API URLs or process commands in backoffice incident errors.
3. Catch TinyDB/file operations at store open or the specific I/O call, not whole routers.
4. Keep `GET /health` public.
5. Do not rewrite PLAN-024; this stamp is the implementation record.
