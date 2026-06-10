"""LLM wrapper (Gemini Flash via Google AI Studio).

Two calls:
- ``classify_structured(prompt)`` — JSON-mode classification, returns a parsed
  dict (``predicted_class``, ``confidence``, ``reasoning``, and optionally
  ``alternative_classes`` / ``ambiguity_reason``). The prompt itself specifies
  the schema; JSON mode guarantees parseable output (ARCHITECTURE.md §2.7).
- ``synthesize(prompt)`` — free-text synthesis of patch descriptions (§2.5).

The exact JSON schema lives in the classify node's prompt (Phase 3); this
wrapper only enforces JSON output and parses it.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache

import google.generativeai as genai

from config import get_settings

logger = logging.getLogger(__name__)

_configured = False


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        genai.configure(api_key=get_settings().google_api_key)
        _configured = True


@lru_cache
def _model(json_mode: bool) -> "genai.GenerativeModel":
    _ensure_configured()
    generation_config: dict = {"temperature": 0.2}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
    return genai.GenerativeModel(
        get_settings().llm_model,
        generation_config=generation_config,
    )


def classify_structured(prompt: str) -> dict:
    """Run a JSON-mode classification call and return the parsed dict.

    Retries once on a transient error. Raises ``json.JSONDecodeError`` if the
    response is not valid JSON (the classify node treats this as a failure and
    routes to the CLIP fallback)."""
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = _model(json_mode=True).generate_content(prompt)
            return json.loads(response.text)
        except json.JSONDecodeError:
            raise
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini classify failed (attempt %d/2): %s", attempt + 1, exc)
    assert last_error is not None
    raise last_error


def synthesize(prompt: str) -> str:
    """Run a free-text synthesis call and return the response text."""
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = _model(json_mode=False).generate_content(prompt)
            return (response.text or "").strip()
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini synthesize failed (attempt %d/2): %s", attempt + 1, exc)
    assert last_error is not None
    raise last_error


if __name__ == "__main__":
    result = classify_structured(
        'Classify the scene into one of ["forest", "urban", "water"]. '
        "Scene: dense green tree canopy covering rolling hills. "
        'Respond as JSON: {"predicted_class": string, "confidence": integer 1-5, "reasoning": string}.'
    )
    print(f"model    : {get_settings().llm_model}")
    print(f"classify : {result}")
    summary = synthesize("Summarize in one sentence: a river runs through a forested valley.")
    print(f"synthesize: {summary}")
