"""The memo scan (Phase 5.5 IMPLEMENTATION doc §5.4, K4), on fakes. No model, no AWS, no SEC: the bucket is a
local folder, the runs are written by hand, SEC's list and both providers are scripted, and every company,
word and memo here is a fictional canary (the real term file and cases are private).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.edgar import EdgarClient, Response
from horizon_compact.caseprobe.layout import runs_prefix
from horizon_compact.caseprobe.memos import (
    SEC_TICKERS_URL,
    MemosRefused,
    NamesPreview,
    ReaderPreview,
    ScanResult,
    build_list_net,
    final_text,
    load_term_file_with_hash,
    run_memo_scan,
)
from horizon_compact.privacy.names import parse_term_file
from horizon_compact.protocol.lock import check_lock
from horizon_compact.providers.base import RawDecision, TextRequest
from horizon_compact.reader import memo as memo_reader
from horizon_compact.reader.briefs import FROZEN_PATHS, KINDS, MEMO_KINDS, BriefError, load_brief
from horizon_compact.reader.read import ReaderError
from horizon_compact.sweep.plan import SweepRefusal
from horizon_compact.sweep.store import LocalStore
from test_case_match import (
    HEAD,
    LABEL,
    LINES,
    MODEL,
    OBJECTIVES,
    SWEEP,
    WORDINGS,
    appendix_of,
    make_tree,
)
from test_casebuild_extract import PROVENANCE, ok
from test_casebuild_frozen import fake_git as _fake_git
from test_casebuild_rubric import rubric_text


def fake_git(**kwargs: str) -> Any:
    return _fake_git(**kwargs)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = f"experiment/results/cases/{LABEL}"
TERM = "Fernwick Canary Holdings"  # a term-file canary
SEC_NAME = "Quillfeather Canary"  # on SEC's fake list as "QUILLFEATHER CANARY INC."
MODEL_NAME = "Gleamwood"  # known only to the fake model net
TICKER = "ZQXT"
REASONING = "REASONING-CANARY-DO-NOT-READ"
SEC_LIST = {
    "0": {"cik_str": 1, "ticker": "ZZQ", "title": "QUILLFEATHER CANARY INC."},
    "1": {"cik_str": 2, "ticker": TICKER, "title": "Zorp Canary Ltd"},
    "2": {"cik_str": 3, "ticker": "AB", "title": "Ab Corp"},
}

CLEAN = "We should close the plant and move the work. The Company keeps its best staff."
# Run n (1-based) gets a scripted final attempt; the rest get CLEAN-like memos.
SPECS: dict[int, tuple[str, str]] = {
    1: ("memo", f"Following the lead of {TERM}, we close the plant."),
    2: ("memo", f"{SEC_NAME} supplies the resin we use, so we keep that line."),
    3: ("memo", f"{MODEL_NAME} leads the sector, so we close the plant."),
    4: ("reply", "A reply with no tool call, so its text blocks are what is scanned."),
    5: ("nomemo", ""),
    6: ("failed", f"A failed final attempt that still mentions {TERM}."),
    7: ("memo", f"Sell it to the buyer (NYSE: {TICKER}) and be done."),
}


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def write_memo_sweep(
    store: LocalStore,
    *,
    repeats: int = 2,
    specs: dict[int, tuple[str, str]] | None = None,
    sweep_id: str = SWEEP,
) -> list[str]:
    """A finished case sweep whose runs carry scripted texts. Returns the run ids in order."""
    scripted = SPECS if specs is None else specs
    prefix = runs_prefix(LABEL, sweep_id)
    planned: list[dict[str, Any]] = []
    for objective in OBJECTIVES:
        for wording in WORDINGS:
            for repeat in range(1, repeats + 1):
                planned.append(
                    {
                        "run_id": f"r-{len(planned) + 1:012x}",
                        "scenario_id": "s3",
                        "objective_id": objective,
                        "wording_id": wording,
                        "repeat": repeat,
                    }
                )
    manifest = {
        "sweep_id": sweep_id,
        "label": "case",
        "experiment": f"case-{LABEL}",
        "model_key": MODEL,
        "scenarios": ["s3"],
        "runs": planned,
    }
    store.put_new(f"{prefix}manifest.json", json.dumps(manifest))
    for n, run in enumerate(planned, start=1):
        kind, text = scripted.get(n, ("memo", f"{CLEAN} Run {n}."))
        status = "schema_invalid" if kind == "failed" else "valid"
        amounts = {
            "eliminated": 190,
            "moved_other_plants": 0,
            "kept_at_plant": 0,
            "transferred_to_buyer": 0,
        }
        attempt: dict[str, Any] = {
            "status": status,
            "attempt": 1,
            "scenario_id": "s3",
            "objective_id": run["objective_id"],
            "menu_order": list(LINES),
            "option_order": ["close", "retool", "sell"],
            "validation": {"amounts": amounts, "choice": "close"} if status == "valid" else None,
            "tool_calls": [],
            "text_blocks": [],
            "reasoning_block_count": 1,
            "raw_response": {"reasoning": REASONING},
        }
        if kind in ("memo", "failed"):
            attempt["tool_calls"] = [
                {"name": "decide", "input": {"amounts": amounts, "memo": text}}
            ]
        elif kind == "nomemo":
            attempt["tool_calls"] = [{"name": "decide", "input": {"amounts": amounts}}]
        else:
            attempt["text_blocks"] = [text, "  "]
        final = {"status": status, "final_attempt": 1, "first_attempt_status": status}
        base = f"{prefix}runs/{run['run_id']}/"
        store.put_new(f"{base}attempt-1.json", json.dumps(attempt))
        store.put_new(f"{base}final.json", json.dumps(final))
    return [run["run_id"] for run in planned]


class Scripted:
    """A fake provider: ``respond(request, call_number)`` makes the decision; every request is kept."""

    name = "fake"

    def __init__(self, respond: Callable[[TextRequest, int], RawDecision]) -> None:
        self.respond = respond
        self.requests: list[TextRequest] = []

    def text_request_body(self, request: TextRequest) -> dict[str, Any]:
        return {"model": request.route.model_id}

    def decide_text(self, request: TextRequest) -> RawDecision:
        self.requests.append(request)
        return self.respond(request, len(self.requests))


def api_error() -> RawDecision:
    return RawDecision(
        status="api_error", provenance=PROVENANCE, error={"code": "Boom", "message": "m"}
    )


def haiku(known: tuple[str, ...] = (MODEL_NAME,)) -> Scripted:
    """The model net: lists each known name that a memo of the batch holds."""

    def respond(request: TextRequest, call: int) -> RawDecision:
        found = dict(
            re.findall(
                r"\[memo (m\d+)\]\n(.*?)\n\[end of memo m\d+\]", request.user, flags=re.DOTALL
            )
        )
        reply = {"memos": {i: [n for n in known if n in text] for i, text in found.items()}}
        return ok(json.dumps(reply))

    return Scripted(respond)


def reader(says: Callable[[str, list[str]], str] = lambda text, words: "no") -> Scripted:
    """The independent reader: ``says(memo, words)`` is its answer for every flagged word and for the memo."""

    def respond(request: TextRequest, call: int) -> RawDecision:
        memo = re.search(r"\[Memo\]\n(.*?)\n\[end of Memo\]", request.user, flags=re.DOTALL)
        listed = re.search(
            r"\[Flagged words\]\n(.*?)\n\[end of Flagged words\]", request.user, flags=re.DOTALL
        )
        assert memo is not None and listed is not None
        words = (
            []
            if listed.group(1) == "(none)"
            else [w.split(". ", 1)[1] for w in listed.group(1).split("\n")]
        )
        answer = says(memo.group(1), words)
        flags = [
            {"flag": n, "names_a_real_company": answer, "reason": "why"}
            for n in range(1, len(words) + 1)
        ]
        return ok(json.dumps({"flags": flags, "memo": answer}))

    return Scripted(respond)


def names_a(text: str, words: list[str]) -> str:
    """A reader that confirms a name wherever a canary company is written, and clears the rest."""
    return "yes" if any(n in text for n in (TERM, SEC_NAME, MODEL_NAME)) else "no"


class Fake:
    """Everything a scan needs, with the providers and prompts it was given."""

    def __init__(self, root: Path, store: LocalStore, names: Scripted, read: Scripted) -> None:
        self.root, self.store, self.names, self.read = root, store, names, read
        self.previews: list[Any] = []
        self.made: list[str] = []
        self.answer = True

    def confirm_names(self, preview: NamesPreview) -> bool:
        self.previews.append(preview)
        return self.answer

    def confirm_reader(self, preview: ReaderPreview) -> bool:
        self.previews.append(preview)
        return self.answer

    def names_provider(self) -> Scripted:
        self.made.append("names")
        return self.names

    def reader_provider(self) -> Scripted:
        self.made.append("reader")
        return self.read


def transport() -> Any:
    class Transport:
        def __init__(self) -> None:
            self.urls: list[str] = []

        def get(self, url: str, headers: Any) -> Response:
            self.urls.append(url)
            return Response(200, json.dumps(SEC_LIST).encode("utf-8"))

    return Transport()


def scan(fake: Fake, *, sweep_id: str = SWEEP, git: Any = None) -> ScanResult:
    root = fake.root
    sec = EdgarClient(
        appendix=CaseAppendix(appendix_of(root), LABEL),
        transport=transport(),
        user_agent="Test Agent test@example.com",
    )
    return run_memo_scan(
        root,
        fake.store,
        LABEL,
        MODEL,
        sweep_id,
        appendix=appendix_of(root),
        head=HEAD,
        git=git or fake_git(),
        sec=sec,
        confirm_names=fake.confirm_names,
        confirm_reader=fake.confirm_reader,
        make_names_provider=fake.names_provider,
        make_reader_provider=fake.reader_provider,
    )


def refused(fake: Fake, **kwargs: Any) -> str:
    with pytest.raises(SweepRefusal) as caught:  # MemosRefused, or the matcher's own refusal
        scan(fake, **kwargs)
    return str(caught.value)


@pytest.fixture(autouse=True)
def _term_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The private term file the guard finds, with one canary term."""
    longlist = tmp_path / "longlist.md"
    longlist.write_text("a fictional longlist\n", encoding="utf-8")
    digest = hashlib.sha256(longlist.read_bytes()).hexdigest()
    terms = tmp_path / "terms.txt"
    terms.write_text(
        f"longlist: {longlist}\nlonglist-sha256: {digest}\nterm: {TERM}\n", encoding="utf-8"
    )
    monkeypatch.setenv("HC_NAME_GUARD_TERMS", str(terms))
    monkeypatch.setenv("HC_APPENDIX_DIR", str(tmp_path / "appendix"))


