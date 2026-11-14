"""Phase 4's raw objects published in full, and ``hc site raw-pull`` and ``hc site raw-verify`` (Phase 6.5
IMPLEMENTATION doc section 5.1, decision A).

Every key, run id and body is a fictional canary in the real key shapes. The bucket is a fake whose name ends
in a fake account id. Nothing here touches a network.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from horizon_compact import cli
from horizon_compact.cli import CLEAN_EXIT, RAW_MANIFEST_PATH, REFUSED_EXIT, main
from horizon_compact.site import rawtext
from horizon_compact.site.rawmanifest import (
    HASH,
    KIND,
    PREFIXES,
    SCHEMA,
    SCHEMA_VERSION,
    S3RawReader,
    build_raw_manifest,
)
from horizon_compact.site.rawtext import (
    ALLOWED_PREFIXES,
    Entry,
    RawTextRefusal,
    check_text,
    load_manifest,
    pull_raw,
    verify_raw,
)
from horizon_compact.smoke import record

ACCOUNT = "111122223333"
BUCKET = f"horizon-compact-results-{ACCOUNT}"
REPO = Path(__file__).resolve().parents[1]

GRID = "official/company/grid-canary-b-1b2c3d4e/"
PILOT = "pilot/company/pilot-canary-a-0a1b2c3d/"
# A record's real shapes, with canary values: the ARN with the placeholder the writer puts there, a 64-digit
# hash, a run id, a seed longer than twelve digits, a memo with trailing spaces and no final newline.
RECORD = (
    '{\n  "task_arn": "arn:aws:ecs:us-east-1:<account-id>:task/horizon-compact/e31c7106",\n'
    '  "prompt_sha256": "1234567890123456789012345678901234567890123456789012345678901234",\n'
    '  "run_id": "r-100000000001",\n  "menu_order_seed": "14771555503354458442",\n'
    '  "memo": "ZEBRA-MEMO canary words   "\n}'
)
BODIES: dict[str, bytes] = {
    GRID + "manifest.json": b'{"grid": true}\n',
    GRID + "runs/r-100000000001/attempt-1.json": RECORD.encode("utf-8"),
    GRID + "runs/r-100000000001/final.json": b'{"final": 1}\n',
    PILOT + "manifest.json": b'{"pilot": true}\n',
    PILOT + "runs/r-a00000000001/attempt-1.json": "café canary\r\n".encode(),
    "pilot/company/repeats.json": b'{"repeats": 3}\n',
}


def version_of(key: str) -> str:
    return "v-" + hashlib.sha256(key.encode()).hexdigest()[:8]


@dataclass
class Stored:
    key: str
    version_id: str
    body: bytes


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def iter_chunks(self, chunk_size: int = 1024) -> Iterator[bytes]:
        step = min(chunk_size, 5)  # several chunks, so the joining is exercised
        for start in range(0, len(self._data), step):
            yield self._data[start : start + step]


class FakeS3:
    """Just enough of a boto3 S3 client for ``S3RawReader.read``: get_object by version, every call
    recorded. Any other attribute (a put, a copy, a delete) does not exist."""

    def __init__(self, stored: list[Stored]) -> None:
        self.stored = stored
        self.reads: list[tuple[str, str]] = []

    def get_object(self, *, Bucket: str, Key: str, VersionId: str) -> dict[str, Any]:
        assert Bucket == BUCKET
        self.reads.append((Key, VersionId))
        for s in self.stored:
            if s.key == Key and s.version_id == VersionId:
                return {"Body": FakeBody(s.body)}
        raise AssertionError(f"no such version {Key} {VersionId}")  # pragma: no cover


def stored(bodies: dict[str, bytes] | None = None) -> list[Stored]:
    return [Stored(k, version_of(k), b) for k, b in (bodies or BODIES).items()]


def reader(client: FakeS3) -> S3RawReader:
    return S3RawReader(cast("Any", client), BUCKET)


def manifest_text(bodies: dict[str, bytes] | None = None, **override: Any) -> str:
    """A manifest in Phase 1.5's shape, written by hand so these tests do not depend on its builder (one test
    below checks the builder's own output loads)."""
    chosen = bodies or BODIES
    objects = [
        {
            "key": k,
            "bytes": len(chosen[k]),
            "sha256": hashlib.sha256(chosen[k]).hexdigest(),
            "version_id": version_of(k),
            "last_modified": "2026-10-14T12:00:00Z",
        }
        for k in sorted(chosen)
    ]
    head: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "kind": KIND,
        "hash": HASH,
        "prefixes": list(PREFIXES),
        "versioning": "Enabled",
        "object_count": len(objects),
        "total_bytes": sum(o["bytes"] for o in objects),
        "groups": [],
        "objects": objects,
    }
    head.update(override)
    return json.dumps(head, indent=2) + "\n"


