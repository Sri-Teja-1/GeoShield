"""Object storage abstraction.

A single ``StorageBackend`` interface with two implementations — ``LocalStorage``
(dev, filesystem) and ``R2Storage`` (prod, Cloudflare R2 over S3) — selected by
the ``STORAGE_BACKEND`` setting. Keeping image bytes out of Qdrant and behind
this interface is the §3.4 decision: vector DBs are for vectors + metadata, not
binary blobs.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

from config import get_settings

logger = logging.getLogger(__name__)

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_JPEG_MAGIC = b"\xff\xd8\xff"
_MIME_BY_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".bin": "application/octet-stream"}


def _ext_from_bytes(data: bytes) -> str:
    """Sniff a file extension from magic bytes (PNG/JPEG only; §2.1 accepts these)."""
    if data.startswith(_PNG_MAGIC):
        return ".png"
    if data.startswith(_JPEG_MAGIC):
        return ".jpg"
    return ".bin"


class StorageBackend(ABC):
    """Persists image bytes and resolves a loadable URL for them."""

    @abstractmethod
    def save_image(self, image_bytes: bytes, image_hash: str) -> str:
        """Persist the image, keyed by its SHA-256 hash, and return an opaque
        ``image_ref`` (e.g. ``file:///…`` or ``r2://bucket/key``)."""

    @abstractmethod
    def get_image_url(self, image_ref: str) -> str:
        """Resolve a stored ``image_ref`` to a URL a browser can load."""


class LocalStorage(StorageBackend):
    """Development backend: writes to the local filesystem under ``base_path``.

    ``save_image`` returns a ``file://`` URI; ``get_image_url`` returns an
    app-relative ``/images/{filename}`` path (a static route serving these is
    wired up in a later phase)."""

    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_bytes: bytes, image_hash: str) -> str:
        filename = f"{image_hash}{_ext_from_bytes(image_bytes)}"
        path = self.base_path / filename
        if not path.exists():  # content-addressed: identical bytes never rewritten
            path.write_bytes(image_bytes)
        return path.as_uri()

    def get_image_url(self, image_ref: str) -> str:
        filename = image_ref.rsplit("/", 1)[-1]
        return f"/images/{filename}"


class R2Storage(StorageBackend):
    """Production backend: Cloudflare R2 (S3-compatible) via boto3."""

    def __init__(
        self,
        *,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ) -> None:
        import boto3  # imported lazily so dev (LocalStorage) never needs R2 config

        self.bucket = bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def save_image(self, image_bytes: bytes, image_hash: str) -> str:
        ext = _ext_from_bytes(image_bytes)
        key = f"{image_hash}{ext}"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=image_bytes,
            ContentType=_MIME_BY_EXT.get(ext, "application/octet-stream"),
        )
        return f"r2://{self.bucket}/{key}"

    def get_image_url(self, image_ref: str) -> str:
        # r2://bucket/key -> presigned GET URL (1h)
        _, _, rest = image_ref.partition("r2://")
        bucket, _, key = rest.partition("/")
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket or self.bucket, "Key": key},
            ExpiresIn=3600,
        )


@lru_cache
def get_storage() -> StorageBackend:
    """Return the configured storage backend (cached). Reads ``STORAGE_BACKEND``."""
    settings = get_settings()
    if settings.storage_backend == "r2":
        logger.info("Using R2 storage backend (bucket=%r)", settings.r2_bucket_name)
        return R2Storage(
            account_id=settings.r2_account_id,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket_name=settings.r2_bucket_name,
        )
    logger.info("Using local storage backend (path=%r)", settings.local_storage_path)
    return LocalStorage(settings.local_storage_path)
