"""Object storage abstraction.

Phase 1: ``StorageBackend`` interface with ``save_image(image_bytes, image_hash)
-> str`` and ``get_image_url(image_ref) -> str``. ``LocalStorage`` (dev) and
``R2Storage`` (prod) implementations behind a factory that reads
``STORAGE_BACKEND`` from config. See ARCHITECTURE.md §5 / CLAUDE.md §5.
"""
