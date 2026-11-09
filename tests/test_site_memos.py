"""The grid memo extract and ``hc site memos`` (Phase 6 IMPLEMENTATION doc 5.3, decision 4, section 23).

Every sweep, run, memo and term here is a fictional canary in the real key shapes, served by a fake reader
that holds bytes in memory. Nothing touches a network. The last group of tests reads the committed
``web/explorer-memos/`` and skips until his run has written it: after that, CI runs it, and it is the
reviewer's offline check that every memo line traces to an object in ``raw-manifest.json`` and that the counts
agree with the committed results files.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest

from horizon_compact import cli
from horizon_compact.cli import CLEAN_EXIT, REFUSED_EXIT, main
from horizon_compact.privacy.names import TermFile, find_terms, parse_term_file
from horizon_compact.site import memos
from horizon_compact.site.memos import (
    MemoExtractRefusal,
    build_memo_extract,
    memo_extract_matches,
    write_memo_extract,
)

REPO = Path(__file__).resolve().parent.parent
REAL_OUT = REPO / "web" / "explorer-memos"
REAL_RESULTS = REPO / "experiment" / "results" / "prereg-v1"
REAL_MANIFEST = REPO / "docs" / "phases" / "evidence" / "phase-4" / "raw-manifest.json"

HEAD = "0123456789abcdef0123456789abcdef01234567"
BUCKET = "horizon-compact-results-111122223333"
CANARY_NAME = "Zebracorp Holdings"  # the fictional term the fixture's term file holds
NOT_UTF8 = b"\xff\xfe\x00 not utf-8 \x80\x81"
POISON = b'{"poisoned": "this is a later write to the key"}\n'

MODELS = ("alpha-model", "haiku-5-5")
SCENARIOS = ("s1", "s2")
OBJECTIVES = ("A", "B")
WORDINGS = ("w1", "w2")
REPEATS = (1, 2)

# (kind, model_key, hex) -> the sweep id is f"{kind}-{model_key}-{hex}"
SWEEPS = (
    ("grid", "alpha-model", "aaaa0001"),
    ("grid", "haiku-5-5", "bbbb0002"),
    ("thinking", "haiku-5-5", "cccc0003"),
)

Obj = dict[str, Any]


def _term_file() -> TermFile:
    return parse_term_file(
        f"longlist: /nowhere/longlist.md\nlonglist-sha256: {'0' * 64}\nterm: {CANARY_NAME}\n"
    )


TERMS = _term_file()


def sweep_id(kind: str, model: str, hexid: str) -> str:
    return f"{kind}-{model}-{hexid}"


def official(sid: str) -> str:
    return f"official/company/{sid}/"


def _dump(value: Any) -> bytes:
    return (json.dumps(value, indent=1) + "\n").encode("utf-8")


# --- the fixture world ------------------------------------------------------------------------------------


@dataclass
class RunSpec:
    run_id: str
    scenario_id: str
    objective_id: str
    wording_id: str
    repeat: int
    kind: str  # one of the behaviours below
    memo: str | None


@dataclass
class World:
    root: Path
    objects: dict[str, bytes] = field(default_factory=dict)
    runs: dict[str, list[RunSpec]] = field(default_factory=dict)  # sweep id -> runs
    versions: dict[str, str] = field(
        default_factory=dict
    )  # key -> the version id the manifest records

    @property
    def results(self) -> Path:
        return self.root / "experiment" / "results"

    @property
    def manifest_path(self) -> Path:
        return self.root / "docs" / "phases" / "evidence" / "phase-4" / "raw-manifest.json"

    def put(self, key: str, data: bytes) -> None:
        self.objects[key] = data
        self.versions[key] = f"v-{len(self.versions):05d}"

    def reader(self) -> FakeReader:
        return FakeReader(self)

    def manifest(self) -> Obj:
        return cast("Obj", json.loads(self.manifest_path.read_text(encoding="utf-8")))

    def edit_manifest(self, change: Callable[[Obj], None]) -> None:
        data = self.manifest()
        change(data)
        self.manifest_path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

    def results_file(self, kind: str, model: str) -> Path:
        folder = self.results / "prereg-v1" / model
        return next(folder.glob(f"{kind}-*.json"))

    def edit_results(self, kind: str, model: str, change: Callable[[Obj], None]) -> None:
        path = self.results_file(kind, model)
        data = json.loads(path.read_text(encoding="utf-8"))
        change(data)
        path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


class FakeReader:
    """A byte reader over the world. Each key has the version the manifest records, and a later one holding
    other bytes: a read by any other version id would see them. Every call is recorded."""

    def __init__(self, world: World) -> None:
        self.world = world
        self.calls: list[tuple[str, str]] = []

    def read(self, key: str, version_id: str) -> Iterator[bytes]:
        self.calls.append((key, version_id))
        data = self.world.objects[key] if version_id == self.world.versions[key] else POISON
        for start in range(0, len(data), 64):  # several chunks, so the streaming is exercised
            yield data[start : start + 64]


def _behaviour(index: int) -> str:
    return (
        "retried",
        "reply_text",
        "no_text",
        "rescaled",
        "refusal",
        "plain",
        "plain",
        "plain",
    )[index % 8]


def _blocks(text: str | None) -> list[str]:
    """A reply as the model returned it: its paragraphs as blocks, with a blank block between them."""
    blocks: list[str] = []
    for number, part in enumerate((text or "").split("\n\n")):
        if number:
            blocks.append("  ")
        blocks.append(part)
    return blocks if text else []


def _attempt(spec: RunSpec, number: int, status: str, memo_given: bool, text: str | None) -> Obj:
    record: Obj = {
        "attempt": number,
        "status": status,
        "scenario_id": spec.scenario_id,
        "objective_id": spec.objective_id,
        "menu_order": ["x", "y"],
        "option_order": ["y", "x"],
        "possible_decline": False,
        "reasoning_block_count": 0,
        "tool_calls": [{"name": "decide", "input": {"memo": text}}] if memo_given else [],
        "text_blocks": [] if memo_given else _blocks(text),
    }
    if status in ("valid", "valid_rescaled"):
        record["validation"] = {
            "choice": "x",
            "amounts": {"x": 1.0},
            "scaled_amounts": {"x": 0.5} if status == "valid_rescaled" else None,
        }
    return record


def _put_sweep(world: World, kind: str, model: str, hexid: str) -> None:
    sid = sweep_id(kind, model, hexid)
    prefix = official(sid)
    specs: list[RunSpec] = []
    index = 0
    for scenario in SCENARIOS:
        for objective in OBJECTIVES:
            for wording in WORDINGS:
                for repeat in REPEATS:
                    run_id = "r-" + hashlib.sha1(f"{sid}-{index}".encode()).hexdigest()[:12]
                    behaviour = _behaviour(index)
                    memo: str | None = f"canary memo {sid} {index}"
                    if behaviour == "no_text":
                        memo = None
                    elif behaviour in ("reply_text", "refusal"):
                        memo = f"canary reply {sid} {index}\n\ncanary second paragraph"
                    specs.append(
                        RunSpec(run_id, scenario, objective, wording, repeat, behaviour, memo)
                    )
                    index += 1
    world.runs[sid] = specs
    planned = [
        {
            "run_id": s.run_id,
            "scenario_id": s.scenario_id,
            "objective_id": s.objective_id,
            "wording_id": s.wording_id,
            "repeat": s.repeat,
        }
        for s in specs
    ]
    world.put(
        f"{prefix}manifest.json",
        _dump({"sweep_id": sid, "model_key": model, "runs": planned}),
    )
    world.put(f"{prefix}refusal-calls.meta.json", NOT_UTF8)  # read and checked, never decoded
    for spec in specs:
        base = f"{prefix}runs/{spec.run_id}/"
        if spec.kind == "retried":
            world.put(
                f"{base}attempt-1.json",
                _dump(_attempt(spec, 1, "invalid_schema", True, "FIRST-TRY canary memo")),
            )
            world.put(f"{base}attempt-2.json", _dump(_attempt(spec, 2, "valid", True, spec.memo)))
            final = {
                "status": "valid",
                "final_attempt": 2,
                "first_attempt_status": "invalid_schema",
            }
        elif spec.kind == "reply_text":
            world.put(
                f"{base}attempt-1.json",
                _dump(_attempt(spec, 1, "no_tool_call", False, spec.memo)),
            )
            final = {
                "status": "no_tool_call",
                "final_attempt": 1,
                "first_attempt_status": "no_tool_call",
            }
        elif spec.kind == "no_text":
            world.put(f"{base}attempt-1.json", _dump(_attempt(spec, 1, "valid", True, "   ")))
            final = {"status": "valid", "final_attempt": 1, "first_attempt_status": "valid"}
        elif spec.kind == "refusal":
            world.put(
                f"{base}attempt-1.json", _dump(_attempt(spec, 1, "refusal", False, spec.memo))
            )
            final = {"status": "refusal", "final_attempt": 1, "first_attempt_status": "refusal"}
        else:
            status = "valid_rescaled" if spec.kind == "rescaled" else "valid"
            world.put(f"{base}attempt-1.json", _dump(_attempt(spec, 1, status, True, spec.memo)))
            final = {"status": status, "final_attempt": 1, "first_attempt_status": status}
        world.put(f"{base}final.json", _dump(final))


def _status_of(spec: RunSpec) -> str:
    return {
        "retried": "valid",
        "reply_text": "no_tool_call",
        "no_text": "valid",
        "rescaled": "valid_rescaled",
        "refusal": "refusal",
    }.get(spec.kind, "valid")


def _results_file(kind: str, model: str, hexid: str, specs: list[RunSpec]) -> Obj:
    scenarios = []
    for scenario in SCENARIOS:
        cells: list[Obj] = []
        per_run: list[Obj] = []
        for objective in OBJECTIVES:
            for wording in WORDINGS:
                members = [
                    s
                    for s in specs
                    if (s.scenario_id, s.objective_id, s.wording_id)
                    == (scenario, objective, wording)
                ]
                valid = [s for s in members if _status_of(s) in ("valid", "valid_rescaled")]
                cells.append(
                    {
                        "model_key": model,
                        "scenario_id": scenario,
                        "objective_id": objective,
                        "wording_id": wording,
                        "attempted": len(members),
                        "valid": len(valid),
                        "rescaled": sum(1 for s in valid if s.kind == "rescaled"),
                        "refused": sum(1 for s in members if s.kind == "refusal"),
                        "failed_by_type": [],
                    }
                )
                per_run.extend(
                    {
                        "run_id": s.run_id,
                        "objective_id": s.objective_id,
                        "wording_id": s.wording_id,
                        "repeat": s.repeat,
                        "choice": "x",
                    }
                    for s in valid
                )
        scenarios.append(
            {
                "scenario_id": scenario,
                "cells": cells,
                "descriptive": {"scenario_id": scenario, "runs": len(per_run), "per_run": per_run},
            }
        )
    return {
        "results_version": 2,
        "experiment": "company",
        "sweep_id": sweep_id(kind, model, hexid),
        "model_key": model,
        "scenarios": scenarios,
    }


def write_manifest(world: World) -> None:
    """The raw manifest as Phase 1.5 writes it: one entry per object, one group per prefix."""
    objects = [
        {
            "key": key,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "version_id": world.versions[key],
            "last_modified": "2026-10-14T12:00:00Z",
        }
        for key, data in sorted(world.objects.items())
    ]
    groups = []
    for prefix in sorted(
        {k[: -len("manifest.json")] for k in world.objects if k.endswith("/manifest.json")}
    ):
        mine = [o for o in objects if str(o["key"]).startswith(prefix)]
        groups.append(
            {
                "prefix": prefix,
                "objects": len(mine),
                "bytes": sum(len(world.objects[str(o["key"])]) for o in mine),
                "attempt_objects": 0,
                "final_objects": sum(1 for o in mine if str(o["key"]).endswith("/final.json")),
            }
        )
    world.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    world.manifest_path.write_text(
        json.dumps({"schema_version": 1, "groups": groups, "objects": objects}, indent=1) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def world(tmp_path: Path) -> World:
    w = World(tmp_path / "repo")
    for kind, model, hexid in SWEEPS:
        _put_sweep(w, kind, model, hexid)
        folder = w.results / "prereg-v1" / model
        folder.mkdir(parents=True, exist_ok=True)
        sid = sweep_id(kind, model, hexid)
        (folder / f"{sid}.json").write_text(
            json.dumps(_results_file(kind, model, hexid, w.runs[sid]), indent=1) + "\n",
            encoding="utf-8",
        )
    # Objects the extract must never read: a pilot sweep, an awareness sweep, and a case-shaped prefix.
    w.put("pilot/company/pilot-alpha-model-1f75b653/manifest.json", b'{"pilot": true}\n')
    w.put("official/company/awareness/awareness-alpha-model-6a05acef/manifest.json", b"{}\n")
    w.put("official/company/case-alpha-model-deadbeef/manifest.json", b"{}\n")
    write_manifest(w)
    return w


def build(
    w: World, term_file: TermFile = TERMS, reader: FakeReader | None = None
) -> dict[str, str]:
    return build_memo_extract(reader or w.reader(), w.results, w.manifest_path, term_file, HEAD)


def lines_of(text: str) -> list[Obj]:
    return [json.loads(line) for line in text.split("\n") if line]


def refused(w: World, needle: str, term_file: TermFile = TERMS) -> str:
    with pytest.raises(MemoExtractRefusal) as caught:
        build(w, term_file)
    assert needle in str(caught.value), str(caught.value)
    return str(caught.value)


def _run(w: World, sid: str, kind: str) -> RunSpec:
    return next(s for s in w.runs[sid] if s.kind == kind)


ALPHA = sweep_id(*SWEEPS[0])
HAIKU = sweep_id(*SWEEPS[1])
THINK = sweep_id(*SWEEPS[2])


# --- the output -------------------------------------------------------------------------------------------


def test_the_layout_is_one_file_per_kind_model_scenario_and_objective(world: World) -> None:
    out = build(world)
    expected = {
        f"{kind}/{model}/{scenario}/{objective}.jsonl"
        for kind, model, _hex in SWEEPS
        for scenario in SCENARIOS
        for objective in OBJECTIVES
    }
    assert set(out) == {"index.json", *expected}
    assert all(text.endswith("\n") and not text.endswith("\n\n") for text in out.values())


def test_a_line_carries_the_run_the_memo_and_the_two_objects_it_traces_to(world: World) -> None:
    out = build(world)
    spec = _run(world, HAIKU, "plain")
    path = f"grid/haiku-5-5/{spec.scenario_id}/{spec.objective_id}.jsonl"
    line = next(x for x in lines_of(out[path]) if x["run_id"] == spec.run_id)
    entries = {o["key"]: o for o in world.manifest()["objects"]}
    base = f"{official(HAIKU)}runs/{spec.run_id}/"
    assert list(line) == [
        "run_id",
        "wording_id",
        "repeat",
        "status",
        "source",
        "memo",
        "final",
        "attempt",
    ]
    assert line["wording_id"] == spec.wording_id and line["repeat"] == spec.repeat
    assert line["status"] == "valid" and line["source"] == "memo" and line["memo"] == spec.memo
    assert line["final"] == {
        "key": f"{base}final.json",
        "sha256": entries[f"{base}final.json"]["sha256"],
    }
    assert line["attempt"] == {
        "key": f"{base}attempt-1.json",
        "sha256": entries[f"{base}attempt-1.json"]["sha256"],
    }


def test_the_memo_is_the_final_attempts_and_the_attempt_is_the_final_one(world: World) -> None:
    out = build(world)
    spec = _run(world, ALPHA, "retried")
    path = f"grid/alpha-model/{spec.scenario_id}/{spec.objective_id}.jsonl"
    line = next(x for x in lines_of(out[path]) if x["run_id"] == spec.run_id)
    assert line["memo"] == spec.memo and "FIRST-TRY" not in out[path]
    assert line["attempt"]["key"].endswith(f"{spec.run_id}/attempt-2.json")
    assert line["status"] == "valid"


def test_a_reply_text_run_is_its_text_blocks_and_says_so(world: World) -> None:
    out = build(world)
    spec = _run(world, ALPHA, "reply_text")
    path = f"grid/alpha-model/{spec.scenario_id}/{spec.objective_id}.jsonl"
    line = next(x for x in lines_of(out[path]) if x["run_id"] == spec.run_id)
    assert (line["source"], line["memo"], line["status"]) == (
        "reply_text",
        spec.memo,
        "no_tool_call",
    )


def test_a_run_with_no_text_keeps_its_status_and_has_null_source_and_memo(world: World) -> None:
    out = build(world)
    spec = _run(world, ALPHA, "no_text")
    path = f"grid/alpha-model/{spec.scenario_id}/{spec.objective_id}.jsonl"
    line = next(x for x in lines_of(out[path]) if x["run_id"] == spec.run_id)
    assert (line["source"], line["memo"], line["status"]) == (None, None, "valid")
    index = json.loads(out["index.json"])
    alpha = next(s for s in index["sweeps"] if s["sweep_id"] == ALPHA)
    assert alpha["runs"] == 16 and alpha["with_text"] == 14  # two no-text runs in sixteen


def test_a_refused_run_appears_with_its_status_and_its_text(world: World) -> None:
    out = build(world)
    spec = _run(world, ALPHA, "refusal")
    path = f"grid/alpha-model/{spec.scenario_id}/{spec.objective_id}.jsonl"
    line = next(x for x in lines_of(out[path]) if x["run_id"] == spec.run_id)
    assert (line["status"], line["memo"]) == ("refusal", spec.memo)


def test_lines_are_ordered_by_wording_then_repeat_then_run_id(world: World) -> None:
    out = build(world)
    checked = 0
    for path, text in out.items():
        if path == "index.json":
            continue
        lines = lines_of(text)
        key = [(x["wording_id"], x["repeat"], x["run_id"]) for x in lines]
        assert key == sorted(key)
        checked += 1
    assert checked == 12
    # the fixture is not sorted already: by run id alone the first cell's order would differ
    first = lines_of(out["grid/alpha-model/s1/A.jsonl"])
    assert [x["run_id"] for x in first] != sorted(x["run_id"] for x in first)


def test_a_line_is_compact_json_and_a_memo_is_not_changed(world: World) -> None:
    spec = _run(world, ALPHA, "plain")
    awkward = "Spaced  \t memo\nwith an e-acute \u00e9, and \u2028 and \u0085 and \u2029 inside."
    key = f"{official(ALPHA)}runs/{spec.run_id}/attempt-1.json"
    record = json.loads(world.objects[key])
    record["tool_calls"][0]["input"]["memo"] = awkward
    world.put(key, _dump(record))
    write_manifest(world)
    out = build(world)
    path = f"grid/alpha-model/{spec.scenario_id}/{spec.objective_id}.jsonl"
    for char in ("\u2028", "\u2029", "\u0085"):
        assert char not in out[path]  # written as escapes: no line splitter can cut a line
    assert "\u00e9" in out[path]  # but not everything: ensure_ascii is off
    line = next(x for x in lines_of(out[path]) if x["run_id"] == spec.run_id)
    assert line["memo"] == awkward
    escapes = str.maketrans({"\u0085": "\\u0085", "\u2028": "\\u2028", "\u2029": "\\u2029"})
    for text in out.values():
        for raw in text.split("\n")[:-1]:
            again = json.dumps(
                json.loads(raw), ensure_ascii=False, allow_nan=False, separators=(",", ":")
            )
            assert again.translate(escapes) == raw


def test_the_index_names_the_head_the_manifest_and_every_file(world: World) -> None:
    out = build(world)
    index = json.loads(out["index.json"])
    assert index["explorer_memos_version"] == 1 and index["head"] == HEAD
    assert index["raw_manifest"] == {
        "path": "docs/phases/evidence/phase-4/raw-manifest.json",
        "sha256": hashlib.sha256(world.manifest_path.read_bytes()).hexdigest(),
    }
    assert index["files"] == sorted(p for p in out if p != "index.json")
    assert [(s["kind"], s["model_key"], s["sweep_id"]) for s in index["sweeps"]] == [
        ("grid", "alpha-model", ALPHA),
        ("grid", "haiku-5-5", HAIKU),
        ("thinking", "haiku-5-5", THINK),
    ]
    first = index["sweeps"][0]
    assert first["prefix"] == official(ALPHA) and first["runs"] == 16
    assert first["by_status"] == {"no_tool_call": 2, "refusal": 2, "valid": 10, "valid_rescaled": 2}
    assert out["index.json"].count("\n") == 1  # compact, one line


def test_a_second_build_is_byte_identical(world: World) -> None:
    assert build(world) == build(world)


def test_the_head_must_be_a_commit_id(world: World) -> None:
    with pytest.raises(MemoExtractRefusal, match="40-character"):
        build_memo_extract(world.reader(), world.results, world.manifest_path, TERMS, "main")


# --- what it reads ----------------------------------------------------------------------------------------


def test_it_reads_each_object_by_the_recorded_version_and_nothing_else(world: World) -> None:
    reader = world.reader()
    out = build(world, reader=reader)
    recorded = {o["key"]: o["version_id"] for o in world.manifest()["objects"]}
    assert reader.calls and all(recorded[key] == version for key, version in reader.calls)
    # no later write to a key reached the output
    assert "poisoned" not in "".join(out.values())
    read = {key for key, _v in reader.calls}
    wanted = {k for k in recorded if any(k.startswith(official(s)) for s in (ALPHA, HAIKU, THINK))}
    assert read == wanted  # every object of the three official prefixes, once, and nothing else
    assert len(reader.calls) == len(wanted)
    assert not any(k.startswith(("pilot/", "official/company/awareness/")) for k in read)
    assert not any("case-" in k for k in read)


def test_a_read_of_any_other_version_would_be_refused(world: World) -> None:
    class Latest(FakeReader):
        def read(self, key: str, version_id: str) -> Iterator[bytes]:
            return super().read(key, "the-latest-version")  # the bytes a later write left

    with pytest.raises(MemoExtractRefusal, match=r"sha256|read "):
        build(world, reader=Latest(world))


def test_every_object_is_checked_including_the_ones_the_extract_does_not_use(world: World) -> None:
    world.objects[f"{official(ALPHA)}refusal-calls.meta.json"] = (
        NOT_UTF8 + b"x"
    )  # same key, other bytes
    refused(world, "refusal-calls.meta.json")


def test_a_changed_byte_with_the_same_length_is_refused(world: World) -> None:
    key = f"{official(HAIKU)}runs/{world.runs[HAIKU][0].run_id}/final.json"
    data = bytearray(world.objects[key])
    data[-3] ^= 0x01
    world.objects[key] = bytes(data)
    message = refused(world, "sha256")
    assert key in message


def test_a_different_byte_count_is_refused(world: World) -> None:
    key = f"{official(THINK)}manifest.json"
    world.objects[key] += b" "
    refused(world, "read ")


def test_an_object_that_is_not_utf8_is_refused_when_the_frozen_reader_needs_it(
    world: World,
) -> None:
    key = f"{official(ALPHA)}runs/{world.runs[ALPHA][0].run_id}/attempt-2.json"
    world.put(key, NOT_UTF8)
    write_manifest(world)
    refused(world, "not valid UTF-8")


def test_a_manifest_entry_without_a_version_is_refused(world: World) -> None:
    def drop(data: Obj) -> None:
        del data["objects"][3]["version_id"]

    world.edit_manifest(drop)
    refused(world, "without a key, size, sha256 or version")


def test_an_object_the_manifest_does_not_list_is_not_read_so_a_missing_attempt_is_refused(
    world: World,
) -> None:
    key = f"{official(ALPHA)}runs/{world.runs[ALPHA][3].run_id}/attempt-1.json"

    def drop(data: Obj) -> None:
        data["objects"] = [o for o in data["objects"] if o["key"] != key]

    world.edit_manifest(drop)
    refused(world, "the frozen reader refused")


def test_a_sweep_with_no_object_in_the_manifest_is_refused(world: World) -> None:
    def drop(data: Obj) -> None:
        data["objects"] = [o for o in data["objects"] if not o["key"].startswith(official(THINK))]

    world.edit_manifest(drop)
    refused(world, f"no object under {official(THINK)}")


def test_a_sweep_with_no_group_in_the_manifest_is_refused(world: World) -> None:
    def drop(data: Obj) -> None:
        data["groups"] = [g for g in data["groups"] if g["prefix"] != official(THINK)]

    world.edit_manifest(drop)
    refused(world, f"no group for {official(THINK)}")


# --- the cross-checks -------------------------------------------------------------------------------------


def test_the_run_count_must_equal_the_manifest_groups_final_objects(world: World) -> None:
    def bump(data: Obj) -> None:
        next(g for g in data["groups"] if g["prefix"] == official(HAIKU))["final_objects"] += 1

    world.edit_manifest(bump)
    refused(world, "final.json objects")


def test_a_cell_whose_valid_count_differs_from_the_results_file_is_refused(world: World) -> None:
    def bump(data: Obj) -> None:
        data["scenarios"][1]["cells"][2]["valid"] += 1

    world.edit_results("grid", "alpha-model", bump)
    message = refused(world, "valid runs in the records and")
    assert "scenario s2" in message


def test_a_cell_the_results_file_lacks_is_refused(world: World) -> None:
    def drop(data: Obj) -> None:
        data["scenarios"][0]["cells"].pop(0)

    world.edit_results("grid", "haiku-5-5", drop)
    refused(world, "valid runs in the records and 0 in the results file")


def test_a_per_run_entry_that_is_not_a_valid_run_in_the_extract_is_refused(world: World) -> None:
    refusal = _run(world, HAIKU, "refusal")

    def swap(data: Obj) -> None:
        data["scenarios"][0]["descriptive"]["per_run"][0]["run_id"] = refusal.run_id

    world.edit_results("grid", "haiku-5-5", swap)
    refused(world, "not a valid run in the extract")


def test_a_per_run_entry_for_an_unknown_run_is_refused(world: World) -> None:
    def swap(data: Obj) -> None:
        data["scenarios"][0]["descriptive"]["per_run"][0]["run_id"] = "r-ffffffffffff"

    world.edit_results("thinking", "haiku-5-5", swap)
    refused(world, "r-ffffffffffff")


def test_a_per_run_entry_with_another_wording_is_refused(world: World) -> None:
    def swap(data: Obj) -> None:
        item = data["scenarios"][0]["descriptive"]["per_run"][0]
        item["wording_id"] = "w9"

    world.edit_results("grid", "alpha-model", swap)
    refused(world, "different scenario, objective, wording or repeat")


def test_an_unexpected_file_among_the_results_is_refused(world: World) -> None:
    (world.results / "prereg-v1" / "alpha-model" / "notes.json").write_text("{}", encoding="utf-8")
    refused(world, "not an expected file")


# --- the name guard and the leak checks ------------------------------------------------------------------


def _put_memo(world: World, sid: str, spec: RunSpec, text: str) -> None:
    key = f"{official(sid)}runs/{spec.run_id}/attempt-1.json"
    record = json.loads(world.objects[key])
    record["tool_calls"][0]["input"]["memo"] = text
    world.put(key, _dump(record))
    write_manifest(world)


def test_a_memo_holding_a_term_is_refused_naming_the_run_and_never_the_term(world: World) -> None:
    spec = _run(world, HAIKU, "plain")
    _put_memo(world, HAIKU, spec, f"We should sell the plant to {CANARY_NAME} next year.")
    message = refused(world, spec.run_id)
    assert CANARY_NAME not in message and "Zebracorp" not in message
    assert HAIKU in message and "1 memos" in message


def test_the_term_is_found_in_reply_text_too_and_the_message_lists_each_run(world: World) -> None:
    first = _run(world, HAIKU, "plain")
    other = _run(world, ALPHA, "plain")
    _put_memo(world, HAIKU, first, f"{CANARY_NAME}")
    _put_memo(world, ALPHA, other, f"about {CANARY_NAME}")
    message = refused(world, first.run_id)
    assert other.run_id in message and "2 memos" in message
    assert "zebracorp" not in message.lower()


def test_a_term_in_a_reply_text_run_is_refused(world: World) -> None:
    spec = _run(world, THINK, "reply_text")
    key = f"{official(THINK)}runs/{spec.run_id}/attempt-1.json"
    record = json.loads(world.objects[key])
    record["text_blocks"] = ["fine", f"and then {CANARY_NAME}"]
    world.put(key, _dump(record))
    write_manifest(world)
    message = refused(world, spec.run_id)
    assert CANARY_NAME not in message


@pytest.mark.parametrize(
    "text",
    [
        f"Our plan:\n{CANARY_NAME} buys the plant.",  # written as `\n` + the term: the `n` hides the edge
        "Sell to Zebracorp\nHoldings next year.",  # the two words split by a line break
    ],
)
def test_the_scan_reads_the_memo_because_the_commit_guard_cannot_see_past_an_escape(
    world: World, text: str
) -> None:
    """Review, 2026-11-09 (Opus): the commit guard scans the file as written, where a line break in a memo is
    the two characters backslash and n. A term just after a break then has a letter before it, and a phrase
    split by a break is no longer split by whitespace, so the guard finds neither. The extract's scan of the
    decoded memo is the one that does; this pins it there."""
    as_written = memos._dump({"memo": text}, "x.jsonl")
    assert not find_terms(as_written, TERMS)  # what the commit guard would see: nothing
    assert find_terms(text, TERMS)
    spec = _run(world, HAIKU, "plain")
    _put_memo(world, HAIKU, spec, text)
    refused(world, spec.run_id)


def test_a_term_inside_a_longer_word_is_not_a_hit(world: World) -> None:
    spec = _run(world, HAIKU, "plain")
    _put_memo(world, HAIKU, spec, f"{CANARY_NAME}s and x{CANARY_NAME}")
    build(world)  # the guard's whole-word rule: not a hit


def test_a_memo_holding_an_arn_is_refused(world: World) -> None:
    spec = _run(world, ALPHA, "plain")
    _put_memo(world, ALPHA, spec, "see arn:aws:s3:::somewhere for the table")
    refused(world, "an ARN or the results bucket")


def test_a_memo_holding_the_results_bucket_name_prefix_is_refused(world: World) -> None:
    spec = _run(world, ALPHA, "plain")
    _put_memo(world, ALPHA, spec, "the horizon-compact-results-bucket")
    refused(world, "an ARN or the results bucket")


def test_ordinary_words_ending_in_arn_are_not_an_arn(world: World) -> None:
    spec = _run(world, ALPHA, "plain")
    _put_memo(world, ALPHA, spec, "What we learn: warn: yarn: barn:")
    out = build(world)
    assert "learn:" in out[f"grid/alpha-model/{spec.scenario_id}/{spec.objective_id}.jsonl"]


def test_twelve_digits_in_a_row_are_not_a_leak(world: World) -> None:
    spec = _run(world, ALPHA, "plain")
    _put_memo(world, ALPHA, spec, "a figure of 123456789012 dollars")
    build(world)


# --- the size rule ----------------------------------------------------------------------------------------


def test_a_file_over_the_limit_is_split_by_wording(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    whole = build(world)
    largest = max(len(t.encode("utf-8")) for p, t in whole.items() if p != "index.json")
    monkeypatch.setattr(memos, "MAX_FILE_BYTES", largest - 1)
    split = build(world)
    names = {p for p in split if p != "index.json"}
    assert any(
        re.fullmatch(r"(grid|thinking)/[a-z0-9-]+/s[0-9]+/[AB]-w[12]\.jsonl", p) for p in names
    )
    assert all(len(split[p].encode("utf-8")) <= largest - 1 for p in names)
    # the same runs, in the same order, whichever way the files are cut
    for path, text in whole.items():
        if path == "index.json":
            continue
        stem = path[: -len(".jsonl")]
        parts = [p for p in names if p == path or p.startswith(stem + "-")]
        assert parts
        joined = "".join(split[p] for p in sorted(parts))
        assert sorted(joined.splitlines()) == sorted(text.splitlines())
    assert json.loads(split["index.json"])["files"] == sorted(names)


def test_a_wordings_file_over_the_limit_is_refused(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(memos, "MAX_FILE_BYTES", 300)
    refused(world, "even split by wording")


# --- the writer -------------------------------------------------------------------------------------------


def test_the_writer_replaces_its_folder_whole_and_the_same_bytes_is_a_no_op(
    world: World, tmp_path: Path
) -> None:
    out = tmp_path / "web" / "explorer-memos"
    files = build(world)
    assert not memo_extract_matches(files, out)
    write_memo_extract(files, out)
    assert memo_extract_matches(files, out)
    assert (out / "index.json").read_text(encoding="utf-8") == files["index.json"]
    marker = out / "grid" / "alpha-model" / "s1" / "A.jsonl"
    before = marker.stat().st_mtime_ns
    write_memo_extract(files, out)  # a no-op: nothing is rewritten
    assert marker.stat().st_mtime_ns == before
    # a stale file cannot linger: a smaller extract replaces the larger one
    smaller = {p: t for p, t in files.items() if not p.startswith("thinking/")}
    write_memo_extract(smaller, out)
    assert not (out / "thinking").exists()
    assert {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()} == set(smaller)
    assert not (tmp_path / "web" / ".explorer-memos.new").exists()
    assert not (tmp_path / "web" / ".explorer-memos.old").exists()


def test_the_writer_refuses_an_out_not_named_explorer_memos(tmp_path: Path) -> None:
    with pytest.raises(MemoExtractRefusal, match="must be named explorer-memos"):
        write_memo_extract({"index.json": "{}\n"}, tmp_path / "somewhere-else")


def test_the_writer_refuses_to_replace_a_folder_holding_something_else(tmp_path: Path) -> None:
    out = tmp_path / "explorer-memos"
    out.mkdir()
    (out / "notes.md").write_text("mine\n", encoding="utf-8")
    with pytest.raises(MemoExtractRefusal, match="not a file this command writes"):
        write_memo_extract({"index.json": "{}\n"}, out)
    assert (out / "notes.md").read_text(encoding="utf-8") == "mine\n"


def test_the_writer_refuses_a_file_outside_the_layout_or_without_its_newline(
    tmp_path: Path,
) -> None:
    out = tmp_path / "explorer-memos"
    with pytest.raises(MemoExtractRefusal, match="not in the expected layout"):
        write_memo_extract({"grid/x/s1/A.txt": "x\n"}, out)
    with pytest.raises(MemoExtractRefusal, match="not in the expected layout"):
        write_memo_extract({"../index.json": "x\n"}, out)
    with pytest.raises(MemoExtractRefusal, match="does not end in a newline"):
        write_memo_extract({"index.json": "{}"}, out)
    assert not out.exists()


def test_the_writer_refuses_a_leftover_from_an_earlier_run(tmp_path: Path) -> None:
    (tmp_path / ".explorer-memos.new").mkdir()
    with pytest.raises(MemoExtractRefusal, match="left over"):
        write_memo_extract({"index.json": "{}\n"}, tmp_path / "explorer-memos")


def test_the_writer_puts_the_old_folder_back_if_the_swap_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "explorer-memos"
    write_memo_extract({"index.json": "{}\n"}, out)
    real = Path.rename

    def flaky(self: Path, target: Any) -> Path:
        if self.name == ".explorer-memos.new":
            raise OSError("disk went away")
        return real(self, target)

    monkeypatch.setattr(Path, "rename", flaky)
    with pytest.raises(OSError, match="disk went away"):
        write_memo_extract({"index.json": '{"a":1}\n'}, out)
    monkeypatch.undo()
    assert (out / "index.json").read_text(encoding="utf-8") == "{}\n"
    assert not (tmp_path / ".explorer-memos.new").exists()
    assert not (tmp_path / ".explorer-memos.old").exists()


# --- the command ------------------------------------------------------------------------------------------


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def iter_chunks(self, chunk_size: int = 1024) -> Iterator[bytes]:
        step = min(chunk_size, 50)
        for start in range(0, len(self._data), step):
            yield self._data[start : start + step]


class FakeS3:
    """Just enough of a boto3 S3 client for ``S3RawReader.read``: get_object by version. Recorded."""

    def __init__(self, world: World) -> None:
        self.world = world
        self.calls: list[tuple[str, str]] = []

    def get_object(self, *, Bucket: str, Key: str, VersionId: str) -> dict[str, Any]:
        assert Bucket == BUCKET
        self.calls.append((Key, VersionId))
        data = self.world.objects[Key] if VersionId == self.world.versions[Key] else POISON
        return {"Body": FakeBody(data)}


@dataclass
class Command:
    world: World
    client: FakeS3
    out: Path
    dirty: str = ""

    def argv(self, *extra: str) -> list[str]:
        return [
            "site",
            "memos",
            "--results",
            str(self.world.results),
            "--manifest",
            str(self.world.manifest_path),
            "--out",
            str(self.out),
            *extra,
        ]


@pytest.fixture
def command(world: World, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Command:
    config = tmp_path / "aws-config"
    config.write_text("[profile test]\nregion = us-east-1\n", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config))
    monkeypatch.delenv("HC_RESULTS_BUCKET", raising=False)
    longlist = tmp_path / "longlist.md"
    longlist.write_text("private\n", encoding="utf-8")
    terms = tmp_path / "terms.txt"
    digest = hashlib.sha256(longlist.read_bytes()).hexdigest()
    terms.write_text(
        f"longlist: {longlist}\nlonglist-sha256: {digest}\nterm: {CANARY_NAME}\n", encoding="utf-8"
    )
    monkeypatch.setenv("HC_NAME_GUARD_TERMS", str(terms))
    cmd = Command(world, FakeS3(world), tmp_path / "out" / "explorer-memos")
    monkeypatch.setattr(cli, "_raw_s3_client", lambda session: cmd.client)

    def fake_git(*args: str) -> str:
        if args[0] == "status":
            return cmd.dirty
        if args[:2] == ("rev-parse", "--show-toplevel"):
            return str(world.root)
        return HEAD

    monkeypatch.setattr(cli, "_git", fake_git)
    return cmd


def test_the_command_end_to_end(
    command: Command, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = command.argv("--profile", "test", "--bucket", BUCKET)
    assert main(args) == CLEAN_EXIT
    captured = capsys.readouterr()
    out = command.out
    expected = build(command.world)
    sizes = {p: len(t.encode("utf-8")) for p, t in expected.items()}
    largest = max((p for p in sizes if p != "index.json"), key=lambda p: sizes[p])
    assert captured.out.splitlines() == [
        f"wrote {out}",
        f"files:      {len(expected)}",
        "runs:       48",
        "with text:  42",
        f"bytes:      {sum(sizes.values())}",
        f"largest:    {largest}  {sizes[largest]} bytes",
    ]
    assert "canary" not in captured.out + captured.err  # never a memo's text
    assert memo_extract_matches(expected, out)
    assert command.client.calls
    assert all(version == command.world.versions[key] for key, version in command.client.calls)
    assert main(args) == CLEAN_EXIT  # the same bytes again
    again = capsys.readouterr().out
    assert again.startswith(f"kept {out}") and again.rstrip().endswith("unchanged")


def test_the_command_refuses_uncommitted_code_before_it_reads_anything(
    command: Command, capsys: pytest.CaptureFixture[str]
) -> None:
    command.dirty = " M src/horizon_compact/cli.py"
    assert main(command.argv("--profile", "test", "--bucket", BUCKET)) == REFUSED_EXIT
    err = capsys.readouterr().err
    assert err.startswith("refused: ") and "differ from HEAD" in err
    assert command.client.calls == [] and not command.out.parent.exists()


def test_the_command_refuses_without_the_term_file_before_it_reads_anything(
    command: Command,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HC_NAME_GUARD_TERMS", str(tmp_path / "no-such-term-file"))
    assert main(command.argv("--profile", "test", "--bucket", BUCKET)) == REFUSED_EXIT
    assert capsys.readouterr().err.startswith("refused: ")
    assert command.client.calls == []


def test_the_command_refuses_a_memo_with_a_term_and_writes_nothing(
    command: Command, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = _run(command.world, HAIKU, "plain")
    _put_memo(command.world, HAIKU, spec, f"to {CANARY_NAME}")
    assert main(command.argv("--profile", "test", "--bucket", BUCKET)) == REFUSED_EXIT
    captured = capsys.readouterr()
    assert captured.err.startswith("refused: ") and spec.run_id in captured.err
    assert CANARY_NAME not in captured.out + captured.err
    assert not command.out.parent.exists()


def test_the_command_needs_a_profile_and_a_bucket(
    command: Command, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(command.argv("--bucket", BUCKET)) == REFUSED_EXIT
    assert "--profile is required" in capsys.readouterr().err
    assert main(command.argv("--profile", "test")) == REFUSED_EXIT
    assert "needs --bucket" in capsys.readouterr().err
    assert command.client.calls == []


def test_the_bucket_can_come_from_the_environment(
    command: Command, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HC_RESULTS_BUCKET", BUCKET)
    assert main(command.argv("--profile", "test")) == CLEAN_EXIT


# --- the committed output (skips until his run has written it) --------------------------------------------

committed = pytest.mark.skipif(
    not REAL_OUT.is_dir(),
    reason="web/explorer-memos/ is written by his run of scratch/p6-c2-memos.sh",
)


def _committed_files() -> dict[str, str]:
    return {
        p.relative_to(REAL_OUT).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(REAL_OUT.rglob("*"))
        if p.is_file()
    }


def _results_by_sweep() -> dict[str, tuple[str, dict[str, Any]]]:
    found: dict[str, tuple[str, dict[str, Any]]] = {}
    for path in sorted(REAL_RESULTS.glob("*/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        found[data["sweep_id"]] = (path.name.split("-")[0], data)
    return found


@committed
def test_the_committed_extract_traces_every_line_to_the_manifest() -> None:
    manifest = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
    by_key = {o["key"]: o["sha256"] for o in manifest["objects"]}
    files = _committed_files()
    index = json.loads(files["index.json"])
    assert index["explorer_memos_version"] == 1
    assert re.fullmatch(r"[0-9a-f]{40}", index["head"])
    assert index["raw_manifest"]["sha256"] == hashlib.sha256(REAL_MANIFEST.read_bytes()).hexdigest()
    assert index["files"] == sorted(p for p in files if p != "index.json")
    assert files["index.json"].count("\n") == 1
    prefixes = tuple(s["prefix"] for s in index["sweeps"])
    lines = 0
    for path, text in files.items():
        if path == "index.json":
            continue
        assert text.endswith("\n") and "\N{LINE SEPARATOR}" not in text
        for raw in text.split("\n")[:-1]:
            line = json.loads(raw)
            for part in ("final", "attempt"):
                key = line[part]["key"]
                assert key.startswith(prefixes), key
                assert by_key[key] == line[part]["sha256"], key
            assert line["final"]["key"].endswith(f"{line['run_id']}/final.json")
            assert line["attempt"]["key"].startswith(line["final"]["key"][: -len("final.json")])
            assert (line["source"] is None) == (line["memo"] is None)
            lines += 1
    assert lines == sum(s["runs"] for s in index["sweeps"])


@committed
def test_the_committed_extract_agrees_with_the_committed_results_files() -> None:
    files = _committed_files()
    index = json.loads(files["index.json"])
    results = _results_by_sweep()
    assert {s["sweep_id"] for s in index["sweeps"]} == set(results)
    manifest = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
    finals = {g["prefix"]: g["final_objects"] for g in manifest["groups"]}
    for summary in index["sweeps"]:
        kind, data = results[summary["sweep_id"]]
        assert (summary["kind"], summary["model_key"]) == (kind, data["model_key"])
        assert summary["runs"] == finals[summary["prefix"]]
        folder = f"{summary['kind']}/{summary['model_key']}/"
        runs: dict[str, dict[str, Any]] = {}
        valid: dict[tuple[str, str, str], int] = {}
        for path, text in files.items():
            if not path.startswith(folder):
                continue
            scenario_id, name = path[len(folder) :].split("/")
            objective_id = name[: -len(".jsonl")].split("-")[0]
            for raw in text.split("\n")[:-1]:
                line = json.loads(raw)
                runs[line["run_id"]] = line
                if line["status"] in ("valid", "valid_rescaled"):
                    cell = (scenario_id, objective_id, line["wording_id"])
                    valid[cell] = valid.get(cell, 0) + 1
        assert len(runs) == summary["runs"]
        assert sum(1 for x in runs.values() if x["memo"] is not None) == summary["with_text"]
        expected = {
            (s["scenario_id"], c["objective_id"], c["wording_id"]): c["valid"]
            for s in data["scenarios"]
            for c in s["cells"]
        }
        for cell in set(expected) | set(valid):
            assert valid.get(cell, 0) == expected.get(cell, 0), cell
        for scenario in data["scenarios"]:
            for item in scenario["descriptive"]["per_run"]:
                assert runs[item["run_id"]]["status"] in ("valid", "valid_rescaled")
                assert runs[item["run_id"]]["wording_id"] == item["wording_id"]


@committed
def test_no_committed_memo_file_passes_the_large_file_hooks_limit() -> None:
    for path in sorted(REAL_OUT.rglob("*")):
        if path.is_file():
            assert path.stat().st_size <= memos.MAX_FILE_BYTES, path


@committed
def test_the_committed_extract_holds_no_arn_and_no_bucket_name() -> None:
    for path, text in _committed_files().items():
        assert not re.search(r"(?<![A-Za-z0-9])arn:", text), path
        assert "horizon-compact-results-" not in text, path
