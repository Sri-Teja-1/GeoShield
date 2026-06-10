"""preprocess node.

Phase 3: EXIF correction, RGB conversion, dimension check (reject < 224px),
tiling (passthrough <= 1024px; 512px patches with 10% overlap otherwise).
Returns ``processed_patches``, ``was_tiled``, ``num_patches``. See
ARCHITECTURE.md §2.2.
"""
