"""Vision-language model wrapper (Groq / Llama 3.2 Vision).

Phase 2: ``describe_image(image_bytes: bytes, prompt: str) -> str`` using the
Groq SDK with Llama 3.2 Vision. One retry on transient errors.
"""
