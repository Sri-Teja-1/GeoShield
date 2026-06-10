"""Agent state schema.

A single flat ``TypedDict`` that flows through every node; nodes return partial
updates that LangGraph merges into the global state. Two fields carry
``operator.add`` reducers so the parallel ``describe_single_patch`` fan-out and
any node can append without clobbering concurrent writes (ARCHITECTURE.md §4.2,
CLAUDE.md §8).

Downstream nodes classify against ``effective_class_list`` (set by clustering, or
defaulted to ``class_list``), never ``class_list`` directly.
"""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Literal, Optional, TypedDict

from models.types import AnalyzeResponse, PatchData, RetrievedAnalysis

ClusteringStrategy = Literal["none", "flat", "hierarchical_d1", "hierarchical_d2"]


class AgentState(TypedDict, total=False):
    # ── Inputs (set at validation, never modified after) ────────────────
    image_bytes: bytes
    image_hash: str
    lat: float
    lon: float
    timestamp: datetime
    class_list: list[str]
    class_list_hash: str
    class_descriptions: Optional[dict[str, str]]
    retrieval_radius_km: float
    retrieval_time_window_days: Optional[int]
    analysis_id: str

    # ── Preprocessing ───────────────────────────────────────────────────
    processed_patches: Optional[list[PatchData]]
    was_tiled: bool
    num_patches: int

    # ── Clustering ──────────────────────────────────────────────────────
    clustering_strategy: ClusteringStrategy
    class_hierarchy: Optional[dict]
    effective_class_list: list[str]

    # ── vLLM (patch description + synthesis) ────────────────────────────
    # operator.add reducer: parallel patch workers append concurrently.
    patch_descriptions: Annotated[list[str], operator.add]
    synthesized_description: str

    # ── RAG retrieval ───────────────────────────────────────────────────
    retrieved_context: list[RetrievedAnalysis]
    retrieval_relaxation_applied: list[str]

    # ── Classification ──────────────────────────────────────────────────
    predicted_class: Optional[str]
    confidence: Optional[int]
    reasoning: Optional[str]
    alternative_classes: Optional[list[str]]
    ambiguity_reason: Optional[str]

    # ── Pipeline metadata ───────────────────────────────────────────────
    used_retry: bool
    used_clip_fallback: bool
    used_clustering: bool
    # operator.add reducer: any node may append a non-fatal error.
    pipeline_errors: Annotated[list[str], operator.add]

    # ── Output ──────────────────────────────────────────────────────────
    final_result: Optional[AnalyzeResponse]


if __name__ == "__main__":
    # Sanity: confirm the reducer annotations resolve the way LangGraph reads them.
    # Because of `from __future__ import annotations` the raw __annotations__ are
    # strings; get_type_hints(include_extras=True) resolves them to real Annotated
    # types (exactly what LangGraph's StateGraph does to discover reducers).
    from typing import get_type_hints

    hints = get_type_hints(AgentState, include_extras=True)
    for field in ("patch_descriptions", "pipeline_errors"):
        meta = getattr(hints[field], "__metadata__", ())
        assert operator.add in meta, f"{field} is missing its operator.add reducer"
    print(f"AgentState OK — {len(hints)} fields; reducers on patch_descriptions, pipeline_errors")
