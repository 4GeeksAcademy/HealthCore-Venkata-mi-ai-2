# HealthCore Digital API

FastAPI service for:

- CSV incident analysis (shared with `scripts/analyze.py`)
- Clinic supplier directory (TinyDB)

## Setup

```bash
cd services/api
python -m pip install -r requirements.txt
cp .env.example .env
python seed.py
```

Set `JWT_SECRET_KEY` in `.env` before starting the API.

Minimum `.env` values for auth:

- `JWT_SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default `30`)
- `RESET_TOKEN_EXPIRE_MINUTES` (default `30`)
- `BACKOFFICE_PUBLIC_URL` (default `http://localhost:3001`)

Demo note: forgot-password runs in demo mode and does not send real outbound email.
The reset link is written to API logs for local testing.

Seeder writes `data/suppliers.json` and prints `Inserted N supplier(s).` Re-runs do not duplicate rows.

## Run

```bash
cd services/api
python -m uvicorn app.main:app --reload --port 8001
```

Health: http://localhost:8001/health → `{"status":"ok"}`

## Endpoints

### Incidents

- `POST /api/incidents/analyze` — multipart CSV upload → JSON summary (requires Bearer token)
- `GET /api/incidents/results/export` — last analysis as `results.csv` (requires Bearer token)

### Auth

- `POST /users` — register user + linked profile (201)
- `POST /auth/login` — returns `{"access_token":"...","token_type":"bearer"}`
- `GET /auth/me` — current authenticated user + profile
- `POST /auth/forgot-password` — always returns 200 generic response
- `POST /auth/reset-password` — token + new password; invalid/expired/used token returns 400
- `POST /auth/change-password` — authenticated password change
- `GET /users` — list users (requires Bearer token)
- `GET /users/{id}` — user detail (requires Bearer token)
- `PUT /users/{id}` — owner/admin update; role change only admin
- `DELETE /users/{id}` — owner/admin delete (also deletes profile)
- `GET /profiles/me` — current profile
- `PUT /profiles/me` — update name/phone/address

### Suppliers

- `POST /suppliers` — create (201, requires Bearer token)
- `GET /suppliers` — list; optional `country`, `category` (AND when both set, requires Bearer token)
- `GET /suppliers/{id}` — detail (404 if missing, requires Bearer token)
- `PATCH /suppliers/{id}/rate` — update `monthly_rate` + `updated_at` (requires Bearer token)
- `PATCH /suppliers/{id}/status` — `active` | `suspended` (requires Bearer token)
- `DELETE /suppliers/{id}` — `{"ok": true, "id": ...}` (requires Bearer token)

Field names and enums must match `docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`.
