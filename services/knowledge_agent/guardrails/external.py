"""Isolate untrusted RAG and tool text so it is never treated as system instructions."""

from __future__ import annotations

import re
from typing import Any

_INJECTION_LINES = re.compile(
    r"(?im)^(?:\s*)(?:"
    r"ignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions?|rules?|prompts?)|"
    r"system\s*:"
    r"|you\s+are\s+now\b|"
    r"disregard\s+(?:your\s+)?(?:instructions?|rules?)|"
    r"new\s+instructions?\s*:"
    r").*$"
)

_ROLE_SPOOF = re.compile(
    r"(?im)^\s*(?:system|assistant|developer)\s*:\s*.*$"
)


def sanitize_external_text(text: str) -> str:
    """Strip common prompt-injection lines from retrieved or tool-sourced text."""
    body = text or ""
    body = _INJECTION_LINES.sub("[external content redacted]", body)
    body = _ROLE_SPOOF.sub("[external role label redacted]", body)
    return body.strip()


def isolate_context_block(chunks: list[dict[str, Any]]) -> str:
    """Format retrieved chunks as delimited untrusted data for the user message."""
    if not chunks:
        return "(no relevant passages were found in the knowledge base)"
    blocks: list[str] = []
    for n, item in enumerate(chunks, start=1):
        text = sanitize_external_text(str(item.get("text", "")))
        doc = item.get("source_document", "unknown")
        section = item.get("section", "")
        blocks.append(
            f"<retrieved_document index=\"{n}\" source=\"{doc}\" section=\"{section}\">\n"
            f"{text}\n"
            f"</retrieved_document>"
        )
    return "\n\n".join(blocks)
