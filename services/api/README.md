# HealthCore Incident Analyzer API

FastAPI service for CSV incident analysis (shared with `scripts/analyze.py`).

## Run

```bash
cd services/api
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

## Endpoints

- `POST /api/incidents/analyze` — multipart CSV upload → JSON summary
- `GET /api/incidents/results/export` — last analysis as `results.csv`
- `GET /health` — liveness