def make_world(
    tmp_path: Path,
    *,
    repeats: int = 2,
    specs: dict[int, tuple[str, str]] | None = None,
    names: Scripted | None = None,
    read: Scripted | None = None,
    results: bool = True,
) -> Fake:
    root, store = make_tree(tmp_path, rubric_text())
    shutil.copytree(ROOT / "experiment" / "readers", root / "experiment" / "readers")
    write_memo_sweep(store, repeats=repeats, specs=specs)
    if results:
        write(root, f"{RESULTS}/{MODEL}.json", "{}\n")
    return Fake(root, store, names or haiku(), read or reader(names_a))


@pytest.fixture
def world(tmp_path: Path) -> Fake:
    return make_world(tmp_path)


def public(root: Path) -> list[dict[str, Any]]:
    path = root / RESULTS / f"{MODEL}-memos.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def summary(root: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        (root / RESULTS / f"{MODEL}-memos-summary.json").read_text(encoding="utf-8")
    )
    return loaded


def by_run(root: Path) -> dict[str, dict[str, Any]]:
    return {line["run_id"]: line for line in public(root)}


def run_id(n: int) -> str:
    return f"r-{n:012x}"


def records(root: Path, pattern: str) -> list[Path]:
    return sorted((appendix_of(root) / LABEL).glob(pattern))


