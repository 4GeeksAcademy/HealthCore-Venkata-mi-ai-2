"""Classifier decisions for HealthCore RFPs. No live model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from data.pipelines.rfp_intake.agents import classify_document, decision_from_model
from data.pipelines.rfp_intake.errors import ModelUnavailable


def test_formal_buyer_is_accepted() -> None:
    accepted, code = decision_from_model(
        {
            "is_rfp": True,
            "reason_code": "institutional_request",
            "client_role": "buyer",
            "rationale": "An employer asked for a proposal.",
        }
    )
    assert accepted is True
    assert code == "institutional_request"


def test_informal_buyer_is_accepted() -> None:
    accepted, code = decision_from_model(
        {
            "is_rfp": True,
            "reason_code": "institutional_request",
            "client_role": "buyer",
            "rationale": "A university email asked for a proposal.",
        }
    )
    assert accepted is True
    assert code == "institutional_request"


def test_vendor_pitch_is_discarded() -> None:
    accepted, code = decision_from_model(
        {
            "is_rfp": False,
            "reason_code": "vendor_pitch",
            "client_role": "seller",
            "rationale": "A vendor is selling an EHR to HealthCore.",
        }
    )
    assert accepted is False
    assert code == "vendor_pitch"


def test_seller_flag_discards_even_if_marked_rfp() -> None:
    accepted, code = decision_from_model(
        {"is_rfp": True, "reason_code": "institutional_request", "client_role": "seller"}
    )
    assert accepted is False
    assert code == "vendor_pitch"


def test_uncertain_is_discarded_not_accepted() -> None:
    accepted, code = decision_from_model(
        {"is_rfp": False, "reason_code": "uncertain", "client_role": "unknown"}
    )
    assert accepted is False
    assert code == "uncertain"


def test_patient_record_is_discarded() -> None:
    accepted, code = decision_from_model(
        {"is_rfp": False, "reason_code": "patient_record", "client_role": "unknown"}
    )
    assert accepted is False
    assert code == "patient_record"


def test_classify_reads_model_json() -> None:
    def complete(system: str, user: str) -> dict:
        assert "CLASSIFIER" in system
        assert "Meridian" in user
        return {
            "is_rfp": True,
            "reason_code": "institutional_request",
            "client_role": "buyer",
            "rationale": "Employer request.",
        }

    accepted, code = classify_document(
        "Meridian Manufacturing requests a proposal.",
        complete=complete,
    )
    assert accepted is True
    assert code == "institutional_request"


def test_classifier_outage_is_not_a_discard() -> None:
    def complete(system: str, user: str) -> dict:
        raise ModelUnavailable("RuntimeError")

    with pytest.raises(ModelUnavailable):
        classify_document("Meridian Manufacturing requests a proposal.", complete=complete)
