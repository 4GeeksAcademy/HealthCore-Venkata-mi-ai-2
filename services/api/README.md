# HealthCore Digital API

FastAPI service for:

- CSV incident analysis (shared with `scripts/analyze.py`)
- Clinic supplier directory (TinyDB)

## Setup

```bash
cd services/api
python -m pip install -r requirements.txt
python seed.py
```

Seeder writes `data/suppliers.json` and prints `Inserted N supplier(s).` Re-runs do not duplicate rows.

## Run

```bash
cd services/api
python -m uvicorn app.main:app --reload --port 8001
```

Health: http://localhost:8001/health → `{"status":"ok"}`

## Endpoints

### Incidents

- `POST /api/incidents/analyze` — multipart CSV upload → JSON summary
- `GET /api/incidents/results/export` — last analysis as `results.csv`

### Suppliers

- `POST /suppliers` — create (201)
- `GET /suppliers` — list; optional `country`, `category` (AND when both set)
- `GET /suppliers/{id}` — detail (404 if missing)
- `PATCH /suppliers/{id}/rate` — update `contract_rate` + `updated_at`
- `PATCH /suppliers/{id}/status` — `active` | `suspended`
- `DELETE /suppliers/{id}` — `{"ok": true, "id": ...}`

Field names and enums must match `docs/Project_Contexts/SupplierDirectory_TinyDb_API.md`.