# --- the briefs and the reader's pure side --------------------------------------------------------------


def test_the_memo_briefs_are_read_beside_the_reader_kinds_and_not_as_one_of_them() -> None:
    assert MEMO_KINDS == ("memo-names", "memo") and not set(MEMO_KINDS) & set(KINDS)
    for kind in MEMO_KINDS:
        brief = load_brief(ROOT, kind)
        assert brief.name == f"{kind}.txt" and len(brief.sha256) == 64
        assert "objective" not in brief.text.lower()  # no objective in a brief
    assert (
        "experiment/readers" in FROZEN_PATHS
    )  # so the briefs are committed and pushed before a read
    with pytest.raises(BriefError, match="not a kind of read"):
        load_brief(ROOT, "grid")


def test_hc_case_reader_cannot_take_a_memo_kind(tmp_path: Path) -> None:
    from horizon_compact.casebuild.appendix import CaseAppendix as Case
    from horizon_compact.reader.read import run_read

    case = Case(tmp_path, "closure-1")
    with pytest.raises(ReaderError, match="not a kind of read"):
        run_read(
            case,
            "memo",
            None,
            repo_root=ROOT,
            git=fake_git(),
            search=case,
            confirm=lambda preview: True,
            make_provider=lambda: pytest.fail("no provider"),
        )


def test_a_batch_is_sent_under_opaque_positions_and_nothing_else() -> None:
    sent = memo_reader.names_material(["first text", "second text"])
    assert sent.user == (
        "[memo m1]\nfirst text\n[end of memo m1]\n\n[memo m2]\nsecond text\n[end of memo m2]"
    )
    assert memo_reader.batch_ids(3) == ("m1", "m2", "m3") and list(sent.parts) == ["Memos"]


def test_a_names_reply_must_account_for_every_id_and_only_those() -> None:
    ids = memo_reader.batch_ids(2)
    got, problem = memo_reader.parse_names_reply('{"memos": {"m1": [" X ", " "], "m2": []}}', ids)
    assert got == {"m1": ["X"], "m2": []} and problem is None
    for text in (
        '{"memos": {"m1": []}}',
        '{"memos": {"m1": [], "m2": [], "m3": []}}',
        '{"memos": {"m1": "none", "m2": []}}',
        "no json at all",
    ):
        assert memo_reader.parse_names_reply(text, ids)[0] is None


def test_a_memo_reply_must_answer_every_flag_once_and_the_memo() -> None:
    def reply(flags: list[tuple[int, str]], memo: str) -> str:
        entries = [{"flag": n, "names_a_real_company": a, "reason": "r"} for n, a in flags]
        return json.dumps({"flags": entries, "memo": memo})

    confirmed, _ = memo_reader.parse_memo_reply(reply([(1, "no"), (2, "yes")], "no"), 2)
    assert confirmed is not None and confirmed.verdict == memo_reader.CONFIRMED
    unclear, _ = memo_reader.parse_memo_reply(reply([(1, "cannot_tell")], "no"), 1)
    assert unclear is not None and unclear.verdict == memo_reader.UNCLEAR
    cleared, _ = memo_reader.parse_memo_reply(reply([], "no"), 0)
    assert cleared is not None and cleared.verdict == memo_reader.CLEARED
    elsewhere, _ = memo_reader.parse_memo_reply(reply([(1, "no")], "yes"), 1)
    assert elsewhere is not None and elsewhere.verdict == memo_reader.CONFIRMED
    for flags, count in (([(1, "no")], 2), ([(1, "no"), (1, "no")], 2), ([(2, "no")], 1)):
        assert memo_reader.parse_memo_reply(reply(flags, "no"), count)[0] is None
    assert memo_reader.parse_memo_reply('{"flags": [], "memo": "maybe"}', 0)[0] is None


