"""Incident analysis and read-only incident lookup HTTP routes."""

from __future__ import annotations

from pathlib import PurePath

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app import incidents_store
from app.deps.auth import get_current_user
from app.incident_analysis import AnalysisError, analyze_rows, parse_csv_rows, valid_rows
from app.models.incidents import (
    IncidentAnalyzeResponse,
    IncidentCategory,
    IncidentListResponse,
    IncidentRecord,
    IncidentStatus,
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


@router.post("/analyze", response_model=IncidentAnalyzeResponse)
async def analyze_incidents(
    file: UploadFile = File(...),
    _: dict = Depends(get_current_user),
) -> IncidentAnalyzeResponse:
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
    incidents_store.upsert_incidents(valid_rows(rows), source_file=PurePath(file.filename).name[:120])
    return IncidentAnalyzeResponse.model_validate(result.to_dict())


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    status: IncidentStatus | None = None,
    category: IncidentCategory | None = None,
    clinic_id: str | None = Query(default=None, max_length=40),
    country: str | None = Query(default=None, max_length=4),
    limit: int = Query(default=50, ge=1, le=200),
    _: dict = Depends(get_current_user),
) -> IncidentListResponse:
    total, items = incidents_store.list_incidents(
        status=status, category=category, clinic_id=clinic_id, country=country, limit=limit
    )
    return IncidentListResponse(total=total, items=items)


@router.get(
    "/results/export",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
async def export_results(_: dict = Depends(get_current_user)) -> Response:
    """CSV download — documented exception: no JSON response_model."""
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
    record = incidents_store.get_incident(incident_id.strip().upper())
    if record is None:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return record
