"""Phase 4's raw objects, published in full (Phase 6.5 IMPLEMENTATION doc section 5.1, decision A).

The manifest (``site/rawmanifest.py``, committed in Phase 1.5) names every pilot and official object by key,
byte count, sha256 and version id. This module copies each object's bytes into the repository at its key,
under ``experiment/raw/``, and checks the copy against the manifest. Two entry points:

- ``pull_raw`` reads each object **at the manifest's version id** through ``rawmanifest.RawReader``, which
  has no write call, so the bucket cannot be changed from here. His to run: Claude's deny list keeps it out
  of S3.
- ``verify_raw`` reads only the published copy and the committed manifest. Anyone can run it, and
  ``pytest`` does, once the copy is committed.

**Both refuse** (each is a finding for him, never something to code around): a manifest that does not
describe itself as the Phase 1.5 one does; a key outside the fictional company's two prefixes (rule zero: no
case record is in the manifest, and none may reach this folder); a key of an unexpected shape; bytes whose
count or sha256 differs from the manifest; a file that is not UTF-8; and a file that fails the checks every
sweep record passed when it was written (``smoke/record.py``'s ``assert_clean``): an e-mail address, a
twelve-digit number standing alone, an API key, and, when the pull knows it, the account id itself.
``verify_raw`` also refuses a file the manifest does not name, and a named file that is missing. Nothing is
overwritten: the same bytes again is a no-op, different bytes are refused.

Run code under ``protocol/sets.py``'s rules; standard library only.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from horizon_compact.site.rawmanifest import (
    HASH,
    KIND,
    PREFIXES,
    SCHEMA,
    SCHEMA_VERSION,
    RawReader,
)

RAW_ROOT = Path("experiment") / "raw"
# The fictional company's records only. The manifest's prefixes are ``official/`` and ``pilot/``; every key in
# it is under one of these two (measured 2026-11-14: 4,892 and 355). A key anywhere else is refused, whatever
# the manifest says.
ALLOWED_PREFIXES: tuple[str, ...] = ("official/company/", "pilot/company/")
PROGRESS_EVERY = 500

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_KEY_CHARACTERS = re.compile(r"^[A-Za-z0-9._/-]+$")
# Copied from ``smoke/record.py``, which keeps them private; a test holds the copies equal to the originals,
# so the check here is the one every record passed when it was written.
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}")
ACCOUNT_ID_SHAPE = re.compile(r"(?<![\w-])\d{12}(?![\w-])")
API_KEY = re.compile(r"sk-(?:or|ant)-[A-Za-z0-9_-]{8,}")


class RawTextRefusal(Exception):
    """The raw text cannot be published, or does not match its manifest."""


@dataclass(frozen=True)
class Entry:
    """One object, as the manifest states it."""

    key: str
    size: int
    sha256: str
    version_id: str


@dataclass(frozen=True)
class PullReport:
    written: int
    unchanged: int
    total_bytes: int


@dataclass(frozen=True)
class VerifyReport:
    objects: int
    total_bytes: int


def _check_key(key: str) -> None:
    if not _KEY_CHARACTERS.match(key) or key.endswith("/"):
        raise RawTextRefusal(f"a key with an unexpected shape: {key!r}")
    if any(part in ("", ".", "..") for part in key.split("/")):
        raise RawTextRefusal(f"a key with an unexpected shape: {key!r}")
    if not key.startswith(ALLOWED_PREFIXES):
        raise RawTextRefusal(
            f"{key} is outside the fictional company's records ({', '.join(ALLOWED_PREFIXES)})"
        )


def _entry(item: Any, number: int) -> Entry:
    if not isinstance(item, dict):
        raise RawTextRefusal(f"object {number} of the manifest is not an object")
    key, size, sha, version = (item.get(f) for f in ("key", "bytes", "sha256", "version_id"))
    if not isinstance(key, str):
        raise RawTextRefusal(f"object {number} of the manifest has no key")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise RawTextRefusal(f"{key}: the manifest's byte count is not a whole number")
    if not isinstance(sha, str) or not _SHA256.match(sha):
        raise RawTextRefusal(f"{key}: the manifest's sha256 is not 64 hex digits")
    if not isinstance(version, str) or not version:
        raise RawTextRefusal(f"{key}: the manifest has no version id")
    _check_key(key)
    return Entry(key, size, sha, version)


def load_manifest(path: Path) -> tuple[Entry, ...]:
    """The manifest's objects, in its order, after checking that the file is what Phase 1.5 wrote: its
    schema, its prefixes, its count and its total, and keys that are unique and sorted."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RawTextRefusal(f"no manifest at {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RawTextRefusal(f"{path} is not a JSON manifest: {exc}") from exc
    if not isinstance(data, dict):
        raise RawTextRefusal(f"{path} is not a JSON object")
    expected = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "hash": HASH,
        "prefixes": list(PREFIXES),
    }
    for field, value in expected.items():
        if data.get(field) != value:
            raise RawTextRefusal(f"the manifest's {field} is {data.get(field)!r}, not {value!r}")
    items = data.get("objects")
    if not isinstance(items, list) or not items:
        raise RawTextRefusal("the manifest lists no objects")
    entries = tuple(_entry(item, n) for n, item in enumerate(items, start=1))
    keys = [e.key for e in entries]
    if len(set(keys)) != len(keys):
        raise RawTextRefusal("the manifest names a key twice")
    if keys != sorted(keys):
        raise RawTextRefusal("the manifest's keys are not in sorted order")
    if data.get("object_count") != len(entries):
        raise RawTextRefusal(
            f"the manifest says {data.get('object_count')} objects and lists {len(entries)}"
        )
    if data.get("total_bytes") != sum(e.size for e in entries):
        raise RawTextRefusal("the manifest's total_bytes is not the sum of its objects' bytes")
    return entries


