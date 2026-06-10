"""Middleware: CORS, rate limiting, and exception handlers.

Phase 5: configure CORS from ``FRONTEND_ORIGIN`` + localhost:5173 (no wildcard
in production), the slowapi limiter (10/minute on the analyze endpoints only),
and a global exception handler (unhandled -> 500, ValidationError -> 400). See
CLAUDE.md §9.
"""
