"""Domain types — the canonical data structures used by the agent, storage, and
API layers.

These are the single source of truth for field shapes. The API layer
(``api/schemas.py``) builds its HTTP request/response contract on top of these,
adding transport concerns (multipart-form parsing, error envelopes). Datetimes
are timezone-aware UTC ``datetime`` objects; Pydantic serializes them to ISO-8601
on the wire (§5.2).

See ARCHITECTURE.md §4.2 (state), §5.2 (payload), §6.3 (responses), §2.1 (validation).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────── Internal types ────────────────────────────


class PatchData(BaseModel):
    """One image patch produced by preprocessing. Internal only — flows through
    agent state and is never serialized to clients."""

    image_bytes: bytes
    row: int  # grid row in the source image
    col: int  # grid column in the source image
    index: int  # unique patch index


class RetrievedAnalysis(BaseModel):
    """A full prior-analysis record returned by the ``retrieve`` node and held in
    agent state. Carries the full description and similarity score; the
    ``format`` node compacts it into a :class:`RetrievedContext` for the API."""

    analysis_id: str
    score: float | None = None  # cosine similarity from Qdrant search
    timestamp: datetime
    lat: float
    lon: float
    distance_km: float | None = None
    predicted_class: str
    confidence: int
    vllm_description: str
    reasoning: str

    def to_context(self, snippet_len: int = 240) -> "RetrievedContext":
        """Compact this record into the API-facing card form (snippet, not full text)."""
        snippet = self.vllm_description.strip()
        if len(snippet) > snippet_len:
            snippet = snippet[: snippet_len - 1].rstrip() + "…"
        return RetrievedContext(
            analysis_id=self.analysis_id,
            timestamp=self.timestamp,
            lat=self.lat,
            lon=self.lon,
            distance_km=self.distance_km,
            predicted_class=self.predicted_class,
            confidence=self.confidence,
            description_snippet=snippet,
            reasoning=self.reasoning,
        )


# ─────────────────────────── API-facing types ──────────────────────────


class RetrievedContext(BaseModel):
    """A compact prior-analysis card surfaced in responses and on /history (§6.3.1).

    ``analysis_id`` is included (beyond the fields named in §6.3.1) because the
    Archive page needs it to fetch the full detail view via
    ``GET /analyses/{analysis_id}`` (§6.3.4)."""

    analysis_id: str
    timestamp: datetime
    lat: float
    lon: float
    distance_km: float | None = None
    predicted_class: str
    confidence: int = Field(ge=0, le=5)
    description_snippet: str
    reasoning: str


class AnalyzeRequest(BaseModel):
    """Validated, parsed analysis inputs (the non-binary fields; image bytes are
    carried separately). Mirrors the validation contract in §2.1 so malformed
    requests fail with a 400 before the graph runs."""

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    class_list: list[str]
    class_descriptions: dict[str, str] | None = None
    retrieval_radius_km: float = Field(default=5.0, ge=0.1, le=100)
    retrieval_time_window_days: int | None = Field(default=None, ge=1)
    timestamp: datetime | None = None

    @field_validator("class_list")
    @classmethod
    def _normalize_class_list(cls, value: list[str]) -> list[str]:
        cleaned = [c.strip() for c in value if c and c.strip()]
        if len(cleaned) < 2:
            raise ValueError("class_list must contain at least 2 non-empty classes")
        if len(cleaned) > 50:
            raise ValueError("class_list must contain at most 50 classes")
        seen: set[str] = set()
        for c in cleaned:
            key = c.lower()
            if key in seen:
                raise ValueError(f"class_list contains a duplicate class: {c!r}")
            seen.add(key)
        return cleaned


class AnalyzeResponse(BaseModel):
    """The synchronous /analyze response and the SSE ``complete`` payload (§6.3.1)."""

    analysis_id: str
    predicted_class: str
    confidence: int = Field(ge=0, le=5)
    reasoning: str
    synthesized_description: str
    retrieved_context: list[RetrievedContext] = Field(default_factory=list)
    used_clustering: bool = False
    used_retry: bool = False
    used_clip_fallback: bool = False
    alternative_classes: list[str] | None = None  # populated when confidence < 4


class FullAnalysisResponse(AnalyzeResponse):
    """The /analyses/{id} detail response: everything in AnalyzeResponse plus the
    stored provenance and pipeline metadata that drives the Pipeline Trace
    section (§6.3.4, DESIGN.md §10)."""

    timestamp: datetime
    lat: float
    lon: float
    class_list: list[str]
    image_ref: str | None = None
    image_url: str | None = None
    was_tiled: bool = False
    num_patches: int = 1
    patch_descriptions: list[str] = Field(default_factory=list)
    clustering_strategy: str = "none"
    ambiguity_reason: str | None = None
    vllm_model: str | None = None
    llm_model: str | None = None
    embedding_model: str | None = None


class HealthResponse(BaseModel):
    """`GET /health` self-report (§6.3.5)."""

    status: str  # "ok" | "degraded"
    qdrant: str  # "ok" | "unreachable"
    vllm_model: str
    llm_model: str
    embedding_model: str