def test_the_reader_is_shown_the_memo_and_the_numbered_words_and_nothing_else() -> None:
    sent = memo_reader.memo_material("the memo text", ["Alpha", "Beta"])
    assert sent.user == (
        "[Memo]\nthe memo text\n[end of Memo]\n\n[Flagged words]\n1. Alpha\n2. Beta\n[end of Flagged words]"
    )
    assert "(none)" in memo_reader.memo_material("t", []).user


# --- the lists net --------------------------------------------------------------------------------------


def net() -> Any:
    term_file = parse_term_file(f"longlist: /x\nlonglist-sha256: {'0' * 64}\nterm: {TERM}\n")
    return build_list_net(term_file, json.dumps(SEC_LIST).encode("utf-8"))


def test_the_term_file_flags_a_canary_and_matches_whole_words_only() -> None:
    assert net().words_in(f"as {TERM} did") == [TERM]
    assert (
        net().words_in(f"as {TERM}ly or X{TERM} did") == []
    )  # a term inside a longer word is no hit
    assert net().words_in(f"as {TERM.lower()} did") == []  # case-sensitive


def test_sec_names_are_stripped_of_their_legal_form_and_matched_in_both_casings() -> None:
    got = net()
    assert got.words_in(f"{SEC_NAME} won") == [SEC_NAME]
    assert got.words_in("QUILLFEATHER CANARY won") == ["QUILLFEATHER CANARY"]
    assert got.words_in("quillfeather canary won") == []  # case-sensitive
    assert got.words_in("Zorp Canary won") == ["Zorp Canary"]  # "Ltd" stripped
    assert got.words_in("Quillfeatherly Canary won") == []  # whole words


def test_a_short_name_is_dropped_and_a_ticker_counts_only_where_marked_in_capitals() -> None:
    got = net()
    assert got.words_in("Ab Corp ab was here") == []  # "Ab" is under four characters
    assert got.words_in(f"sell to {TICKER} now") == []  # bare: the model net's to find
    assert got.words_in("an AB deal") == []  # a short ticker bare is an ordinary word in capitals
    for marked, ticker in (
        (f"(NYSE: {TICKER})", TICKER),
        (f"Nasdaq {TICKER}", TICKER),
        (f"NYSE American: {TICKER}", TICKER),
        (f"${TICKER} rose", TICKER),
        (f"ticker symbol {TICKER}", TICKER),
        (f"Ticker: {TICKER}", TICKER),
        ("(NYSE: AB)", "AB"),  # a short ticker, marked, counts
    ):
        assert got.words_in(f"sell to the buyer {marked} now") == [ticker], marked
    assert got.words_in(f"sell to (NYSE: {TICKER.lower()}) now") == []  # capitals only
    assert got.words_in(f"(NYSE: {TICKER}X) or ${TICKER}y") == []  # whole words
    assert got.words_in("(NYSE: QQQZ)") == []  # marked, but not on SEC's list


def test_a_list_of_filers_of_another_shape_is_refused() -> None:
    term_file = parse_term_file(f"longlist: /x\nlonglist-sha256: {'0' * 64}\nterm: {TERM}\n")
    for body in (b"[1, 2]", b"{}", b'{"0": {"ticker": "A"}}', b"not json"):
        with pytest.raises(MemosRefused, match="SEC's list"):
            build_list_net(term_file, body)


def test_the_term_file_is_found_as_the_guard_finds_it_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    term_file, digest = load_term_file_with_hash()
    assert term_file.terms and len(digest) == 64
    monkeypatch.setenv("HC_NAME_GUARD_TERMS", str(tmp_path / "missing.txt"))
    with pytest.raises(MemosRefused, match="term file cannot be used"):
        load_term_file_with_hash()


# --- which texts are scanned ----------------------------------------------------------------------------


def test_the_tool_calls_memo_or_a_replys_text_blocks_are_scanned_and_nothing_else() -> None:
    call = {"tool_calls": [{"input": {"memo": "the memo", "amounts": {}}}], "text_blocks": ["side"]}
    assert final_text(call) == ("memo", "the memo")  # a reply with a tool call: the memo alone
    assert final_text({"tool_calls": [], "text_blocks": ["one", " ", "two"]}) == (
        "reply_text",
        "one\n\ntwo",
    )
    assert final_text({"tool_calls": [{"input": {"amounts": {}}}], "text_blocks": ["x"]}) == (
        None,
        None,
    )
    assert final_text({"tool_calls": [], "text_blocks": [" "]}) == (None, None)
    assert final_text({"tool_calls": [{"input": {"memo": " "}}]}) == (None, None)


def test_every_run_has_a_line_and_reasoning_is_never_in_a_request_or_a_file(world: Fake) -> None:
    scan(world)
    lines = by_run(world.root)
    assert len(lines) == 30
    assert lines[run_id(4)]["source"] == "reply_text" and lines[run_id(4)]["memo"] == SPECS[4][1]
    assert (
        lines[run_id(5)]["source"] is None and lines[run_id(5)]["memo"] is None
    )  # no memo written
    failed = lines[run_id(6)]  # a failed final is scanned, and here confirmed and held
    assert failed["status"] == "schema_invalid" and failed["memo"] == "held"
    assert set(lines[run_id(1)]) == {"run_id", "objective", "wording", "status", "source", "memo"}
    sent = " ".join(r.user for p in (world.names, world.read) for r in p.requests)
    on_disk = " ".join(
        p.read_text("utf-8") for p in (appendix_of(world.root) / LABEL).glob("memos-*")
    )
    public_text = (world.root / RESULTS / f"{MODEL}-memos.jsonl").read_text("utf-8")
    for text in (sent, on_disk, public_text):
        assert REASONING not in text


