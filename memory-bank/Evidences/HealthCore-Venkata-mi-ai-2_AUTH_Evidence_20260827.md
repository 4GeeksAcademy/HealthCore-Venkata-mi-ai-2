# HealthCore-Venkata-mi-ai-2 - Authentication Evidence Report

Date: 2026-08-27
Repository: HealthCore-Venkata-mi-ai-2
Branch: Authentication_in_WebApplications
Scope: AUTH-01 + AUTH-02 + AUTH-03 + demo-mode no realtime email

## Validation commands executed

1. Backoffice lint
- Command: npm run lint (in uis/backoffice)
- Result: PASS

2. Backoffice typecheck
- Command: npm run typecheck (in uis/backoffice)
- Result: PASS

3. API syntax compile
- Command: python -m compileall app (in services/api)
- Result: PASS

4. API runtime smoke suite
- Command: JWT_SECRET_KEY=dev-secret python smoke script with FastAPI TestClient
- Result: PASS

## Runtime evidence (status codes)

- health=200
- suppliers_without_token=401
- register_a=201
- register_duplicate=409
- login_a=200
- auth_me=200
- suppliers_with_token=200
- cross_user_update=403
- forgot_known=200
- forgot_unknown=200
- reset_bad=400
- change_wrong_current=400
- change_ok=200
- relogin_after_change=200
- reset_ok=200
- reset_reuse=400
- login_after_reset=200

## AUTH-01 evidence checklist

- PASS - User register endpoint creates user+profile with 201.
- PASS - Duplicate email rejected with 409.
- PASS - Login returns bearer token with 200.
- PASS - /auth/me works with valid token.
- PASS - Protected supplier route returns 401 without token.
- PASS - Protected supplier route works with token (200).
- PASS - Cross-user modification blocked with 403.
- PASS - /health remains public (200).
- PASS - Incident routes are protected by bearer dependency in implementation.

## AUTH-02 evidence checklist

- PASS - Backoffice lint/typecheck pass after auth guard and route/page additions.
- PASS - Auth guard and token storage implemented for protected backoffice routes.
- PASS - Suppliers and incidents frontend calls use authenticated fetch flow.
- PASS - Session clear + redirect on 401 implemented in shared fetch utility.

## AUTH-03 evidence checklist

- PASS - Forgot-password returns 200 for known and unknown emails.
- PASS - Reset with invalid token returns 400.
- PASS - Reset success returns 200 and updates login password.
- PASS - Reset token reuse returns 400.
- PASS - Change-password wrong current returns 400.
- PASS - Change-password success returns 200.

## Demo-mode no realtime communication evidence

- Forgot-password outbound provider calls are disabled; reset links are logged locally.
- .env.example contains demo-safe keys only:
  - JWT_SECRET_KEY
  - ACCESS_TOKEN_EXPIRE_MINUTES
  - RESET_TOKEN_EXPIRE_MINUTES
  - BACKOFFICE_PUBLIC_URL

## Notes

- FastAPI TestClient prints a StarletteDeprecationWarning about httpx adapter usage; this does not impact test outcomes.
- Evidence based on direct command outputs in this workspace on the date above.
