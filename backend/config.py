"""Application configuration.

Phase 1: implement a pydantic-settings ``Settings`` class that loads every
environment variable from CLAUDE.md §6 (model keys, Qdrant, storage backend,
app settings) and a cached ``get_settings()`` accessor. Nothing is hardcoded;
all config flows from ``.env`` through this module.
"""
