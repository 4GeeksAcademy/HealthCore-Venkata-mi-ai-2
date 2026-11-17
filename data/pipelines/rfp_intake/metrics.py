"""Readability metrics used as a processing-cost signal, not a literary grade."""

from __future__ import annotations

import os
import re
from typing import Any

from .paths import REPO_ROOT

_NLTK_DIR = REPO_ROOT / "data" / "process" / "nltk_data"
_WORD = re.compile(r"[A-Za-z0-9']+")


def _ensure_punkt() -> bool:
    try:
        import nltk
    except ImportError:
        return False
    os.environ.setdefault("NLTK_DATA", str(_NLTK_DIR))
    if str(_NLTK_DIR) not in nltk.data.path:
        nltk.data.path.append(str(_NLTK_DIR))
    try:
        nltk.data.find("tokenizers/punkt_tab/english/")
        return True
    except LookupError:
        pass
    try:
        _NLTK_DIR.mkdir(parents=True, exist_ok=True)
        nltk.download("punkt_tab", download_dir=str(_NLTK_DIR), quiet=True)
        nltk.data.find("tokenizers/punkt_tab/english/")
        return True
    except Exception:
        return False


def _cost_band(tokens: int, fog: float | None) -> str:
    if tokens >= 8000 or (fog is not None and fog >= 17):
        return "high"
    if tokens >= 2000 or (fog is not None and fog >= 12):
        return "medium"
    return "low"


def measure(text: str) -> dict[str, Any]:
    words = _WORD.findall(text or "")
    word_count = len(words)
    estimated_tokens = max(1, (len(text or "") + 3) // 4) if text else 0
    metrics: dict[str, Any] = {
        "word_count": word_count,
        "estimated_tokens": estimated_tokens,
        "flesch_reading_ease": None,
        "flesch_kincaid_grade": None,
        "gunning_fog": None,
        "cost_band": _cost_band(estimated_tokens, None),
        "readability_note": "",
    }
    if word_count < 30 or not _ensure_punkt():
        metrics["readability_note"] = (
            "Grade indexes were not computed. The cost band uses document length only."
        )
        metrics["cost_band"] = _cost_band(estimated_tokens, None)
        return metrics
    try:
        from readability import Readability

        scores = Readability(text)
        ease = scores.flesch()
        grade = scores.flesch_kincaid()
        fog = scores.gunning_fog()
        metrics["flesch_reading_ease"] = round(float(ease.score), 2)
        metrics["flesch_kincaid_grade"] = round(float(grade.score), 2)
        metrics["gunning_fog"] = round(float(fog.score), 2)
    except Exception:
        metrics["readability_note"] = (
            "Grade indexes were not computed. The cost band uses document length only."
        )
        metrics["cost_band"] = _cost_band(estimated_tokens, None)
        return metrics
    fog_value = metrics["gunning_fog"]
    metrics["cost_band"] = _cost_band(estimated_tokens, fog_value)
    metrics["readability_note"] = (
        f"Processing cost band: {metrics['cost_band']}. "
        f"About {estimated_tokens} tokens. "
        f"Gunning Fog {fog_value}."
    )
    return metrics
