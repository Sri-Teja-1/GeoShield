"""Text embeddings wrapper (OpenAI ``text-embedding-3-small``, 1536-dim).

The embedding of the synthesized description is the query/stored vector for RAG
retrieval (ARCHITECTURE.md §2.6, §5.1). The client is cached on first use.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from openai import OpenAI

from config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def _client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)


def embed_text(text: str) -> list[float]:
    """Return the 1536-dim embedding of ``text`` using text-embedding-3-small."""
    settings = get_settings()
    response = _client().embeddings.create(model=settings.embedding_model, input=text)
    return response.data[0].embedding


if __name__ == "__main__":
    vector = embed_text("a satellite image of dense urban residential housing")
    print(f"model      : {get_settings().embedding_model}")
    print(f"dimensions : {len(vector)}")
    print(f"first three: {vector[:3]}")
