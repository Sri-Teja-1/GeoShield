"""retrieve node.

Phase 3: embed the synthesized description, build a Qdrant filter (geo +
class_list_hash + confidence floor + optional time window), query top-3, and
relax progressively on zero results. See ARCHITECTURE.md §2.6.
"""
