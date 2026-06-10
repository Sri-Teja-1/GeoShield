"""clip_fallback node.

Phase 4: call ``services/clip.py`` for zero-shot classification against the
class list, set ``confidence = 2`` and ``used_clip_fallback = True``. Fires when
the LLM path bottoms out (confidence <= 1, or <= 2 after retry). See
ARCHITECTURE.md §2.9.
"""
