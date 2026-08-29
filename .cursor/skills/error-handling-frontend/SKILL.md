---
name: error-handling-frontend
description: >-
  Apply three-state UI error handling to Next.js/TypeScript HealthCore apps.
  Use when editing fetch/API calls in uis/healthcore or uis/backoffice, or
  when adding loading, success, and error states, retry/home/support CTAs,
  optional chaining, or finally-based loading cleanup.
---

# Frontend error handling

Read first:

- [policy.context.md](../error-handling-audit/policy.context.md)
- [findings-taxonomy.context.md](../error-handling-audit/findings-taxonomy.context.md)

## Frontend (Next.js / TypeScript)

- Identify all fetch or API calls in the frontend and verify each one has a try/catch block scoped specifically to that call.
- For every async data-fetching operation, implement the three-state UI pattern: loading (spinner or skeleton), fulfilled (data renders), rejected (error message with a call to action).
- Replace any raw error messages (Error 500, Unexpected token, etc.) with human-readable explanations.
- Ensure every error state includes a meaningful call to action: a retry button, a link to the home page, or a contact support prompt.
- Use optional chaining (`?.`) where accessing potentially undefined nested properties.
- Add safe defaults or fallbacks for values that could be null or undefined when rendering.
- Use finally blocks to ensure loading states are always cleared, regardless of outcome.

Every async operation on the frontend must have three visible states: loading, success, and error.

Error messages shown to users must be human-readable — never a raw stack trace, status code, or JSON parsing error.

Every error state must offer a clear exit: a retry button, a link back to home, or instructions to contact support.

⚠ IMPORTANT: Do not introduce new features or refactor code unrelated to error handling.

## General

Review the codebase for any `console.error` or `print` statements that expose sensitive internal information and remove or replace them.

## HealthCore repo notes

- Public app: `uis/healthcore`. Internal app: `uis/backoffice`. Do not share layouts or marketing chrome between them.
- Keep error copy inside the app you are editing.
- Catch the fetch/API call, not the entire component or function.
- Do not show secrets, member IDs, or clinical free text in UI errors. Sample IDs (`HC-*`, `CLM-*`, `APT-*`, `CLN-*`) are synthetic.
- Auth/session errors: on 401, follow existing backoffice logout/redirect behavior; do not leak token or user-enumeration details.
