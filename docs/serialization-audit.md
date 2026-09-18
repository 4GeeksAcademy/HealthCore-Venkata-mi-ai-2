# Backend serialization audit — HealthCore Digital API

**Date:** 2026-09-18  
**Scope:** every FastAPI route in `services/api`  
**CONTEXT:** [CONTEXT-backend-serialization-audit.md](./Project_Contexts/CONTEXT-backend-serialization-audit.md)

Auth users are TinyDB documents (not ORM). Inventory products/orders are SQLModel. HTTP JSON must still go through Pydantic `response_model`.

Register in this repo is **`POST /users`**. There is no `/auth/register`.

---

## Status legend

| Mark | Meaning |
|------|---------|
| ✓ | Explicit Pydantic `response_model` (or documented non-JSON exception) |
| Gap | Closed in this pass |

---

## Endpoint table

| Method | Path | Original return | Target schema | Status |
|--------|------|-----------------|---------------|--------|
| GET | `/health` | raw `{"status": "ok"}` dict | `HealthResponse` | ✓ (was Gap) |
| POST | `/auth/login` | `AccessTokenResponse` | `AccessTokenResponse` | ✓ |
| GET | `/auth/me` | `AuthMeResponse` (email allowed) | `AuthMeResponse` | ✓ |
| POST | `/auth/forgot-password` | `MessageResponse` | `MessageResponse` | ✓ |
| POST | `/auth/reset-password` | `MessageResponse` | `MessageResponse` | ✓ |
| POST | `/auth/change-password` | `MessageResponse` | `MessageResponse` | ✓ |
| POST | `/users` | `UserWithProfileResponse` **with** `user.email` | `UserWithProfileResponse` (`UserResponse` **without** email) | ✓ (was Gap) |
| GET | `/users` | `list[UserResponse]` **with** email | `list[UserResponse]` without email | ✓ (was Gap) |
| GET | `/users/{user_id}` | `UserResponse` **with** email | `UserResponse` without email | ✓ (was Gap) |
| PUT | `/users/{user_id}` | `UserResponse` **with** email | `UserResponse` without email | ✓ (was Gap) |
| DELETE | `/users/{user_id}` | raw `{"ok": true}` / `dict[str, bool]` | `UserDeleteAck` | ✓ (was Gap) |
| GET | `/profiles/me` | `ProfileResponse` | `ProfileResponse` | ✓ |
| PUT | `/profiles/me` | `ProfileResponse` | `ProfileResponse` | ✓ |
| GET | `/inventory/products` | `list[MedicalSupplyResponse]` | same | ✓ |
| POST | `/inventory/products` | `MedicalSupplyResponse` | same (input is `MedicalSupplyCreate`) | ✓ |
| GET | `/inventory/products/{product_id}` | `MedicalSupplyResponse` | same | ✓ |
| POST | `/inventory/orders/inbound` | `InboundOrderResponse` | same (input is `InboundOrderCreate`; keeps `created_by` email) | ✓ |
| POST | `/inventory/orders/outbound` | `OutboundOrderResponse` | same (input is `OutboundOrderCreate`; keeps `created_by` email) | ✓ |
| GET | `/inventory/orders` | `list[InventoryOrderResponse]` | same (`created_by` kept) | ✓ |
| POST | `/suppliers` | `SupplierResponse` | same (input is `SupplierCreate`) | ✓ |
| GET | `/suppliers` | `list[SupplierResponse]` | same | ✓ |
| GET | `/suppliers/{supplier_id}` | `SupplierResponse` | same | ✓ |
| PATCH | `/suppliers/{supplier_id}/rate` | `SupplierResponse` | same (input is `RateUpdate`) | ✓ |
| PATCH | `/suppliers/{supplier_id}/status` | `SupplierResponse` | same (input is `StatusUpdate`) | ✓ |
| DELETE | `/suppliers/{supplier_id}` | `DeleteAck` | `DeleteAck` | ✓ |
| POST | `/api/incidents/analyze` | raw `AnalysisResult.to_dict()` | `IncidentAnalyzeResponse` | ✓ (was Gap) |
| GET | `/api/incidents/results/export` | `Response` `text/csv` | **CSV exception** — `response_class=Response`, no JSON `response_model` | ✓ documented |

Trailing slash aliases (`POST /users/`, `GET /users/`, supplier list/create `/`) are `include_in_schema=False` and use the same models.

---

## Input vs output

| Flow | Input | Output |
|------|-------|--------|
| Register | `RegisterRequest` (email + password) | `UserWithProfileResponse` (no email, no password) |
| Login | `LoginRequest` | `AccessTokenResponse` (token only) |
| Forgot / reset / change password | request models with secrets | `MessageResponse` only |
| User update | `UserUpdateRequest` | `UserResponse` (no email) |
| Profile update | `ProfileUpdateRequest` | `ProfileResponse` |
| Inventory product | `MedicalSupplyCreate` | `MedicalSupplyResponse` |
| Inventory orders | `InboundOrderCreate` / `OutboundOrderCreate` | order response + `created_by` |
| Supplier create | `SupplierCreate` | `SupplierResponse` |

---

## Auth field policy

- Login, register, forgot/reset/change password, and 401/409 bodies do **not** echo password.
- Register `user` does **not** include `email`.
- User list / get / put do **not** include `email`.
- `GET /auth/me` **does** include `email` (session identity).
- Inventory `created_by` remains staff email for backoffice order history (ops attribution, not an unauthenticated auth echo).

---

## OpenAPI / `/docs` verification (2026-09-18)

Checked `GET /openapi.json` via TestClient (same schemas FastAPI `/docs` uses) plus live calls:

1. **`GET /health`** — schema `HealthResponse`; body `{"status":"ok"}`.
2. **`POST /users` (register)** — schema `UserWithProfileResponse`; body has `user.id` / `user.role` and **no** `user.email` or password.
3. **`POST /auth/login`** — schema `AccessTokenResponse`; body is `access_token` + `token_type` only.

---

## Tests updated

- `test_register.py` — asserts `"email" not in user`.
- `test_token.py` — `/auth/me` email compared to `STAFF_EMAIL`.
- `test_inventory.py` — `created_by` compared to `STAFF_EMAIL` (register JSON no longer carries email).
