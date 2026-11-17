"""Locations for intake artifacts. Uploaded PDFs stay under data/raw/rfp/."""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MAX_PDF_BYTES = 15 * 1024 * 1024


def raw_dir() -> Path:
    override = os.getenv("RFP_RAW_DIR", "").strip()
    if override:
        return Path(override)
    return REPO_ROOT / "data" / "raw" / "rfp"


def sanitize_filename(name: str) -> str:
    base = Path(name or "upload.pdf").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:80].strip("._")
    if not cleaned:
        cleaned = "upload.pdf"
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf"
    return cleaned


def relative_pdf_path(ticket_id: str) -> str:
    return f"data/raw/rfp/{ticket_id}.pdf"


def absolute_pdf_path(ticket_id: str) -> Path:
    return raw_dir() / f"{ticket_id}.pdf"
