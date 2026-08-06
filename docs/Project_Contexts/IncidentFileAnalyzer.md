# Company Incident File Analyzer

**Company:** HealthCore — Outpatient Healthcare Network  
**Unit:** HealthCore Digital  
**Document type:** Assignment CONTEXT (field names, categories, statuses, and expected values for verification)

This CONTEXT is the single source of truth for the Incident File Analyzer. Field names, categories, statuses, and expected values used by the script, API, and UI must match this document exactly.

---

## Invalid records

Real-world data always has problems. For this project, a record is considered invalid if it is missing at least one of the required fields defined in this CONTEXT, or if it contains a value in a field that is not within the allowed set (statuses and categories). The logic must detect them, count them, and exclude them from the main analysis — but never silently ignore them.

Invalid records must be classified by problem type (for example: missing required field, status not in allowed set, category not in allowed set) and reported with counts.

---

## CSV contract

### Required fields

| Field | Description |
|-------|-------------|
| `incident_id` | Unique incident identifier |
| `reported_date` | Date the incident was reported |
| `category` | Incident category (must be in the allowed set below) |
| `status` | Incident status (must be in the allowed set below) |
| `location_id` | Clinic / location identifier |

### Optional fields

| Field | Description |
|-------|-------------|
| `satisfaction_score` | Satisfaction index when recorded; used only for closed cases that have a score |

### Allowed statuses

- `open`
- `closed`
- `discarded`

### Allowed categories

- `clinical_safety`
- `facilities`
- `it_systems`
- `billing_access`
- `patient_experience`
- `workforce`

### Sample input

CLI example (maps the generic `incidents-COMPANY.csv` pattern):

```bash
python analyze.py incidents-healthcore.csv
```

---

## What You Need to Do

### Phase 1 — Analysis script (`/scripts`)

Create a main script named `analyze.py` that accepts a path to a CSV file as a command-line argument:

```bash
python analyze.py incidents-healthcore.csv
```

The script must:

1. **Load** the CSV using native Python reading or pandas.
2. **Validate** records per this CONTEXT: detect and count invalid records, detailing how many there are and why (missing fields, out-of-range / disallowed values).
3. **Calculate metrics on valid records only:**
   - Total elements processed (separate counts for valid and invalid).
   - Breakdown by incident category.
   - Breakdown by status (`open`, `closed`, `discarded`).
   - Average satisfaction index for closed cases that have a recorded score.
4. **Print** a readable summary to the console with separators, clear labels, and alignment.
5. **Prompt** the user: `export results to CSV? (y / n)`. If `y`, save results to `results.csv` with one row per metric.
6. **Verify** that results match the expected values defined in this CONTEXT (see Expected values below).

### Phase 2 — Integration into the platform

Extract the script logic into reusable services and integrate them into the system. Analysis and validation logic must be **shared** between the script and the API (not duplicated). Code must follow the monorepo folder structure.

#### Backend (`/services/api`)

- Create `POST /api/incidents/analyze` accepting a CSV file as `multipart/form-data` and returning the summary as JSON.
- Create `GET /api/incidents/results/export` that returns the last analysis as a downloadable CSV.
- Implement error handling for empty files or incorrect formats, returning appropriate HTTP responses with descriptive messages.

#### Frontend (`/src/web`)

- Create an Incident analysis page in the application menu.
- Include a file upload component (drag & drop or file selector).
- Display the results summary: general metrics, category breakdown, status breakdown, and satisfaction index.
- Include a button to download results as a CSV.
- Inform the user if the file contains invalid records and show the count for each type.

---

## What we will evaluate

### Script

- Accepts CSV path as an argument without code modification.
- Correctly detects, classifies, and shows invalid records with their problem type.
- Displays all five required metrics in the console in a readable format.
- CSV export works and is well-structured.
- Results match the expected values in this CONTEXT.

### Backend

- Analysis endpoint accepts CSV, processes it, and returns JSON summary.
- Export endpoint returns a correctly formatted downloadable CSV.
- Input errors return appropriate HTTP status codes.

### Frontend

- Files can be uploaded via the UI without the terminal.
- The summary is displayed clearly and interpretably.
- The export button successfully downloads the CSV.
- Invalid records are communicated to the user clearly.

### Cross-cutting

- Analysis and validation logic is shared between the script and API (not duplicated).
- The code is organized according to a monorepo folder structure.

---

## Expected values

Verified against sample file [`scripts/samples/incidents-healthcore.csv`](../../scripts/samples/incidents-healthcore.csv):

| Metric | Value |
|--------|-------|
| Total processed | 20 |
| Valid | 16 |
| Invalid | 4 |
| Avg satisfaction (closed with score) | 3.75 |
| Closed cases with score | 6 |

**Invalid by problem type**

| Type | Count |
|------|-------|
| `missing_required_field` | 2 |
| `category_not_allowed` | 1 |
| `status_not_allowed` | 1 |

**By category (valid only)**

| Category | Count |
|----------|-------|
| `billing_access` | 3 |
| `clinical_safety` | 2 |
| `facilities` | 3 |
| `it_systems` | 3 |
| `patient_experience` | 3 |
| `workforce` | 2 |

**By status (valid only)**

| Status | Count |
|--------|-------|
| `closed` | 7 |
| `discarded` | 3 |
| `open` | 6 |

---

## How to run

Run all commands from the monorepo root unless a `cd` is shown.

### CLI (Phase 1)

Requires Python 3.10+.

```bash
python scripts/analyze.py scripts/samples/incidents-healthcore.csv
```

1. The script prints the analysis summary (totals, invalid-by-type, category/status breakdowns, average satisfaction).
2. When prompted `export results to CSV? (y / n)`, type `y` to write `results.csv` in the current working directory, or `n` to skip.
3. Pass any other CSV path as the only argument (no code changes needed).

Example with your own file:

```bash
python scripts/analyze.py path/to/incidents-healthcore.csv
```

### Frontend (Phase 2 UI + API)

The backoffice page calls the FastAPI service. Start the API first, then the UI.

**1. Start the Incident Analyzer API** (port `8001` — use this if `8000` is already taken):

```bash
cd services/api
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

Leave this terminal running. Health check: http://localhost:8001/health  
You should see `{"status":"ok"}`. If that URL fails, the UI upload will show **Failed to fetch**.

**2. Start the backoffice frontend** (port `3001`):

```bash
cd uis/backoffice
npm install
npm run dev
```

**3. Open the Incident analysis page**

- Browser: http://localhost:3001/incidents
- Upload `scripts/samples/incidents-healthcore.csv` (drag-and-drop or file picker).
- Review the summary (metrics, invalid counts, category/status breakdowns).
- Use **Download results CSV** to fetch the last analysis from `GET /api/incidents/results/export`.

Optional: override the API base URL (must match the uvicorn port):

```bash
# Windows PowerShell
$env:NEXT_PUBLIC_INCIDENTS_API_URL="http://localhost:8001"
npm run dev
```

Default API URL (if unset): `http://localhost:8001`.
