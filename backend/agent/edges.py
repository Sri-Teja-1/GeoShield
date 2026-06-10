"""Conditional edge functions for the agent graph.

Phase 3/4: implement the routing functions referenced by ``graph.py``:

- after ``decide_cluster``: route to ``cluster`` or straight to ``describe_patches``
- ``route_after_classify``: confidence >= 4 -> store; 2-3 and not retried ->
  retry_vllm_targeted; <= 1 -> clip_fallback
- post-retry routing: confidence >= 3 -> store; else -> clip_fallback

Edge functions read ``confidence`` and ``used_retry`` from state. See
ARCHITECTURE.md §2.8 and CLAUDE.md §8.
"""
