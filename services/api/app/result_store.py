"""In-memory store for the last successful incident analysis."""

from __future__ import annotations

from typing import Any

from app.incident_analysis import AnalysisResult, results_to_csv_string


class ResultStore:
    def __init__(self) -> None:
        self._summary: dict[str, Any] | None = None
        self._csv: str | None = None

    def save(self, result: AnalysisResult) -> None:
        self._summary = result.to_dict()
        self._csv = results_to_csv_string(result)

    def get_summary(self) -> dict[str, Any] | None:
        return self._summary

    def get_csv(self) -> str | None:
        return self._csv


store = ResultStore()