# --- the nets, the reader and what is held --------------------------------------------------------------


def test_each_net_flags_and_the_reader_decides(world: Fake) -> None:
    result = scan(world)
    lines = by_run(world.root)
    assert lines[run_id(1)]["memo"] == "held"  # the term file's canary, confirmed by the reader
    assert lines[run_id(2)]["memo"] == "held"  # SEC's list, confirmed
    assert lines[run_id(3)]["memo"] == "held"  # only the model net saw it, confirmed
    assert lines[run_id(7)]["memo"] == SPECS[7][1]  # a ticker the reader cleared is published
    assert lines[run_id(8)]["memo"] == f"{CLEAN} Run 8."  # unflagged: published as written
    counts = result.counts
    assert counts["runs"] == 30 and counts["with_text"] == 29 and counts["without_text"] == 1
    assert counts["flagged_by_lists"] == 4 and counts["flagged_by_model"] == 1
    assert counts["flagged"] == 5 and counts["flagged_by_both"] == 0
    assert counts["reader_confirmed"] == 4 and counts["reader_cleared"] == 1
    assert counts["held"] == 4 and counts["held_by_reason"]["name_confirmed"] == 4
    assert counts["published"] == 25 and counts["overruled"] == 0
    assert summary(world.root)["counts"] == counts


def test_the_reader_is_shown_each_flagged_memo_with_its_words_and_nothing_of_the_run(
    world: Fake,
) -> None:
    scan(world)
    assert len(world.read.requests) == 5
    users = [r.user for r in world.read.requests]
    assert any(f"1. {TERM}" in u for u in users) and any(f"1. {MODEL_NAME}" in u for u in users)
    assert all(u.startswith("[Memo]\n") for u in users)
    for request in world.read.requests:
        assert request.system == load_brief(ROOT, "memo").text
        for banned in (
            SWEEP,
            LABEL,
            "r-0",
            MODEL,
            "objective",
        ):  # nothing of the run, the case or the dossier
            assert banned not in request.user


def test_a_memo_the_reader_calls_unclear_is_held_and_one_it_cannot_answer_is_held(
    tmp_path: Path,
) -> None:
    def says(text: str, words: list[str]) -> str:
        return "cannot_tell"

    fake = make_world(tmp_path, read=reader(says), specs={1: SPECS[1]}, repeats=1)
    result = scan(fake)
    assert result.counts["held_by_reason"]["reader_unclear"] == 1
    assert by_run(fake.root)[run_id(1)]["memo"] == "held"


def test_a_reader_that_never_gives_a_usable_reply_holds_the_memo_after_three_attempts(
    tmp_path: Path,
) -> None:
    bad = Scripted(lambda request, call: ok("this is not json"))
    fake = make_world(tmp_path, read=bad, specs={1: SPECS[1]}, repeats=1)
    result = scan(fake)
    assert len(bad.requests) == 3  # the reader's three attempts, and no more
    assert result.counts["held_by_reason"]["reader_no_reply"] == 1
    assert by_run(fake.root)[run_id(1)]["memo"] == "held"


# --- the model net's batches ----------------------------------------------------------------------------


def test_a_batch_that_does_not_account_for_every_memo_is_asked_again_once_then_flags_them_all(
    tmp_path: Path,
) -> None:
    lost = Scripted(lambda request, call: ok('{"memos": {"m1": []}}'))
    fake = make_world(tmp_path, names=lost, repeats=1, specs={})
    result = scan(fake)
    assert len(lost.requests) == 2 and lost.requests[0].user == lost.requests[1].user
    assert result.counts["model_net_unaccounted"] == 15 and result.counts["flagged"] == 15
    assert len(fake.read.requests) == 15
    assert all(
        "(none)" in r.user for r in fake.read.requests
    )  # no word was flagged, the memo is judged whole


def test_a_second_try_that_accounts_for_the_batch_stands(tmp_path: Path) -> None:
    good = haiku().respond

    def respond(request: TextRequest, call: int) -> RawDecision:
        return ok('{"memos": {}}') if call == 1 else good(request, call)

    names = Scripted(respond)
    fake = make_world(tmp_path, names=names, repeats=1, specs={3: SPECS[3]})
    result = scan(fake)
    assert len(names.requests) == 2
    assert result.counts["model_net_unaccounted"] == 0 and result.counts["flagged_by_model"] == 1


def test_batches_hold_at_most_25_memos_under_opaque_ids_that_carry_no_run_or_objective(
    world: Fake,
) -> None:
    scan(world)
    assert len(world.names.requests) == 2  # 29 memos with text: 25 and 4
    seen: list[int] = []
    for request in world.names.requests:
        ids = re.findall(r"\[memo (\S+)\]", request.user)
        assert ids == [f"m{n}" for n in range(1, len(ids) + 1)]
        seen.append(len(ids))
        assert "r-0" not in request.user  # no run id
    assert sorted(seen) == [4, 25]
    for path in records(world.root, "memos-*-request.json"):
        record = json.loads(path.read_text("utf-8"))
        assert "objective" not in json.dumps(record).lower()
        assert record["brief_sha256"] in (
            load_brief(ROOT, "memo-names").sha256,
            load_brief(ROOT, "memo").sha256,
        )


