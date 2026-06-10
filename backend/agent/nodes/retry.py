"""retry_vllm_targeted node.

Phase 4: build a focused disambiguation prompt from ``alternative_classes`` and
``ambiguity_reason``, re-run the describe_patches -> synthesize subgraph, and set
``used_retry = True``. Fires on confidence 2-3 when not yet retried. See
ARCHITECTURE.md §2.8.
"""
