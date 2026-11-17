"""SQLModel tables for RFP tickets. Source of truth is Postgres, not TinyDB."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class RfpTicket(SQLModel, table=True):
    __tablename__ = "rfp_ticket"

    ticket_id: str = Field(primary_key=True)
    rfp_id: str | None = None
    status: str = Field(index=True)
    original_filename: str = ""
    raw_pdf_path: str = ""
    discard_reason_code: str | None = None
    phi_detected: bool = False
    pipeline_error_code: str | None = None
    handoff_ready: bool = False
    handoff_json: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime
    updated_at: datetime


class RfpMetadata(SQLModel, table=True):
    __tablename__ = "rfp_metadata"

    ticket_id: str = Field(primary_key=True, foreign_key="rfp_ticket.ticket_id")
    client_name: str = ""
    client_country: str = ""
    program_type: str = ""
    covered_population: int | None = None
    deadline: str = ""
    budget_range: str = ""
    currency: str = ""
    departments_needed: list = Field(default_factory=list, sa_column=Column(JSON))
    flesch_reading_ease: float | None = None
    flesch_kincaid_grade: float | None = None
    gunning_fog: float | None = None
    word_count: int = 0
    estimated_tokens: int = 0
    cost_band: str = ""
    open_questions: list = Field(default_factory=list, sa_column=Column(JSON))
    readability_note: str = ""


class RfpDepartmentSection(SQLModel, table=True):
    __tablename__ = "rfp_department_section"

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: str = Field(foreign_key="rfp_ticket.ticket_id", index=True)
    department_id: str
    owner_name: str
    owner_role: str
    key_aspects: list = Field(default_factory=list, sa_column=Column(JSON))
    open_questions: list = Field(default_factory=list, sa_column=Column(JSON))
    claims: dict = Field(default_factory=dict, sa_column=Column(JSON))
    contains_phi: bool = False
    draft_content: str | None = None
    evaluation_results: dict | None = Field(default=None, sa_column=Column(JSON))
    approval_status: str | None = None
    approver: str | None = None
    approved_at: datetime | None = None
