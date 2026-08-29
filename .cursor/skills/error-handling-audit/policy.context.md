# Error handling policy

**Source:** ErrorHandling Requirement.txt.

## Strategy

Apply a consistent error handling strategy across all layers: frontend, backend, and scripts.

- No error should crash the application or leave the user in an undefined state.
- Every async operation on the frontend must have three visible states: loading, success, and error.
- Error messages shown to users must be human-readable — never a raw stack trace, status code, or JSON parsing error.
- Every error state must offer a clear exit: a retry button, a link back to home, or instructions to contact support.
- On the backend and scripts, exceptions must be caught at the right scope — not with a single try/catch wrapping the entire function.
- Sensitive information must never appear in error output sent to the client.
- User who encounters a problem in the platform will know what happened and what to do next.

## General

- Review the codebase for any console.error or print statements that expose sensitive internal information and remove or replace them.

## Scope lock

⚠ IMPORTANT: Do not introduce new features or refactor code unrelated to error handling. The scope of this project is strictly the resilience and error communication of existing code.

## What we will evaluate

The evaluation focuses on the correctness and consistency of error handling patterns — not on whether new features were added.

- All async frontend operations implement the three-state UI pattern (loading / fulfilled / rejected).
- Error messages shown to users are human-readable and include a call to action.
- try/catch and try/except blocks are scoped to specific operations, not wrapped around entire functions.
- finally blocks are used correctly to clean up loading state.
- optional chaining and fallbacks are applied where appropriate to prevent undefined rendering errors.
- Backend routes return structured, clean error responses with the correct HTTP status codes.
- No sensitive information appears in any error output delivered to the client.
- Python scripts handle I/O errors and exit with appropriate codes on failure.

## HealthCore repo notes

- Public app: `uis/healthcore`. Internal app: `uis/backoffice`. Do not share layouts or marketing chrome between them.
- Backend: FastAPI under `services/api`.
- Treat sample IDs (`HC-*`, `CLM-*`, `APT-*`, `CLN-*`) as synthetic. Do not log or return real PHI, member IDs, or clinical free text.
- Forgot-password stays generic (no user enumeration). Demo auth must not send provider/network errors or secrets to the client.
- Do not add provider API keys to tracked files.