def write_manifest(tmp_path: Path, text: str | None = None) -> Path:
    path = tmp_path / "raw-manifest.json"
    path.write_text(text if text is not None else manifest_text(), encoding="utf-8")
    return path


def entries(tmp_path: Path, text: str | None = None) -> tuple[Entry, ...]:
    return load_manifest(write_manifest(tmp_path, text))


def pulled(tmp_path: Path, client: FakeS3 | None = None) -> Path:
    root = tmp_path / "raw"
    pull_raw(reader(client or FakeS3(stored())), entries(tmp_path), root, ACCOUNT)
    return root


# --- the pull --------------------------------------------------------------------------------------


def test_the_pull_writes_every_object_at_its_key_byte_for_byte(tmp_path: Path) -> None:
    root = tmp_path / "raw"
    report = pull_raw(reader(FakeS3(stored())), entries(tmp_path), root, ACCOUNT)
    assert (report.written, report.unchanged) == (len(BODIES), 0)
    assert report.total_bytes == sum(len(b) for b in BODIES.values())
    for key, body in BODIES.items():
        assert (
            root / key
        ).read_bytes() == body  # the CRLF, the trailing spaces, no final newline: all kept
    assert not any(p.name.endswith(".tmp") for p in root.rglob("*"))


def test_a_second_pull_writes_nothing_and_verify_passes(tmp_path: Path) -> None:
    root = pulled(tmp_path)
    again = pull_raw(reader(FakeS3(stored())), entries(tmp_path), root, ACCOUNT)
    assert (again.written, again.unchanged) == (0, len(BODIES))
    report = verify_raw(root, entries(tmp_path))
    assert (report.objects, report.total_bytes) == (
        len(BODIES),
        sum(len(b) for b in BODIES.values()),
    )


def test_the_pull_reads_each_object_at_the_manifest_s_version_and_never_another(
    tmp_path: Path,
) -> None:
    key = GRID + "manifest.json"
    newer = Stored(
        key, "v-newer", b'{"rewritten": true}\n'
    )  # never expected; read only if pinned wrongly
    client = FakeS3([*stored(), newer])
    root = pulled(tmp_path, client)
    assert (root / key).read_bytes() == BODIES[key]
    assert sorted(client.reads) == sorted((k, version_of(k)) for k in BODIES)


def test_the_reader_the_pull_uses_has_no_write_call() -> None:
    for name in ("put_object", "copy_object", "delete_object", "delete_objects"):
        assert not hasattr(FakeS3([]), name)  # so a call to one would fail in every test here
    assert {n for n in vars(S3RawReader) if not n.startswith("_")} == {
        "versioning",
        "list_versions",
        "read",
    }


@pytest.mark.parametrize(
    ("served", "match"),
    [
        (b'{"grid": tru}\n', "bytes, the manifest says"),
        (b'{"grid": TRUE}\n', "its sha256 is not the manifest's"),
    ],
)
def test_the_pull_refuses_bytes_that_differ_from_the_manifest_and_writes_nothing_for_them(
    tmp_path: Path, served: bytes, match: str
) -> None:
    key = GRID + "manifest.json"
    client = FakeS3([s if s.key != key else Stored(key, s.version_id, served) for s in stored()])
    with pytest.raises(RawTextRefusal, match=match):
        pull_raw(reader(client), entries(tmp_path), tmp_path / "raw", ACCOUNT)
    assert not (tmp_path / "raw" / key).exists()


