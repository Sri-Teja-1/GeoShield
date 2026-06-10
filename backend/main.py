"""GeoShield FastAPI application entry point.

Phase 0 scaffold: exposes a bare ``app`` so ``uv run uvicorn main:app`` starts
cleanly. Routes, middleware, the rate limiter, Qdrant collection setup, and the
compiled LangGraph agent on ``app.state.graph`` are wired in Phase 5 (see
ARCHITECTURE.md §6 and CLAUDE.md §9).
"""

from fastapi import FastAPI

app = FastAPI(title="GeoShield API", version="0.1.0")
