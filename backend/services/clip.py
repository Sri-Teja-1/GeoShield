"""Local CLIP wrapper (CPU).

Phase 2: load ``openai/clip-vit-base-patch32`` from HuggingFace on module import
(CPU). ``classify_with_clip(image_bytes: bytes, class_list: list[str]) ->
tuple[str, float]`` returns the best class and its cosine similarity.
"""
