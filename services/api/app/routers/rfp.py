"""RFP intake routes on the existing HealthCore API. The graph lives in data/pipelines."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.deps.auth import get_current_user

logger = logging.getLogger(__name__)


def _ensure_repo_on_path() -> None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "data" / "pipelines" / "rfp_intake").is_dir():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return


_ensure_repo_on_path()
from data.pipelines.rfp_intake import service as rfp_service  # noqa: E402

router = APIRouter(prefix="/rfp", tags=["rfp"])

_UPLOAD_MESSAGES = {
    "not_pdf": "Upload a PDF request for proposal.",
    "too_large": "That PDF is too large. The limit is 15 MB.",
    "empty": "That PDF is empty.",
}


class TicketAccepted(BaseModel):
    ticket_id: str
    status: str


class SectionOut(BaseModel):
    department_id: str
    owner_name: str = ""
    owner_role: str = ""
    key_aspects: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    contains_phi: bool = False
    draft_content: str = ""
    draft_withheld: bool = False
    review_state: str = ""
    provisional: bool = False
    evaluation: dict | None = None


class MetadataOut(BaseModel):
    client_name: str = ""
    client_country: str = ""
    program_type: str = ""
    covered_population: int | None = None
    deadline: str = ""
    budget_range: str = ""
    currency: str = ""
    departments_needed: list[str] = Field(default_factory=list)
    flesch_reading_ease: float | None = None
    flesch_kincaid_grade: float | None = None
    gunning_fog: float | None = None
    word_count: int = 0
    estimated_tokens: int = 0
    cost_band: str = ""
    open_questions: list[str] = Field(default_factory=list)
    readability_note: str = ""


class TicketSummary(BaseModel):
    ticket_id: str
    rfp_id: str | None = None
    status: str
    original_filename: str = ""
    phi_detected: bool = False
    handoff_ready: bool = False
    discard_reason_code: str | None = None
    discard_message: str = ""
    pipeline_error_code: str | None = None
    pipeline_message: str = ""
    client_name: str = ""
    client_country: str = ""
    part2_outcome: str = ""
    created_at: str
    updated_at: str


class TicketDetail(TicketSummary):
    pdf_stored: bool = False
    metadata: MetadataOut | None = None
    sections: list[SectionOut] = Field(default_factory=list)
    sales_summary: str = ""
    conflicts: list[dict] = Field(default_factory=list)
    part2_guard: str = ""
    part2_outcome: str = ""
    evaluation_closed: bool = False
    status_trail: list[str] = Field(default_factory=list)


class TicketList(BaseModel):
    tickets: list[TicketSummary]


def init_rfp_storage() -> None:
    try:
        rfp_service.init_schema()
    except Exception:
        logger.warning("rfp schema init skipped")


def _storage_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="RFP intake storage is not available. Please try again later.",
    )


@router.post("/tickets", response_model=TicketAccepted, status_code=status.HTTP_202_ACCEPTED)
async def create_ticket(
    file: UploadFile = File(...),
    _user: dict = Depends(get_current_user),
) -> TicketAccepted:
    content = await file.read()
    try:
        ticket_id = rfp_service.accept_upload(file.filename or "upload.pdf", content)
    except rfp_service.UploadRejected as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_UPLOAD_MESSAGES.get(exc.code, _UPLOAD_MESSAGES["not_pdf"]),
        ) from None
    except rfp_service.RfpDatabaseUnconfigured:
        raise _storage_unavailable() from None
    except rfp_service.RfpStorageError:
        raise _storage_unavailable() from None
    return TicketAccepted(ticket_id=ticket_id, status="analyzing")


@router.get("/tickets", response_model=TicketList)
def list_tickets(_user: dict = Depends(get_current_user)) -> TicketList:
    try:
        rows = rfp_service.list_tickets()
    except rfp_service.RfpDatabaseUnconfigured:
        raise _storage_unavailable() from None
    except rfp_service.RfpStorageError:
        raise _storage_unavailable() from None
    return TicketList(tickets=[TicketSummary(**row) for row in rows])


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: str, _user: dict = Depends(get_current_user)) -> TicketDetail:
    try:
        row = rfp_service.get_ticket(ticket_id)
    except rfp_service.RfpDatabaseUnconfigured:
        raise _storage_unavailable() from None
    except rfp_service.RfpStorageError:
        raise _storage_unavailable() from None
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That ticket was not found.")
    return TicketDetail(**row)


@router.post(
    "/tickets/{ticket_id}/reprocess",
    response_model=TicketAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def reprocess_ticket(ticket_id: str, _user: dict = Depends(get_current_user)) -> TicketAccepted:
    try:
        new_status = rfp_service.reprocess(ticket_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That ticket was not found.") from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ticket cannot be run again from its current status.",
        ) from None
    except rfp_service.RfpDatabaseUnconfigured:
        raise _storage_unavailable() from None
    except rfp_service.RfpStorageError:
        raise _storage_unavailable() from None
    return TicketAccepted(ticket_id=ticket_id, status=new_status)


@router.post(
    "/tickets/{ticket_id}/draft",
    response_model=TicketAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def draft_ticket(ticket_id: str, _user: dict = Depends(get_current_user)) -> TicketAccepted:
    try:
        new_status = rfp_service.start_draft(ticket_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="That ticket was not found.") from None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ticket is not ready for a proposal draft.",
        ) from None
    except rfp_service.RfpDatabaseUnconfigured:
        raise _storage_unavailable() from None
    except rfp_service.RfpStorageError:
        raise _storage_unavailable() from None
    return TicketAccepted(ticket_id=ticket_id, status=new_status)
