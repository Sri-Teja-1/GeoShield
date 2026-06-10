"""Application configuration.

All settings flow from environment variables (or the project-root ``.env``)
through a single pydantic-settings ``Settings`` object. Nothing is hardcoded at
call sites — services and routes read from ``get_settings()``. See CLAUDE.md §6
for the environment contract.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py lives in backend/; the .env (and .env.example) live at the project
# root, one level up. Resolve it absolutely so the location is independent of
# the process working directory (uvicorn is launched from backend/).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Model provider keys (CLAUDE.md §6) ──────────────────────────────
    groq_api_key: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""

    # ── Qdrant ──────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""  # empty for local Docker

    # ── Storage ─────────────────────────────────────────────────────────
    storage_backend: Literal["local", "r2"] = "local"
    local_storage_path: str = "./data/images"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""

    # ── App ─────────────────────────────────────────────────────────────
    frontend_origin: str = "http://localhost:5173"
    rate_limit: str = "10/minute"

    # ── Vector store layout ─────────────────────────────────────────────
    # Not part of .env (stable across environments) but centralized here so
    # qdrant.py and the agent share one source of truth. Overridable via env.
    qdrant_collection: str = "analyses"
    embedding_dim: int = 1536  # OpenAI text-embedding-3-small

    # ── Model identifiers ───────────────────────────────────────────────
    # Self-reported by /health and tagged onto every stored point (§5.2). The
    # exact provider model IDs are confirmed when the service wrappers are
    # implemented in Phase 2; these are the configured defaults.
    vllm_model: str = "llama-3.2-11b-vision-preview"
    llm_model: str = "gemini-2.0-flash"
    embedding_model: str = "text-embedding-3-small"
    clip_model: str = "openai/clip-vit-base-patch32"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton (cached after first load)."""
    return Settings()
