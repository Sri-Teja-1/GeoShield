"""Qdrant client and collection setup.

The client is created once (cached) and the ``analyses`` collection is created
on demand with the exact vector config and payload indexes from
ARCHITECTURE.md §5.1. Index creation is idempotent — safe to call on every
startup.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from config import get_settings

logger = logging.getLogger(__name__)

# Payload indexes for efficient filtering (ARCHITECTURE.md §5.1).
_PAYLOAD_INDEXES: dict[str, PayloadSchemaType] = {
    "location": PayloadSchemaType.GEO,  # geo_radius queries
    "class_list_hash": PayloadSchemaType.KEYWORD,  # exact-match retrieval compatibility
    "timestamp": PayloadSchemaType.DATETIME,  # time-window range filters
    "confidence": PayloadSchemaType.INTEGER,  # confidence-floor filters
}


@lru_cache
def get_client() -> QdrantClient:
    """Return the process-wide Qdrant client (cached after first use)."""
    settings = get_settings()
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,  # None for local Docker
    )


def create_collection_if_not_exists(client: QdrantClient | None = None) -> None:
    """Create the ``analyses`` collection (1536-dim, cosine) and its payload
    indexes if they do not already exist. Idempotent."""
    settings = get_settings()
    client = client or get_client()

    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dim,
                distance=Distance.COSINE,
            ),
        )
        logger.info(
            "Created Qdrant collection %r (dim=%d, cosine)",
            settings.qdrant_collection,
            settings.embedding_dim,
        )
    else:
        logger.info("Qdrant collection %r already exists", settings.qdrant_collection)

    _ensure_payload_indexes(client, settings.qdrant_collection)


def _ensure_payload_indexes(client: QdrantClient, collection: str) -> None:
    """Create any missing payload indexes; leave existing ones untouched."""
    try:
        existing = client.get_collection(collection).payload_schema or {}
    except Exception:  # pragma: no cover - defensive; treat as "none indexed yet"
        existing = {}

    for field_name, schema_type in _PAYLOAD_INDEXES.items():
        if field_name in existing:
            continue
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=field_name,
                field_schema=schema_type,
            )
            logger.info("Created payload index %r (%s) on %r", field_name, schema_type, collection)
        except Exception as exc:  # non-fatal — log and continue
            logger.warning("Could not create payload index %r on %r: %s", field_name, collection, exc)


if __name__ == "__main__":
    # Manual setup/verification entry point (Phase 1 verify step).
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    create_collection_if_not_exists()
    _settings = get_settings()
    _info = get_client().get_collection(_settings.qdrant_collection)
    _params = _info.config.params.vectors
    print(f"\nCollection : {_settings.qdrant_collection}")
    print(f"Status     : {_info.status}")
    print(f"Vector dim : {_params.size}")
    print(f"Distance   : {_params.distance}")
    print(f"Indexes    : {sorted((_info.payload_schema or {}).keys())}")