def test_the_shuffle_is_fixed_by_the_scan_so_a_rerun_asks_the_same_questions(
    tmp_path: Path,
) -> None:
    first = make_world(tmp_path / "a")
    scan(first)
    second = make_world(tmp_path / "b")
    scan(second)
    assert [r.user for r in first.names.requests] == [r.user for r in second.names.requests]


# --- the files ------------------------------------------------------------------------------------------


def test_the_summary_counts_by_reason_and_records_where_the_scan_came_from(world: Fake) -> None:
    scan(world)
    got = summary(world.root)
    assert got["case"] == LABEL and got["exploratory"] is True and got["sweep_id"] == SWEEP
    assert got["counts"]["held_by_reason"] == {
        "name_confirmed": 4,
        "reader_unclear": 0,
        "reader_no_reply": 0,
        "overruled": 0,
    }
    provenance = got["provenance"]
    assert provenance["head"] == HEAD and provenance["protocol_check"] == "ok"
    assert provenance["names_brief_sha256"] == load_brief(ROOT, "memo-names").sha256
    assert provenance["memo_brief_sha256"] == load_brief(ROOT, "memo").sha256
    assert (
        provenance["sec_list_sha256"] == hashlib.sha256(json.dumps(SEC_LIST).encode()).hexdigest()
    )
    assert provenance["overrules_sha256"] is None
    assert check_lock(world.root).ok  # the lock still holds


def test_a_held_memos_text_and_the_flagged_words_appear_nowhere_public(world: Fake) -> None:
    scan(world)
    public_text = " ".join(
        (world.root / RESULTS / f"{MODEL}-{name}").read_text("utf-8")
        for name in ("memos.jsonl", "memos-summary.json")
    )
    for secret in (TERM, SEC_NAME, MODEL_NAME, SPECS[1][1], SPECS[6][1]):
        assert secret not in public_text
    assert TERM in " ".join(
        p.read_text("utf-8") for p in records(world.root, "memos-*")
    )  # the appendix has it


def test_the_results_file_match_wrote_is_left_alone(world: Fake) -> None:
    path = world.root / RESULTS / f"{MODEL}.json"
    scan(world)
    assert path.read_text("utf-8") == "{}\n"


@pytest.mark.parametrize("name", ["memos.jsonl", "memos-summary.json"])
def test_each_public_file_is_refused_if_it_exists_and_nothing_is_sent(
    world: Fake, name: str
) -> None:
    write(world.root, f"{RESULTS}/{MODEL}-{name}", "kept\n")
    assert "never overwritten" in refused(world)
    assert world.made == [] and not records(world.root, "memos-*")
    assert (world.root / RESULTS / f"{MODEL}-{name}").read_text("utf-8") == "kept\n"


def test_the_command_refuses_before_the_results_file_exists(tmp_path: Path) -> None:
    fake = make_world(tmp_path, results=False)
    assert "runs after the reveal" in refused(fake)
    assert fake.made == [] and fake.names.requests == [] and not records(fake.root, "memos-*")


def test_a_dirty_tree_is_refused_by_the_command(
    world: Fake, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "default_repo_root", lambda: world.root)
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: world.store)
    monkeypatch.setattr(
        cli, "_git", lambda *args: " M src/horizon_compact/cli.py" if args[0] == "status" else HEAD
    )
    argv = ["case", "memos", LABEL, "--model", MODEL, "--sweep", SWEEP, "--profile", "p", "--yes"]
    assert cli.main(argv) == 2
    assert "differ from HEAD" in capsys.readouterr().err
    assert not (world.root / RESULTS / f"{MODEL}-memos.jsonl").exists()


def test_uncommitted_briefs_are_refused_before_anything_is_sent(world: Fake) -> None:
    with pytest.raises(Exception, match="uncommitted"):
        scan(world, git=fake_git(status=" M experiment/readers/memo.txt\n"))
    assert world.made == [] and not records(world.root, "memos-*")


def test_a_sweep_that_is_not_the_cases_or_not_finished_is_refused(tmp_path: Path) -> None:
    fake = make_world(tmp_path)
    assert "no readable manifest" in refused(fake, sweep_id="sw-other001")
    assert fake.made == []


# --- spend ----------------------------------------------------------------------------------------------


def test_declining_the_first_question_sends_nothing_and_asks_for_no_key(world: Fake) -> None:
    world.answer = False
    assert "not confirmed" in refused(world)
    assert world.made == [] and world.names.requests == [] and not records(world.root, "memos-*")
    assert isinstance(world.previews[0], NamesPreview) and len(world.previews) == 1


def test_declining_the_second_question_sends_nothing_to_the_reader(world: Fake) -> None:
    def confirm_reader(preview: ReaderPreview) -> bool:
        world.previews.append(preview)
        return False

    world.confirm_reader = confirm_reader  # type: ignore[method-assign]
    assert "not confirmed" in refused(world)
    assert world.made == ["names"] and world.read.requests == []
    assert not records(world.root, "memos-*-read-*")
    assert not (world.root / RESULTS / f"{MODEL}-memos.jsonl").exists()


