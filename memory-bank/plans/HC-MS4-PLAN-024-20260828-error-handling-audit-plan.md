---
stamp: HC-MS4-PLAN-024
sequence: 24
milestone: MS4
date: 20260828
title: Error Handling Audit and Layered Implementation Plan
status: planned
phase: planning
summary: Full-repo audit against ErrorHandling Requirement.txt (eight taxonomy categories), then sequenced implementation — FastAPI handlers, backoffice/public UI three-state pattern, Python script exit codes — without new features.
related_paths:
  - .cursor/skills/error-handling-audit/SKILL.md
  - services/api/app/main.py
  - uis/backoffice
  - uis/healthcore
  - services/api/seed.py
  - scripts/analyze.py
do_not_repeat:
  - Rewrite root CONTEXT.md for error handling
  - Share layouts between uis/healthcore and uis/backoffice
  - Change forgot-password to enumerate users or send live email
  - Add features unrelated to error handling
  - Remove demo reset-link server logging required by PLAN-022
---

# HC-MS4-PLAN-024 — Error Handling Audit and Layered Implementation Plan

## Requirement

Apply a consistent error handling strategy across frontend, backend, and scripts. Audit the entire repository first. Do not introduce new features.

## Audit summary (pre-implementation)

Highest impact first.

### Backend (`services/api`)

| Category | File | Problem |
|----------|------|---------|
| MISSING TRY/CATCH / RAW ERROR EXPOSURE | `app/main.py` | No exception handlers; uncaught TinyDB/I/O becomes default 500 |
| MISSING TRY/CATCH | `suppliers_store.py` `get_db` / CRUD | TinyDB open/read/write uncaught |
| MISSING TRY/CATCH | `stores/auth_store.py` `_get_db` and store functions | Same for auth.json |
| MISSING TRY/CATCH | `routers/incidents.py` `file.read()` | Upload stream errors uncaught |
| MISSING TRY/CATCH | `auth_store.consume_reset_token` | `fromisoformat` can raise on corrupt data |
| RAW ERROR EXPOSURE | `routers/users.py` | `detail=str(exc)` on ValueError |
| RAW ERROR EXPOSURE | `routers/incidents.py` export 404 | Mentions internal POST path |
| SILENT FAILURES | `incident_analysis.py` | `except ValueError: pass` on satisfaction parse |

Kept as-is (PLAN-022): demo reset links may appear in **server logs** only, never in client bodies.

### Frontend

| Category | File | Problem |
|----------|------|---------|
| RAW ERROR EXPOSURE | `lib/auth-api.ts`, `lib/authed-fetch.ts`, `lib/api-client.ts` | Status codes and raw `detail` / JSON parse errors reach UI |
| RAW ERROR EXPOSURE | Auth and supplier/incident pages | `err.message` shown directly |
| SENSITIVE DATA LEAKS | `IncidentAnalyzerPanel.tsx` | API URL and uvicorn command in error/help copy |
| MISSING TRY/CATCH | Success-path `res.json()` in auth/suppliers APIs | Unguarded parse |
| MISSING TRY/CATCH | Backoffice `app/api/records*` | `request.json()` unguarded |
| NO USER CALL TO ACTION | `AsyncState.tsx` and consumers | Message only; no retry / home / support |
| MISSING LOADING/ERROR UI | `account/profile/page.tsx` | `data.profile.name` without `?.` |
| SILENT FAILURES | `uis/scripts/main.js`, `scripts/main.js` | Empty catch on i18n load |

`uis/healthcore` has no network fetch (client validation only). Still apply safe render fallbacks on the signup form if needed.

### Scripts

| Category | File | Problem |
|----------|------|---------|
| MISSING sys.exit / TRY/CATCH | `services/api/seed.py` | Uncaught TinyDB failure; implicit exit 0 vs traceback |
| OVERLY BROAD CATCH / MISSING TRY/CATCH | `scripts/analyze.py` | Read+analyze in one try; `UnicodeDecodeError` and CSV write uncaught |
| MISSING sys.exit | `skills/data-analysis/scripts/pandas_clean.py` | Example script has no I/O handling or non-zero exit |

## Implementation sequence

1. **Backend** — `StorageError`, scoped TinyDB/open handlers, FastAPI JSON handlers (400/404/422/500/503), sanitize `str(exc)` and export 404 copy, incidents `file.read()`, reset-token parse.
2. **Frontend** — sanitize HTTP errors in fetch helpers; `finally` on loading; optional chaining; `AsyncState` retry/home/support; incident panel (no internal URL/command); records JSON parse; i18n script catches.
3. **Scripts** — `seed.py` stderr + `sys.exit(1)`; `analyze.py` scoped I/O; `pandas_clean.py` main guard.
4. **Evaluate** against the eight rubric bullets (patterns only, not new features).

## Agent instructions

1. Implement only error handling and error communication of existing code.
2. Keep public and backoffice UIs layout-isolated.
3. Keep forgot-password generic; do not add provider keys.
4. Do not rewrite this stamp after implementation — add a later `implemented` stamp.
5. Do not rewrite root `CONTEXT.md`.
