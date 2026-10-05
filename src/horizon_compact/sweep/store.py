"""Where a sweep's objects live (Phase 1 IMPLEMENTATION doc section 7). Every write is exclusive.

``S3Store`` sends ``IfNoneMatch="*"`` on every put, and a 412 means the key exists: never an overwrite. The
bucket's policy refuses a put without the header, so the harness and the bucket enforce write-once separately.
``LocalStore`` writes the same layout with an exclusive create, for laptop development runs under
``scratch/runs/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

_EXISTS_CODES = frozenset({"PreconditionFailed", "ConditionalRequestConflict"})
_MISSING_CODES = frozenset({"NoSuchKey", "404"})


class Store(Protocol):
    def put_new(self, key: str, text: str) -> bool:
        """Create ``key``. False if it already exists; the object is never replaced."""
        ...

    def get(self, key: str) -> str | None: ...

    def list_keys(self, prefix: str) -> list[str]: ...


class LocalStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def put_new(self, key: str, text: str) -> bool:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(text)
        except FileExistsError:
            return False
        return True

    def get(self, key: str) -> str | None:
        path = self.root / key
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def list_keys(self, prefix: str) -> list[str]:
        base = self.root / prefix
        if not base.exists():
            return []
        return sorted(p.relative_to(self.root).as_posix() for p in base.rglob("*") if p.is_file())


class S3Store:
    def __init__(self, client: S3Client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put_new(self, key: str, text: str) -> bool:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=text.encode("utf-8"),
                ContentType="application/json",
                IfNoneMatch="*",
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _EXISTS_CODES:
                return False
            raise
        return True

    def get(self, key: str) -> str | None:
        try:
            body = self._client.get_object(Bucket=self._bucket, Key=key)["Body"].read()
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in _MISSING_CODES:
                return None
            raise
        return bytes(body).decode("utf-8")

    def list_keys(self, prefix: str) -> list[str]:
        keys: list[str] = []
        for page in self._client.get_paginator("list_objects_v2").paginate(
            Bucket=self._bucket, Prefix=prefix
        ):
            keys.extend(obj["Key"] for obj in page.get("Contents", []) if "Key" in obj)
        return sorted(keys)
