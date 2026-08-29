---
name: error-handling-backend
description: >-
  Apply scoped exception handling and structured HTTP errors in the FastAPI
  backend. Use when editing services/api route handlers, TinyDB access,
  outbound HTTP/LLM calls, or API error JSON bodies (400, 404, 422, 500).
---

# Backend error handling

Read first:

- [policy.context.md](../error-handling-audit/policy.context.md)
- [findings-taxonomy.context.md](../error-handling-audit/findings-taxonomy.context.md)

## Backend (Python / FastAPI)

- Review every route handler and ensure exceptions are caught at the correct scope – avoid single large try/except blocks that swallow all errors.
- Return appropriate HTTP error responses (400, 404, 422, 500) with a clean, structured JSON body – no raw Python tracebacks.
- Ensure error responses do not expose sensitive data (database connection strings, internal paths, secret keys).
- Add error handling to all external API calls made from the backend (e.g., calls to an LLM or third-party service).

On the backend and scripts, exceptions must be caught at the right scope — not with a single try/catch wrapping the entire function.

Sensitive information must never appear in error output sent to the client.

⚠ IMPORTANT: Do not introduce new features or refactor code unrelated to error handling.

## General

Review the codebase for any `console.error` or `print` statements that expose sensitive internal information and remove or replace them.

## HealthCore repo notes

- API lives under `services/api`.
- Catch the specific dangerous operation, not the entire handler. Do not wrap a whole router or `main.py` in one blanket except.
- Do not leak secrets, internal paths, database connection strings, or personal data in client error bodies or logs.
- Keep forgot-password responses generic (no user enumeration). Demo auth must not send real provider errors to the client. Do not add live provider API keys to tracked files.
- `GET /health` remains public; do not change route access as part of error handling unless required to return a clean error body.