def test_the_questions_show_counts_and_money_and_no_word(world: Fake) -> None:
    scan(world)
    names, read = world.previews
    assert names.memos == 29 and names.batches == 2 and names.calls_at_most == 4
    assert names.flagged_by_lists == 4 and names.worst_case_usd > 0
    assert read.memos == 5 and read.retries_worst_case_usd >= read.worst_case_usd > 0
    assert all(TERM not in repr(p) for p in world.previews)


def test_a_rerun_from_the_records_asks_nothing_and_sends_nothing(world: Fake) -> None:
    scan(world)
    before = (len(world.names.requests), len(world.read.requests))
    for name in ("memos.jsonl", "memos-summary.json"):
        (world.root / RESULTS / f"{MODEL}-{name}").unlink()
    world.previews.clear()
    world.confirm_names = lambda p: pytest.fail("no question")  # type: ignore[method-assign,assignment]
    world.confirm_reader = lambda p: pytest.fail("no question")  # type: ignore[method-assign,assignment]
    world.made.clear()
    again = scan(world)
    assert (len(world.names.requests), len(world.read.requests)) == before and world.made == []
    assert again.cost_usd == 0 and again.counts["held"] == 4


# --- his overrules --------------------------------------------------------------------------------------


def overrule(root: Path, body: str) -> None:
    path = appendix_of(root) / LABEL / f"memo-overrules-{MODEL}.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def rerun_without_public_files(world: Fake) -> ScanResult:
    for name in ("memos.jsonl", "memos-summary.json"):
        (world.root / RESULTS / f"{MODEL}-{name}").unlink()
    return scan(world)


def test_an_overrule_holds_a_memo_the_reader_cleared_and_is_logged_with_its_reason(
    world: Fake,
) -> None:
    scan(world)
    assert by_run(world.root)[run_id(7)]["memo"] == SPECS[7][1]
    overrule(
        world.root, f'[[overrule]]\nrun_id = "{run_id(7)}"\nreason = "OVERRULE-REASON-CANARY"\n'
    )
    result = rerun_without_public_files(world)
    assert by_run(world.root)[run_id(7)]["memo"] == "held"
    assert result.counts["overruled"] == 1 and result.counts["held_by_reason"]["overruled"] == 1
    assert result.counts["published"] == 24
    log = records(world.root, "memos-*-overrules-*.json")
    assert len(log) == 1
    logged = json.loads(log[0].read_text("utf-8"))["overrules"]
    assert logged == [
        {"run_id": run_id(7), "reason": "OVERRULE-REASON-CANARY", "held_a_published_memo": True}
    ]
    assert summary(world.root)["provenance"]["overrules_sha256"] is not None
    assert "OVERRULE-REASON-CANARY" not in (
        world.root / RESULTS / f"{MODEL}-memos.jsonl"
    ).read_text("utf-8")


def test_an_overrule_of_a_memo_already_held_changes_nothing_and_is_not_counted(world: Fake) -> None:
    scan(world)
    overrule(world.root, f'[[overrule]]\nrun_id = "{run_id(1)}"\nreason = "agree"\n')
    result = rerun_without_public_files(world)
    assert result.counts["overruled"] == 0 and result.counts["held"] == 4


def test_an_overrule_toward_publishing_is_refused_and_the_command_stops(world: Fake) -> None:
    scan(world)
    overrule(
        world.root,
        f'[[overrule]]\nrun_id = "{run_id(1)}"\naction = "publish"\nreason = "OVERRULE-REASON-CANARY"\n',
    )
    for name in ("memos.jsonl", "memos-summary.json"):
        (world.root / RESULTS / f"{MODEL}-{name}").unlink()
    message = refused(world)
    assert "can only hold" in message and "OVERRULE-REASON-CANARY" not in message
    assert not (world.root / RESULTS / f"{MODEL}-memos.jsonl").exists()


@pytest.mark.parametrize(
    ("body", "words"),
    [
        ('[[overrule]]\nrun_id = "r-ffffffffffff"\nreason = "x"\n', "names no memo"),
        (f'[[overrule]]\nrun_id = "{run_id(5)}"\nreason = "x"\n', "names no memo"),  # wrote no text
        (f'[[overrule]]\nrun_id = "{run_id(8)}"\nreason = " "\n', "needs a run_id and a reason"),
        (
            f'[[overrule]]\nrun_id = "{run_id(8)}"\nreason = "a"\n'
            f'[[overrule]]\nrun_id = "{run_id(8)}"\nreason = "b"\n',
            "two entries",
        ),
        (f'[[overrule]]\nrun_id = "{run_id(8)}"\nreason = "x"\nextra = 1\n', "keys other than"),
        ("memo = 1\n", "holds"),
        ("this is not toml [", "cannot be read"),
    ],
)
def test_a_bad_overrule_file_is_refused_before_anything_is_spent(
    tmp_path: Path, body: str, words: str
) -> None:
    fake = make_world(tmp_path)
    overrule(fake.root, body)
    assert words in refused(fake)
    assert fake.made == [] and not records(fake.root, "memos-*-names-*")


# --- the records ----------------------------------------------------------------------------------------


def test_a_request_with_no_reply_is_refused_until_he_has_looked(world: Fake) -> None:
    scan(world)
    for name in ("memos.jsonl", "memos-summary.json"):
        (world.root / RESULTS / f"{MODEL}-{name}").unlink()
    reply = records(world.root, "memos-*-names-001-1-reply.json")[0]
    reply.unlink()
    assert "no reply" in refused(world)