@pytest.mark.parametrize(
    ("body", "match"),
    [
        (f'{{"bucket": "x-{ACCOUNT}"}}'.encode(), "holds the account id"),
        (b'{"by": "canary.person@example.org"}', "an e-mail address"),
        (b'{"account": 444455556666}', "a twelve-digit number standing alone"),
        (b'{"key": "sk-or-v1-abcdefghijklmnop"}', "an API key"),
        (b'{"key": "sk-ant-abcdefghijklmnop"}', "an API key"),
        (b"\xff\xfe not utf-8", "is not UTF-8 text"),
    ],
)
def test_the_pull_refuses_a_file_that_fails_the_write_time_checks_and_writes_nothing_for_it(
    tmp_path: Path, body: bytes, match: str
) -> None:
    bodies = {**BODIES, GRID + "runs/r-100000000001/final.json": body}
    write_manifest(tmp_path, manifest_text(bodies))
    with pytest.raises(RawTextRefusal, match=match):
        pull_raw(
            reader(FakeS3(stored(bodies))),
            load_manifest(tmp_path / "raw-manifest.json"),
            tmp_path / "raw",
            ACCOUNT,
        )
    assert not (tmp_path / "raw" / GRID / "runs/r-100000000001/final.json").exists()


def test_what_the_checks_let_through(tmp_path: Path) -> None:
    check_text(
        "k", RECORD.encode("utf-8"), ACCOUNT
    )  # the placeholder ARN, hashes, run ids, a long seed
    check_text("k", b'{"created": 1791839005, "latency_ms": 41392}')


def test_the_pull_never_overwrites_a_file_that_holds_other_bytes(tmp_path: Path) -> None:
    key = GRID + "manifest.json"
    target = tmp_path / "raw" / key
    target.parent.mkdir(parents=True)
    target.write_bytes(b"something else\n")
    with pytest.raises(RawTextRefusal, match="never overwritten"):
        pull_raw(reader(FakeS3(stored())), entries(tmp_path), tmp_path / "raw", ACCOUNT)
    assert target.read_bytes() == b"something else\n"


def test_progress_is_told_every_five_hundred_objects(tmp_path: Path) -> None:
    bodies = {f"{GRID}runs/r-{n:012x}/final.json": b"{}\n" for n in range(1001)}
    write_manifest(tmp_path, manifest_text(bodies))
    told: list[tuple[int, int]] = []
    pull_raw(
        reader(FakeS3(stored(bodies))),
        load_manifest(tmp_path / "raw-manifest.json"),
        tmp_path / "raw",
        ACCOUNT,
        lambda done, total: told.append((done, total)),
    )
    assert told == [(500, 1001), (1000, 1001)]


# --- the manifest ----------------------------------------------------------------------------------


def load_manifest_text(tmp_path: Path, text: str) -> tuple[Entry, ...]:
    return load_manifest(write_manifest(tmp_path, text))


def test_the_manifest_loads_in_its_own_order(tmp_path: Path) -> None:
    assert [e.key for e in load_manifest_text(tmp_path, manifest_text())] == sorted(BODIES)


def test_the_builder_s_own_output_loads(tmp_path: Path) -> None:
    """The manifest Phase 1.5's builder writes is the one this module reads: built from a fake bucket
    holding the same objects, it loads to the same entries."""

    class Listing:
        def __init__(self, client: FakeS3) -> None:
            self.inner = reader(client)

        def versioning(self) -> str:
            return "Enabled"

        def list_versions(self, prefix: str) -> list[Any]:
            from datetime import UTC, datetime

            from horizon_compact.site.rawmanifest import ObjectVersion

            return [
                ObjectVersion(k, version_of(k), len(b), datetime(2026, 10, 14, tzinfo=UTC), True)
                for k, b in sorted(BODIES.items())
                if k.startswith(prefix)
            ]

        def read(self, key: str, version_id: str) -> Iterator[bytes]:
            return self.inner.read(key, version_id)

    text = build_raw_manifest(Listing(FakeS3(stored())), frozenset({"company"}), BUCKET)
    assert load_manifest_text(tmp_path, text) == load_manifest_text(tmp_path, manifest_text())


def test_the_committed_manifest_loads_and_every_key_is_the_fictional_company_s() -> None:
    loaded = load_manifest(REPO / RAW_MANIFEST_PATH)
    assert len(loaded) == 5247  # Phase 1.5 doc section 19
    assert all(e.key.startswith(ALLOWED_PREFIXES) for e in loaded)


