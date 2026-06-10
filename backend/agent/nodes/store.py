"""store node.

Phase 3: always write the image to object storage; write a Qdrant point only if
``confidence >= 3`` (storage guard). Storage failures are non-fatal — log to
``pipeline_errors`` and continue. See ARCHITECTURE.md §2.10 and CLAUDE.md §8.
"""