def test_a_failed_call_stops_the_run_and_a_rerun_goes_on_from_the_records(tmp_path: Path) -> None:
    good = haiku().respond

    def respond(request: TextRequest, call: int) -> RawDecision:
        return api_error() if call == 2 else good(request, call)

    names = Scripted(respond)
    fake = make_world(tmp_path, names=names)
    assert "a call failed (Boom)" in refused(fake)
    assert not (fake.root / RESULTS / f"{MODEL}-memos.jsonl").exists()
    result = scan(
        fake
    )  # the failed call was not an attempt: the batch is asked again and accounted for
    assert result.counts["model_net_unaccounted"] == 0
    assert len(names.requests) == 3  # batch one, batch two (failed), batch two again


def test_a_rerun_whose_flags_differ_from_the_first_runs_is_refused(world: Fake) -> None:
    scan(world)
    flags = records(world.root, "memos-*-flags.json")[0]
    record = json.loads(flags.read_text("utf-8"))
    record["memos"][run_id(8)]["lists"] = ["Invented"]
    flags.write_text(json.dumps(record), encoding="utf-8")
    for name in ("memos.jsonl", "memos-summary.json"):
        (world.root / RESULTS / f"{MODEL}-{name}").unlink()
    assert "differs from what this run found" in refused(world)


def test_a_rerun_after_a_term_file_edit_that_flags_nothing_new_goes_on(world: Fake) -> None:
    scan(world)
    flags = records(world.root, "memos-*-flags.json")[0]
    record = json.loads(flags.read_text("utf-8"))
    record["lists"]["term_file_sha256"] = "0" * 64  # the file changed, but no memo's flags did
    flags.write_text(json.dumps(record), encoding="utf-8")
    for name in ("memos.jsonl", "memos-summary.json"):
        (world.root / RESULTS / f"{MODEL}-{name}").unlink()
    scan(world)
    assert (world.root / RESULTS / f"{MODEL}-memos.jsonl").exists()


def test_sec_is_fetched_once_through_the_one_client_and_its_hash_is_in_the_appendix(
    world: Fake,
) -> None:
    scan(world)
    flags = json.loads(records(world.root, "memos-*-flags.json")[0].read_text("utf-8"))
    assert flags["lists"]["sec_sha256"] == hashlib.sha256(json.dumps(SEC_LIST).encode()).hexdigest()
    assert len(records(world.root, "cache/*.json")) == 1 and SEC_TICKERS_URL.startswith(
        "https://www.sec.gov/"
    )


def test_every_request_record_holds_the_brief_hash_and_is_written_before_its_reply(
    world: Fake,
) -> None:
    scan(world)
    for request in records(world.root, "memos-*-request.json"):
        record = json.loads(request.read_text("utf-8"))
        assert len(record["brief_sha256"]) == 64 and record["frozen"]["reader_inputs_commit"]
        assert request.with_name(request.name.replace("-request.", "-reply.")).exists()


# --- the command line -----------------------------------------------------------------------------------


def test_the_command_prints_counts_and_never_a_word_or_a_memo(
    world: Fake, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "default_repo_root", lambda: world.root)
    monkeypatch.setattr(cli, "_case_bucket_store", lambda args: world.store)
    monkeypatch.setattr(cli, "_git", lambda *args: "" if args[0] == "status" else HEAD)
    monkeypatch.setattr(cli, "git_in", lambda root: fake_git())
    monkeypatch.setattr(cli, "_memo_names_provider", world.names_provider)
    monkeypatch.setattr(cli, "_reader_provider", world.reader_provider)
    monkeypatch.setattr(cli, "sec_user_agent", lambda: "Test Agent test@example.com")
    monkeypatch.setattr(cli, "UrllibTransport", transport)
    argv = ["case", "memos", LABEL, "--model", MODEL, "--sweep", SWEEP, "--profile", "p", "--yes"]
    assert cli.main(argv) == 0
    captured = capsys.readouterr()
    out = captured.out + captured.err
    assert f"wrote {RESULTS}/{MODEL}-memos.jsonl" in out and "held back: 4" in out
    assert "flagged by the lists: 4; by the model: 1" in out
    secrets = (TERM, SEC_NAME, MODEL_NAME, TICKER, *(text for _, text in SPECS.values() if text))
    for secret in secrets:
        assert secret not in out
    assert cli.main(argv) == 2  # the files exist: refused, and the refusal holds no word either
    assert all(secret not in capsys.readouterr().err for secret in secrets)


def test_the_command_is_a_sweep_refusal_so_the_command_line_needs_no_scipy() -> None:
    assert issubclass(MemosRefused, SweepRefusal)


def test_the_precommit_size_exclusion_admits_the_memo_files_under_cases_only() -> None:
    config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    found = re.search(r"id: check-added-large-files.*?exclude: (\S+)", config, flags=re.DOTALL)
    assert found is not None
    pattern = re.compile(found.group(1))
    for allowed in (
        f"{RESULTS}/{MODEL}-memos.jsonl",
        f"{RESULTS}/{MODEL}-memos-summary.json",
        f"{RESULTS}/{MODEL}.json",
    ):
        assert pattern.search(allowed)
    for other in (
        "experiment/results/analysis/x.jsonl",
        f"{RESULTS}/deep/{MODEL}-memos.jsonl",
        "docs/x.jsonl",
    ):
        assert not pattern.search(other)
