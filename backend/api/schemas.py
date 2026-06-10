"""API boundary: the HTTP request/response contract for the FastAPI routes.

Response models are the domain models from ``models/types.py`` (re-exported here
so route handlers have a single, obvious import site, and to avoid schema drift
between layers). The API-only concerns live here: the error envelope (§6.2),
confidence-tier mapping for /history (§6.3.3), and defensive parsing of the
multipart-form fields that can't be expressed as a single Pydantic body —
``class_list`` arrives JSON-encoded or comma-separated; ``class_descriptions``
arrives JSON-encoded (CLAUDE.md §9).
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel

from models.types import (
    AnalyzeRequest,
    AnalyzeResponse,
    FullAnalysisResponse,
    HealthResponse,
    RetrievedContext,
)

__all__ = [
    "AnalyzeRequest",
    "AnalyzeResponse",
    "FullAnalysisResponse",
    "HealthResponse",
    "RetrievedContext",
    "ErrorResponse",
    "ConfidenceTier",
    "confidence_range_for_tier",
    "parse_class_list",
    "parse_class_descriptions",
    "build_analyze_request",
]


# ─────────────────────────── Error envelope ────────────────────────────


class ErrorResponse(BaseModel):
    """Consistent error body for the global exception handler (§6.2)."""

    error: str
    details: str | None = None


# ───────────────────── /history confidence tiers ───────────────────────

ConfidenceTier = Literal["all", "high", "medium", "low"]

# Inclusive (min, max) integer ranges; None means no bound on that side.
_TIER_RANGES: dict[str, tuple[int | None, int | None]] = {
    "all": (None, None),
    "high": (4, 5),
    "medium": (3, 3),
    "low": (1, 2),
}


def confidence_range_for_tier(tier: str | None) -> tuple[int | None, int | None]:
    """Map a confidence tier label to an inclusive integer range for Qdrant filters."""
    if not tier:
        return (None, None)
    return _TIER_RANGES.get(tier.lower(), (None, None))


# ─────────────────── multipart form-field parsing ──────────────────────


def parse_class_list(raw: str | None) -> list[str]:
    """Parse the ``class_list`` form field, which may be a JSON array string or a
    comma-separated string. Returns the raw list (trimming/validation happens in
    :class:`AnalyzeRequest`)."""
    text = (raw or "").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass  # fall through to comma-separated parsing
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_class_descriptions(raw: str | None) -> dict[str, str] | None:
    """Parse the optional ``class_descriptions`` JSON-encoded dict form field."""
    text = (raw or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"class_descriptions must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("class_descriptions must be a JSON object")
    return {str(key): str(value) for key, value in parsed.items()}


def build_analyze_request(
    *,
    lat: float,
    lon: float,
    class_list: str | None,
    class_descriptions: str | None = None,
    retrieval_radius_km: float | None = 5.0,
    retrieval_time_window_days: int | None = None,
) -> AnalyzeRequest:
    """Assemble a validated :class:`AnalyzeRequest` from raw multipart-form fields.

    Pydantic validation errors propagate to the global handler as HTTP 400 (§6.3.1).
    """
    return AnalyzeRequest(
        lat=lat,
        lon=lon,
        class_list=parse_class_list(class_list),
        class_descriptions=parse_class_descriptions(class_descriptions),
        retrieval_radius_km=retrieval_radius_km if retrieval_radius_km is not None else 5.0,
        retrieval_time_window_days=retrieval_time_window_days,
    )
