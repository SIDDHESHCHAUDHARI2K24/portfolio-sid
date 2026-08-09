"""Tests for app.core.storage (TD-08).

S3 tests run against local MinIO (localhost:9000) and skip when it is
unreachable, so CI without MinIO still exercises LocalDiskStorage.
"""

import ast
import json
import socket
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

from app.core.config import Settings
from app.core.storage import (
    CACHE_CONTROL,
    LocalDiskStorage,
    S3Storage,
    content_hashed_key,
    get_storage,
)

MINIO_HOST = "localhost"
MINIO_PORT = 9000
MINIO_BUCKET = "portfolio-media"


def _minio_reachable() -> bool:
    try:
        with socket.create_connection((MINIO_HOST, MINIO_PORT), timeout=1):
            return True
    except OSError:
        return False


def test_content_hashed_key_stable_for_same_bytes() -> None:
    first = content_hashed_key("certs/aws", b"same-bytes", "pdf")
    second = content_hashed_key("certs/aws", b"same-bytes", "pdf")
    assert first == second


def test_content_hashed_key_differs_for_different_bytes() -> None:
    v1 = content_hashed_key("certs/aws", b"version-one", "pdf")
    v2 = content_hashed_key("certs/aws", b"version-two", "pdf")
    assert v1 != v2


def test_content_hashed_key_format() -> None:
    key = content_hashed_key("img/hero", b"abc", "webp")
    assert key.startswith("img/hero-")
    assert key.endswith(".webp")
    digest = key[len("img/hero-") : -len(".webp")]
    assert len(digest) == 12
    int(digest, 16)


@pytest.fixture
def local_storage(tmp_path: Path) -> LocalDiskStorage:
    return LocalDiskStorage(Settings(local_storage_dir=str(tmp_path / "store")))


def test_local_round_trip(local_storage: LocalDiskStorage, tmp_path: Path) -> None:
    data = b"hello local bytes"
    key = content_hashed_key("docs/resume", data, "txt")
    local_storage.put(key, data, "text/plain")
    assert local_storage.exists(key)
    assert (tmp_path / "store" / key).read_bytes() == data
    assert local_storage.get_url(key) == f"/media/{key}"
    local_storage.delete(key)
    assert not local_storage.exists(key)


def test_local_delete_missing_key_is_noop(local_storage: LocalDiskStorage) -> None:
    local_storage.delete("never/put.txt")


@pytest.fixture
def fresh_storage_caches() -> Iterator[None]:
    from app.core import config as config_module
    from app.core import storage as storage_module

    config_module.get_settings.cache_clear()
    storage_module.get_storage.cache_clear()
    yield
    config_module.get_settings.cache_clear()
    storage_module.get_storage.cache_clear()


def test_get_storage_local(fresh_storage_caches: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_KIND", "local")
    assert isinstance(get_storage(), LocalDiskStorage)


def test_get_storage_s3_is_default(
    fresh_storage_caches: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("STORAGE_KIND", raising=False)
    assert isinstance(get_storage(), S3Storage)


@pytest.fixture
def s3_storage() -> S3Storage:
    if not _minio_reachable():
        pytest.skip(f"MinIO unreachable at {MINIO_HOST}:{MINIO_PORT}")
    settings = Settings(
        r2_endpoint=f"http://{MINIO_HOST}:{MINIO_PORT}",
        r2_access_key_id="minioadmin",
        r2_secret_access_key="minioadmin",
        r2_bucket=MINIO_BUCKET,
    )
    storage = S3Storage(settings)
    try:
        storage._client.head_bucket(Bucket=MINIO_BUCKET)
    except Exception:
        storage._client.create_bucket(Bucket=MINIO_BUCKET)
    # Match prod R2: objects are publicly readable via their URL.
    storage._client.put_bucket_policy(
        Bucket=MINIO_BUCKET,
        Policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"],
                    }
                ],
            }
        ),
    )
    return storage


def test_s3_round_trip_and_cache_headers(s3_storage: S3Storage) -> None:
    data = b"td-08 minio round trip"
    key = content_hashed_key("test/td08", data, "txt")
    s3_storage.put(key, data, "text/plain")
    try:
        assert s3_storage.exists(key)

        head = s3_storage._client.head_object(Bucket=MINIO_BUCKET, Key=key)
        assert head["ContentType"] == "text/plain"
        assert head.get("CacheControl") == CACHE_CONTROL

        response = httpx.get(s3_storage.get_url(key), timeout=5)
        assert response.status_code == 200
        assert response.content == data
        assert response.headers.get("Cache-Control") == CACHE_CONTROL
    finally:
        s3_storage.delete(key)
    assert not s3_storage.exists(key)


def test_s3_different_content_different_key(s3_storage: S3Storage) -> None:
    data_a = b"td-08 version one"
    data_b = b"td-08 version two"
    key_a = content_hashed_key("test/td08-doc", data_a, "bin")
    key_b = content_hashed_key("test/td08-doc", data_b, "bin")
    assert key_a != key_b
    s3_storage.put(key_a, data_a, "application/octet-stream")
    s3_storage.put(key_b, data_b, "application/octet-stream")
    try:
        assert s3_storage.exists(key_a)
        assert s3_storage.exists(key_b)
    finally:
        s3_storage.delete(key_a)
        s3_storage.delete(key_b)


def test_boto3_import_isolation() -> None:
    app_root = Path(__file__).resolve().parents[1]
    offenders: list[Path] = []
    for path in sorted(app_root.rglob("*.py")):
        if path.parent.name == "core" and path.name == "storage.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            if any(module.split(".", 1)[0] in {"boto3", "botocore"} for module in modules):
                offenders.append(path)
    assert offenders == []
