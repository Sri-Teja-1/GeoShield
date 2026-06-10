"""Local CLIP wrapper (CPU fallback).

Zero-shot image-to-text classification used only when the LLM path bottoms out
(ARCHITECTURE.md §2.8, §4.3.11). ``classify_with_clip`` renders each class as a
short prompt, computes cosine similarity against the image embedding, and
returns the argmax class with its similarity score.

Per CLAUDE.md §5 the model is loaded on module import; the load is wrapped so an
offline cache miss logs and defers to first use rather than breaking the whole
backend import.
"""

from __future__ import annotations

import io
import logging

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from config import get_settings

logger = logging.getLogger(__name__)

_model: CLIPModel | None = None
_processor: CLIPProcessor | None = None


def _load() -> tuple[CLIPModel, CLIPProcessor]:
    """Load and cache the CLIP model + processor on CPU."""
    global _model, _processor
    if _model is None or _processor is None:
        name = get_settings().clip_model
        logger.info("Loading CLIP model %r on CPU…", name)
        model = CLIPModel.from_pretrained(name)
        model.eval()
        _model = model
        _processor = CLIPProcessor.from_pretrained(name)
    return _model, _processor


def classify_with_clip(image_bytes: bytes, class_list: list[str]) -> tuple[str, float]:
    """Return the best-matching class and its cosine similarity (∈ [-1, 1])."""
    model, processor = _load()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    prompts = [f"a satellite image of {label}" for label in class_list]

    inputs = processor(text=prompts, images=image, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)

    image_embeds = outputs.image_embeds / outputs.image_embeds.norm(p=2, dim=-1, keepdim=True)
    text_embeds = outputs.text_embeds / outputs.text_embeds.norm(p=2, dim=-1, keepdim=True)
    similarities = (image_embeds @ text_embeds.T).squeeze(0)

    best = int(similarities.argmax())
    return class_list[best], float(similarities[best])


# Eager load on import (CLAUDE.md §5). Tolerate failure so an offline HuggingFace
# cache miss doesn't brick the entire backend import — classify retries the load.
try:
    _load()
except Exception as exc:  # pragma: no cover - defensive
    logger.warning("CLIP eager load on import failed (will retry on first use): %s", exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), (34, 139, 34)).save(buf, format="PNG")  # forest green
    label, score = classify_with_clip(buf.getvalue(), ["forest", "urban", "water"])
    print(f"model : {get_settings().clip_model}")
    print(f"best  : {label}  (cosine={score:.4f})")
