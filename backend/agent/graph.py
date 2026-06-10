"""LangGraph graph definition and compilation.

Phase 3+: implement ``build_graph() -> CompiledGraph`` that wires every node
(validate → preprocess → decide_cluster → [cluster] → describe_patches →
synthesize → retrieve → classify → [retry/clip_fallback] → store → format) and
all conditional edges from ``edges.py``. Compiled exactly once at app startup
and stored on ``app.state.graph`` — never recompiled per request (CLAUDE.md §8).
"""
