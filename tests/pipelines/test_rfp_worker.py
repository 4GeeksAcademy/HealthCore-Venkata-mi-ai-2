"""Revenue worker must not invent a headcount that is absent from the extract."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from data.pipelines.rfp_intake.agents import run_worker


def test_revenue_worker_drops_invented_population() -> None:
    metadata = {
        "client_name": "Meridian Manufacturing",
        "client_country": "US",
        "program_type": "occupational_health",
        "covered_population": None,
        "deadline": "August 23, 2026",
        "budget_range": "",
        "currency": "USD",
        "open_questions": [],
    }
    extract = "Pricing is requested for an on-site clinic. No headcount is in this passage."

    def complete(system: str, user: str) -> dict:
        assert "WORKER" in system
        assert "revenue" in user
        assert "9000" not in user
        return {
            "key_aspects": ["Cover 9000 people under a fixed fee."],
            "open_questions": [],
            "claims": {
                "client_country": "US",
                "covered_population": 9000,
                "budget_range": None,
                "currency": "USD",
            },
            "contains_phi": False,
        }

    section = run_worker("revenue", metadata, extract, complete=complete)
    blob = " ".join(section["key_aspects"])
    assert "9000" not in blob
    assert section["claims"]["covered_population"] is None
    assert section["owner_name"] == "Tom Callahan"
    assert any("budget" in question.lower() for question in section["open_questions"])
    assert any("figure" in question.lower() or "population" in question.lower() for question in section["open_questions"])
