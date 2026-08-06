"""Incident analysis HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.incident_analysis import AnalysisError, analyze_csv_text
from app.result_store import store

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/analyze")
async def analyze_incidents(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    name = file.filename.lower()
    if not name.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Incorrect format: upload a .csv file.",
        )

    raw = await file.read()
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
        result = analyze_csv_text(text)
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    store.save(result)
    return result.to_dict()


@router.get("/results/export")
async def export_results() -> Response:
    csv_body = store.get_csv()
    if csv_body is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No analysis results available. "
                "Upload a CSV via POST /api/incidents/analyze first."
            ),
        )
    return Response(
        content=csv_body,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="results.csv"',
        },
    )
