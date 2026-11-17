"""PDF to Markdown via MarkItDown, before any agent reads the document."""

from __future__ import annotations

import re

from .errors import ConversionError
from .paths import absolute_pdf_path


def convert_pdf(ticket_id: str) -> str:
    path = absolute_pdf_path(ticket_id)
    if not path.is_file():
        raise ConversionError("missing_pdf")
    try:
        from markitdown import MarkItDown

        result = MarkItDown().convert(str(path))
        text = (result.text_content or "").strip()
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(type(exc).__name__) from exc
    if not text:
        raise ConversionError("empty_text")
    text = re.sub(r"\(cid:\d+\)", "- ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()
