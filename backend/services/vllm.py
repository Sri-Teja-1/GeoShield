"""Vision-language model wrapper (Llama Vision via Groq).

``describe_image`` sends image bytes + a text prompt to Groq's hosted Llama
Vision model and returns the description string, retrying once on a transient
error (ARCHITECTURE.md §2.4, §4.3.6). The exact model ID is read from config
(``vllm_model``) and confirmed against Groq's live model list during Phase 2
verification, since Groq rotates which Llama vision checkpoints it hosts.
"""

from __future__ import annotations

import base64
import logging
from functools import lru_cache

from groq import Groq

from config import get_settings

logger = logging.getLogger(__name__)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_MAX_TOKENS = 1024


@lru_cache
def _client() -> Groq:
    return Groq(api_key=get_settings().groq_api_key)


def _data_url(image_bytes: bytes) -> str:
    mime = "image/png" if image_bytes.startswith(_PNG_MAGIC) else "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def describe_image(image_bytes: bytes, prompt: str) -> str:
    """Return a natural-language description of ``image_bytes`` guided by ``prompt``.

    Retries once on a transient API error before re-raising (the caller — the
    ``describe_single_patch`` worker — degrades gracefully on persistent failure).
    """
    settings = get_settings()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": _data_url(image_bytes)}},
            ],
        }
    ]

    last_error: Exception | None = None
    for attempt in range(2):  # initial attempt + one retry
        try:
            response = _client().chat.completions.create(
                model=settings.vllm_model,
                messages=messages,
                temperature=0.2,
                max_tokens=_MAX_TOKENS,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:  # transient: rate limit, timeout, 5xx
            last_error = exc
            logger.warning("vLLM call failed (attempt %d/2): %s", attempt + 1, exc)

    assert last_error is not None
    raise last_error


if __name__ == "__main__":
    # Minimal smoke test: describe a tiny solid-color PNG. Confirms the key works
    # and the configured model responds.
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (256, 256), (34, 139, 34)).save(buf, format="PNG")
    text = describe_image(buf.getvalue(), "Describe this image patch in one sentence.")
    print(f"model: {get_settings().vllm_model}")
    print(f"reply: {text}")
