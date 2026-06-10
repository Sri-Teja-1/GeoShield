"""Analyze routes.

Phase 5: ``POST /analyze`` (sync, ``graph.ainvoke``) and ``POST /analyze/stream``
(SSE via ``graph.astream_events``). Both accept multipart/form-data, build the
initial state, and invoke the same compiled graph. SSE emits ``stage_update``
events per node and a final ``complete`` with the full AnalyzeResponse. See
CLAUDE.md §9 and ARCHITECTURE.md §6.
"""
