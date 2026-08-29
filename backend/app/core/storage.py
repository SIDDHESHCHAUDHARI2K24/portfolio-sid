"""S3-compatible object storage (Cloudflare R2 / local MinIO) plus local-disk fallback.

All adapter methods are sync on purpose: boto3 is a sync SDK. Call from async
code via ``asyncio.to_thread`` when needed. Per conventions invariant 5, boto3
is imported only in this module — feature slices consume the adapter via
``core/deps.py``, never boto3 directly.
"""

import hashlib
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.core.config import Settings, get_settings

CACHE_CONTROL = "public, max-age=31536000, immutable"


def content_hashed_key(prefix: str, data: bytes, extension: str) -> str:
    """Return ``<prefix>-<sha256(data)[:12]>.<extension>``.

    Replacing a file changes its bytes, therefore its key, therefore its URL —
    edge caches can never serve a stale version of a published object.
    """
    digest = hashlib.sha256(data).hexdigest()[:12]
    return f"{prefix}-{digest}.{extension}"


class StorageAdapter(ABC):
    """Sync interface: boto3 is sync. Wrap in ``asyncio.to_thread`` from async code."""

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> None:
        """Store ``data`` at ``key`` with the given content type and immutable cache headers."""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Public URL for ``key``."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete ``key``. No-op if the object does not exist."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """True if ``key`` exists."""


class S3Storage(StorageAdapter):
    """One implementation for Cloudflare R2 (prod) and MinIO (dev) — only the endpoint differs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._settings.r2_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            CacheControl=CACHE_CONTROL,
        )

    def get_url(self, key: str) -> str:
        base = self._settings.r2_public_base_url
        if base:
            return f"{base.rstrip('/')}/{key}"
        return f"{self._settings.r2_endpoint}/{self._settings.r2_bucket}/{key}"

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._settings.r2_bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._settings.r2_bucket, Key=key)
        except ClientError as exc:
            error = exc.response.get("Error", {})
            if (
                error.get("Code") in {"404", "NotFound", "NoSuchKey"}
                or exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404
            ):
                return False
            raise
        return True


class LocalDiskStorage(StorageAdapter):
    """Dev/CI fallback per dependency-map F3.

    Files land under ``settings.local_storage_dir`` and are served at
    ``/media/<key>`` by the frontend/dev server. ``content_type`` is accepted
    for interface parity but not persisted on disk.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._root = Path(settings.local_storage_dir)

    def _path(self, key: str) -> Path:
        path = self._root / key
        if ".." in path.parts or not str(path).startswith(str(self._root)):
            raise ValueError(f"unsafe storage key: {key!r}")
        return path

    def put(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get_url(self, key: str) -> str:
        base = self._settings.media_base_url
        if base:
            return f"{base.rstrip('/')}/media/{key}"
        return f"/media/{key}"

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()


@lru_cache
def get_storage() -> StorageAdapter:
    """Factory selected by ``settings.storage_kind``: ``s3`` (default) or ``local``."""
    settings = get_settings()
    if settings.storage_kind == "local":
        return LocalDiskStorage(settings)
    return S3Storage(settings)