def check_text(key: str, data: bytes, account: str | None = None) -> None:
    """The write-time checks again, on one object's bytes. ``account`` is the account id, known to the pull
    (from the bucket name) and not to a reader of the published copy."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RawTextRefusal(f"{key} is not UTF-8 text") from exc
    if account and account in text:
        raise RawTextRefusal(f"{key} holds the account id")
    for pattern, what in (
        (EMAIL, "an e-mail address"),
        (ACCOUNT_ID_SHAPE, "a twelve-digit number standing alone"),
        (API_KEY, "an API key"),
    ):
        if pattern.search(text):
            raise RawTextRefusal(f"{key} holds {what}")


def _check_bytes(entry: Entry, data: bytes) -> None:
    if len(data) != entry.size:
        raise RawTextRefusal(f"{entry.key}: {len(data)} bytes, the manifest says {entry.size}")
    if hashlib.sha256(data).hexdigest() != entry.sha256:
        raise RawTextRefusal(f"{entry.key}: its sha256 is not the manifest's")


def _path(root: Path, key: str) -> Path:
    path = root.joinpath(*key.split("/"))
    if not path.resolve().is_relative_to(root.resolve()):
        raise RawTextRefusal(f"{key} would be written outside {root}")  # pragma: no cover
    return path


def _write_once(path: Path, data: bytes) -> bool:
    """True when written, False when the same bytes were already there."""
    if path.exists():
        if path.read_bytes() == data:
            return False
        raise RawTextRefusal(f"{path} already holds different bytes; it is never overwritten")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    temporary.replace(path)
    return True


def pull_raw(
    reader: RawReader,
    entries: tuple[Entry, ...],
    root: Path,
    account: str,
    progress: Callable[[int, int], None] | None = None,
) -> PullReport:
    """Every object at its manifest version, checked before it is written. A refusal stops the pull; what was
    written before it passed every check, and a second run skips it."""
    written = unchanged = total = 0
    for number, entry in enumerate(entries, start=1):
        data = b"".join(reader.read(entry.key, entry.version_id))
        _check_bytes(entry, data)
        check_text(entry.key, data, account)
        if _write_once(_path(root, entry.key), data):
            written += 1
        else:
            unchanged += 1
        total += len(data)
        if progress is not None and number % PROGRESS_EVERY == 0:
            progress(number, len(entries))
    return PullReport(written, unchanged, total)


def _on_disk(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def verify_raw(root: Path, entries: tuple[Entry, ...]) -> VerifyReport:
    """The published copy against the manifest: the same keys, and each file's bytes, sha256 and text
    checks."""
    if not root.is_dir():
        raise RawTextRefusal(f"nothing is published at {root}")
    named = {e.key for e in entries}
    present = _on_disk(root)
    missing = sorted(named - present)
    extra = sorted(present - named)
    if missing:
        raise RawTextRefusal(
            f"{len(missing)} object(s) named by the manifest are missing, first {missing[0]}"
        )
    if extra:
        raise RawTextRefusal(f"{len(extra)} file(s) the manifest does not name, first {extra[0]}")
    total = 0
    for entry in entries:
        data = _path(root, entry.key).read_bytes()
        _check_bytes(entry, data)
        check_text(entry.key, data)
        total += len(data)
    return VerifyReport(len(entries), total)
