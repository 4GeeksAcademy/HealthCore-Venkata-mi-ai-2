"""Centralized incident manager and CSV analysis HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app import incidents_store
from app.core.errors import StorageError
from app.deps.auth import get_current_user
from app.incident_analysis import AnalysisError, analyze_rows, parse_csv_rows
from app.models.incidents import (
    IncidentAnalyzeResponse,
    IncidentBranch,
    IncidentCategory,
    IncidentCreate,
    IncidentListResponse,
    IncidentOrigin,
    IncidentRecord,
    IncidentStatus,
    IncidentStatusUpdate,
    IncidentSummaryResponse,
)
from app.result_store import store

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

_SAFE_ANALYSIS_DETAILS = frozenset(
    {
        "File is empty.",
        "CSV has no header row.",
        "CSV contains no data rows.",
    }
)


def _analysis_detail(exc: AnalysisError) -> str:
    message = str(exc)
    if message in _SAFE_ANALYSIS_DETAILS or message.startswith("Incorrect CSV format:"):
        return message
    return "Could not analyze this file. Check the CSV format and try again."


def _field_error(field: str, message: str) -> HTTPException:
    return HTTPException(status_code=400, detail={"field": field, "message": message})


@router.post("/analyze", response_model=IncidentAnalyzeResponse)
async def analyze_incidents(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
) -> IncidentAnalyzeResponse:
    """CSV metrics only — does not write to the incident manager store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    name = file.filename.lower()
    if not name.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Incorrect format: upload a .csv file.",
        )

    try:
        raw = await file.read()
    except OSError as exc:
        raise HTTPException(
            status_code=400,
            detail="Could not read the uploaded file.",
        ) from exc
    if not raw:
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="Incorrect format: file must be UTF-8 encoded CSV.",
        ) from exc

    try:
        rows = parse_csv_rows(text)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=_analysis_detail(exc)) from exc

    result = analyze_rows(rows)
    store.save(result)
    return IncidentAnalyzeResponse.model_validate(result.to_dict())


@router.post("", response_model=IncidentRecord, status_code=201)
def create_incident(body: IncidentCreate, _: dict = Depends(get_current_user)) -> IncidentRecord:
    title = body.title.strip()
    description = body.description.strip()
    if not title:
        raise _field_error("title", "Please enter a title for this incident.")
    if not description:
        raise _field_error("description", "Please enter a description for this incident.")
    if body.status not in {"open", "in_progress"}:
        raise _field_error(
            "status",
            "New incidents must start as open or in_progress.",
        )
    try:
        return incidents_store.create_incident(
            title=title,
            description=description,
            category=body.category,
            status=body.status,
            origin=body.origin,
            branch=body.branch,
        )
    except ValueError as exc:
        field = str(exc)
        raise _field_error(field, f"The {field} value is not allowed.") from exc
    except StorageError:
        raise HTTPException(status_code=500, detail="Unable to save this incident. Try again.")


@router.get("/summary", response_model=IncidentSummaryResponse)
def incident_summary(_: dict = Depends(get_current_user)) -> IncidentSummaryResponse:
    try:
        data = incidents_store.summarize_incidents()
    except StorageError:
        raise HTTPException(status_code=500, detail="Unable to load incident summary. Try again.")
    return IncidentSummaryResponse.model_validate(data)


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status: IncidentStatus | None = None,
    origin: IncidentOrigin | None = None,
    branch: IncidentBranch | None = None,
    category: IncidentCategory | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    _: dict = Depends(get_current_user),
) -> IncidentListResponse:
    try:
        total, items = incidents_store.list_incidents(
            status=status,
            origin=origin,
            branch=branch,
            category=category,
            limit=limit,
        )
    except StorageError:
        raise HTTPException(status_code=500, detail="Unable to load incidents. Try again.")
    return IncidentListResponse(total=total, items=items)


@router.patch("/{incident_id}/status", response_model=IncidentRecord)
def update_incident_status(
    incident_id: str,
    body: IncidentStatusUpdate,
    _: dict = Depends(get_current_user),
) -> IncidentRecord:
    try:
        return incidents_store.update_incident_status(incident_id.strip(), body.status)
    except KeyError:
        raise HTTPException(status_code=404, detail="Incident not found.")
    except incidents_store.InvalidTransitionError as exc:
        raise _field_error("status", exc.message) from exc
    except ValueError:
        raise _field_error("status", "That status value is not allowed.")
    except StorageError:
        raise HTTPException(status_code=500, detail="Unable to update this incident. Try again.")


@router.get(
    "/results/export",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
async def export_results(_: dict = Depends(get_current_user)) -> Response:
    """CSV download of the last analysis — metrics only."""
    csv_body = store.get_csv()
    if csv_body is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis results available. Upload a CSV first.",
        )
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="results.csv"',
        },
    )


@router.get("/{incident_id}", response_model=IncidentRecord)
def get_incident(incident_id: str, _: dict = Depends(get_current_user)) -> IncidentRecord:
    try:
        record = incidents_store.get_incident(incident_id.strip())
    except StorageError:
        raise HTTPException(status_code=500, detail="Unable to load this incident. Try again.")
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return record