def test_the_allowed_prefixes_sit_inside_the_manifest_s() -> None:
    assert all(p.startswith(PREFIXES) for p in ALLOWED_PREFIXES)


@pytest.mark.parametrize(
    ("override", "match"),
    [
        ({"schema": "something/else"}, "schema"),
        ({"schema_version": 2}, "schema_version"),
        ({"kind": "other"}, "kind"),
        ({"hash": "md5"}, "hash"),
        ({"prefixes": ["official/"]}, "prefixes"),
        ({"object_count": 99}, "objects and lists"),
        ({"total_bytes": 1}, "total_bytes"),
        ({"objects": []}, "lists no objects"),
    ],
)
def test_the_manifest_is_refused_when_it_is_not_phase_1_5_s(
    tmp_path: Path, override: dict[str, Any], match: str
) -> None:
    with pytest.raises(RawTextRefusal, match=match):
        load_manifest_text(tmp_path, manifest_text(**override))


def _objects(**change: Any) -> list[dict[str, Any]]:
    objects = cast("list[dict[str, Any]]", json.loads(manifest_text())["objects"])
    objects[0] = {**objects[0], **change}
    return objects


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (
            {"key": "official/placeholder/grid-canary/manifest.json"},
            "outside the fictional company",
        ),
        ({"key": "cases/closure-canary/dossier.toml"}, "outside the fictional company"),
        ({"key": "official/company/../escape.json"}, "unexpected shape"),
        ({"key": "official/company//double.json"}, "unexpected shape"),
        ({"key": "official/company/dir/"}, "unexpected shape"),
        ({"key": "official/company/sp ace.json"}, "unexpected shape"),
        ({"bytes": -1}, "byte count"),
        ({"bytes": True}, "byte count"),
        ({"sha256": "abc"}, "64 hex digits"),
        ({"version_id": ""}, "no version id"),
    ],
)
def test_a_manifest_entry_of_the_wrong_shape_is_refused(
    tmp_path: Path, change: dict[str, Any], match: str
) -> None:
    objects = _objects(**change)
    with pytest.raises(RawTextRefusal, match=match):
        load_manifest_text(
            tmp_path,
            manifest_text(
                objects=objects,
                object_count=len(objects),
                total_bytes=sum(o["bytes"] for o in objects if not isinstance(o["bytes"], bool)),
            ),
        )


def test_a_manifest_naming_a_key_twice_or_out_of_order_is_refused(tmp_path: Path) -> None:
    objects = cast("list[dict[str, Any]]", json.loads(manifest_text())["objects"])
    twice = [objects[0], *objects]
    with pytest.raises(RawTextRefusal, match="names a key twice"):
        load_manifest_text(
            tmp_path,
            manifest_text(
                objects=twice,
                object_count=len(twice),
                total_bytes=sum(o["bytes"] for o in twice),
            ),
        )
    with pytest.raises(RawTextRefusal, match="not in sorted order"):
        load_manifest_text(tmp_path, manifest_text(objects=list(reversed(objects))))


def test_a_missing_or_unreadable_manifest_is_refused(tmp_path: Path) -> None:
    with pytest.raises(RawTextRefusal, match="no manifest at"):
        load_manifest(tmp_path / "absent.json")
    with pytest.raises(RawTextRefusal, match="not a JSON manifest"):
        load_manifest(write_manifest(tmp_path, "{not json"))
    with pytest.raises(RawTextRefusal, match="not a JSON object"):
        load_manifest(write_manifest(tmp_path, "[]"))


# --- the verify ------------------------------------------------------------------------------------


def test_verify_refuses_when_nothing_is_published(tmp_path: Path) -> None:
    with pytest.raises(RawTextRefusal, match="nothing is published"):
        verify_raw(tmp_path / "raw", entries(tmp_path))


def test_verify_refuses_a_missing_object(tmp_path: Path) -> None:
    root = pulled(tmp_path)
    (root / "pilot/company/repeats.json").unlink()
    with pytest.raises(
        RawTextRefusal, match=r"1 object.* missing, first pilot/company/repeats\.json"
    ):
        verify_raw(root, entries(tmp_path))


