"""describe_patches + describe_single_patch nodes.

Phase 3: ``describe_patches`` fans out to ``describe_single_patch`` workers via
LangGraph's ``Send`` API, concurrency capped at 4 in-flight calls. Each worker
calls ``services/vllm.py`` and appends to ``patch_descriptions`` (reducer-safe).
See ARCHITECTURE.md §2.4 and CLAUDE.md §8.
"""