@pytest.mark.parametrize(
    "extra", ["official/company/unnamed.json", "pilot/company/.repeats.json.tmp"]
)
def test_verify_refuses_a_file_the_manifest_does_not_name(tmp_path: Path, extra: str) -> None:
    root = pulled(tmp_path)
    (root / extra).write_bytes(b"{}\n")
    with pytest.raises(RawTextRefusal, match="the manifest does not name"):
        verify_raw(root, entries(tmp_path))


def test_verify_refuses_one_changed_byte(tmp_path: Path) -> None:
    root = pulled(tmp_path)
    path = root / GRID / "runs/r-100000000001/attempt-1.json"
    data = bytearray(path.read_bytes())
    data[-2] = ord("X")
    path.write_bytes(bytes(data))
    with pytest.raises(RawTextRefusal, match="its sha256 is not the manifest's"):
        verify_raw(root, entries(tmp_path))


def test_verify_refuses_a_published_file_that_fails_the_write_time_checks(tmp_path: Path) -> None:
    body = b'{"account": 444455556666}'
    bodies = {**BODIES, "pilot/company/repeats.json": body}
    root = tmp_path / "raw"
    for key, data in bodies.items():  # published by hand, past the pull's own checks
        (root / key).parent.mkdir(parents=True, exist_ok=True)
        (root / key).write_bytes(data)
    with pytest.raises(RawTextRefusal, match="twelve-digit number"):
        verify_raw(root, load_manifest(write_manifest(tmp_path, manifest_text(bodies))))


# --- the checks are the writer's ---------------------------------------------------------------------


def test_the_copied_patterns_are_the_writer_s_own() -> None:
    assert rawtext.EMAIL.pattern == record._EMAIL.pattern
    assert rawtext.ACCOUNT_ID_SHAPE.pattern == record._ACCOUNT_ID_SHAPE.pattern
    assert rawtext.API_KEY.pattern == record._API_KEY.pattern


# --- the commands ----------------------------------------------------------------------------------


@pytest.fixture
def aws(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeS3:
    config = tmp_path / "aws-config"
    config.write_text("[profile test]\nregion = us-east-1\n", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.delenv("HC_RESULTS_BUCKET", raising=False)
    client = FakeS3(stored())
    monkeypatch.setattr(cli, "_raw_s3_client", lambda session: client)
    return client


def _pull_argv(tmp_path: Path, *extra: str) -> list[str]:
    return [
        "site",
        "raw-pull",
        "--manifest",
        str(write_manifest(tmp_path)),
        "--root",
        str(tmp_path / "raw"),
        *extra,
    ]


def test_raw_pull_then_raw_verify_end_to_end(
    aws: FakeS3, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(_pull_argv(tmp_path, "--profile", "test", "--bucket", BUCKET)) == CLEAN_EXIT
    total = sum(len(b) for b in BODIES.values())
    assert capsys.readouterr().out.splitlines() == [
        f"into {tmp_path / 'raw'}",
        f"written:   {len(BODIES)}",
        "unchanged: 0",
        f"bytes:     {total}",
    ]
    verify = ["site", "raw-verify", "--manifest", str(tmp_path / "raw-manifest.json")]
    assert main([*verify, "--root", str(tmp_path / "raw")]) == CLEAN_EXIT
    assert capsys.readouterr().out == (
        f"ok: {len(BODIES)} objects, {total} bytes, each matching raw-manifest.json\n"
    )
    (tmp_path / "raw" / "pilot/company/repeats.json").write_bytes(b"{}\n")
    assert main([*verify, "--root", str(tmp_path / "raw")]) == REFUSED_EXIT
    assert capsys.readouterr().err.startswith("refused: ")


def test_raw_pull_needs_a_bucket_whose_name_ends_in_an_account_id_and_a_profile(
    aws: FakeS3, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(_pull_argv(tmp_path, "--profile", "test")) == REFUSED_EXIT
    assert "needs --bucket" in capsys.readouterr().err
    assert main(_pull_argv(tmp_path, "--profile", "test", "--bucket", "no-account")) == REFUSED_EXIT
    assert "does not end in an account id" in capsys.readouterr().err
    assert main(_pull_argv(tmp_path, "--bucket", BUCKET)) == REFUSED_EXIT
    assert "--profile is required" in capsys.readouterr().err
    assert aws.reads == []  # nothing was read
    assert not (tmp_path / "raw").exists()
