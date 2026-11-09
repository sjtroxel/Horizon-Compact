"""``hc case echoes`` (Phase 6 IMPLEMENTATION doc section 22): the count of published real-case memos that
repeat a distinctive token from their withheld case text. Every name here is a fictional canary; nothing
reads the real appendix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from horizon_compact.caseprobe import echoes
from horizon_compact.caseprobe.echoes import (
    EchoRefusal,
    check_public,
    read_cases,
    run_echo_count,
    tokens,
)

HEAD = "0" * 40

# Case alpha-1: a withheld dossier with two canary words, a percentage, a figure and a dollar amount.
ALPHA_DOSSIER = (
    'title = "Board pack"\n'
    "text = '''Zorvane Works makes quillet tubing and runs the Brindle Ladder program.\n"
    "Margin was 17.25%. Employees at the plant: 93. Liquidity: $174.9 million. Revenue grew 3.5%.\n"
    "Demand for machinery is steady.'''\n"
)
ALPHA_SCENARIO = 'title = "The plant"\ntext = "Plant 6 employs 93 people."\npeople = 93\n'
ALPHA_DESCRIPTION = "A plant closure in a mid-sized business that makes tubing."
BETA_DOSSIER = "text = '''Marrowfield Supply sells quillet parts. Margin 8.1%.'''\n"
BETA_SCENARIO = 'text = "Plant 2."\n'
# The fictional company's text: "machinery", "demand", 3.5% and 125 are reference, never distinctive.
REFERENCE = (
    "text = '''The Company designs machinery. Demand is steady. Revenue growth: 3.5%. "
    "Plant 6 has 125 people. Margin. Employees. Liquidity. Program. Runs. Makes. Plant. "
    "All amounts are in million dollars, and for the year that was.'''\n"
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _memos(path: Path, rows: list[tuple[str, str]]) -> None:
    _write(
        path,
        "".join(
            json.dumps(
                {
                    "memo": memo,
                    "objective": "A",
                    "run_id": run_id,
                    "source": "memo",
                    "status": "valid",
                    "wording": "w1",
                }
            )
            + "\n"
            for run_id, memo in rows
        ),
    )


def make_tree(tmp_path: Path) -> tuple[Path, Path]:
    root, appendix = tmp_path / "repo", tmp_path / "appendix"
    _write(root / "experiment" / "company" / "dossier.toml", REFERENCE)
    _write(root / "experiment" / "results" / "ignored.txt", "zorvane")  # never reference text
    cases: list[dict[str, Any]] = []
    for label, dossier, scenario, description in (
        (
            "alpha-1",
            ALPHA_DOSSIER,
            ALPHA_SCENARIO,
            {"status": "published", "text": ALPHA_DESCRIPTION},
        ),
        (
            "beta-2",
            BETA_DOSSIER,
            BETA_SCENARIO,
            {"status": "withheld", "reason": "withheld: fewer than 20"},
        ),
    ):
        _write(appendix / label / "dossier.toml", dossier)
        _write(appendix / label / "scenario.toml", scenario)
        _write(
            root / "experiment" / "cases" / label / "case.lock",
            f'case_version = 1\nlabel = "{label}"\nprobe_set = 1\n'
            f'dossier_sha256 = "{_sha(dossier)}"\nrubric_sha256 = "{"0" * 64}"\n'
            f'scenario_sha256 = "{_sha(scenario)}"\n',
        )
        cases.append({"label": label, "probe_set": 1, "description": description})
    _write(root / "experiment" / "results" / "cases" / "cases.json", json.dumps({"cases": cases}))
    alpha = root / "experiment" / "results" / "cases" / "alpha-1"
    _memos(
        alpha / "canary-model-memos.jsonl",
        [
            ("r-000000000001", "Keep the quillet line open; the Brindle Ladder program matters."),
            ("r-000000000002", "Margin of 17.25% and all 93 employees argue for retooling."),
            (
                "r-000000000003",
                "Close it. Demand for machinery is steady and liquidity is $174.9 million.",
            ),
            ("r-000000000004", "held"),
            ("r-000000000005", "Revenue growth was 3.5%; the tubing business is steady."),
        ],
    )
    _memos(
        root / "experiment" / "results" / "cases" / "beta-2" / "canary-model-memos.jsonl",
        [("r-000000000011", "Marrowfield should keep the brindle parts plant open at 8.1%.")],
    )
    return root, appendix


def _run(tmp_path: Path) -> tuple[echoes.EchoResult, Path, Path]:
    root, appendix = make_tree(tmp_path)
    result, _path, _wrote = run_echo_count(root, appendix, HEAD)
    return result, root, appendix


def _row(result: echoes.EchoResult, label: str) -> dict[str, Any]:
    row: dict[str, Any] = next(r for r in result.public["counts"] if r["label"] == label)
    return row


def _tokens_of(result: echoes.EchoResult, label: str, kind: str) -> list[str]:
    return [t["token"] for t in result.private[label]["models"]["canary-model"][kind]]


# --- tokens -----------------------------------------------------------------------------------------------


def test_tokens_take_words_percentages_and_figures_and_skip_dollars() -> None:
    found = tokens(
        "Margin 17.250% on 1,093 units; $174.9 million cash; 21.5 million more; 7 plants; ab."
    )
    assert {"margin", "units", "cash", "more", "plants"} <= found["word"]
    assert "ab" not in found["word"]  # under three letters
    assert found["percent"] == {"17.25"}  # trailing zeros dropped
    assert found["figure"] == {
        "1093"
    }  # commas dropped; dollars, scaled amounts and one digit skipped


def test_percent_written_as_a_word_is_a_percentage() -> None:
    assert tokens("a rate of 4.2 percent")["percent"] == {"4.2"}


# --- the rule ---------------------------------------------------------------------------------------------


def test_a_distinctive_word_from_the_withheld_text_is_counted(tmp_path: Path) -> None:
    result, _root, _appendix = _run(tmp_path)
    words = _tokens_of(result, "alpha-1", "word")
    assert words == ["ladder", "quillet"]  # one memo each, then alphabetical


def test_a_word_in_the_reference_text_or_the_published_description_is_not(tmp_path: Path) -> None:
    result, _root, _appendix = _run(tmp_path)
    words = set(_tokens_of(result, "alpha-1", "word"))
    assert "machinery" not in words and "demand" not in words  # the fictional company's text
    assert "tubing" not in words  # in alpha-1's published description


def test_a_word_another_case_s_memos_use_is_not_distinctive(tmp_path: Path) -> None:
    """Both words are in alpha-1's dossier. Beta-2's published memo uses 'brindle', so for alpha-1 it counts
    as ordinary and is dropped; no other case's memo uses 'quillet' or 'ladder', so they stay."""
    result, _root, _appendix = _run(tmp_path)
    words = set(_tokens_of(result, "alpha-1", "word"))
    assert "quillet" in words
    assert "brindle" not in words
    assert "ladder" in words


def test_figures_are_not_filtered_by_other_cases_memos(tmp_path: Path) -> None:
    result, _root, _appendix = _run(tmp_path)
    assert _tokens_of(result, "alpha-1", "percent") == ["17.25"]  # 3.5% is in the reference text
    assert _tokens_of(result, "alpha-1", "figure") == [
        "93"
    ]  # 125 is reference; $174.9 million is skipped


def test_the_counts_per_memo_and_held_memos_skipped(tmp_path: Path) -> None:
    result, _root, _appendix = _run(tmp_path)
    row = _row(result, "alpha-1")
    assert row["published"] == 4 and row["held"] == 1
    assert row["with_word"] == 1  # memo 1 (quillet, ladder); memo 5's "tubing" is described
    assert row["with_percent"] == 1 and row["with_figure"] == 1  # memo 2
    assert (
        row["with_any"] == 2
    )  # memos 1 and 2; memo 3 repeats only reference text and a dollar amount
    assert (
        row["distinct_words"] == 2
        and row["distinct_percents"] == 1
        and row["distinct_figures"] == 1
    )


def test_the_private_report_names_the_runs_for_each_token(tmp_path: Path) -> None:
    result, _root, appendix = _run(tmp_path)
    report = json.loads((appendix / "alpha-1" / "memo-echoes.json").read_text(encoding="utf-8"))
    assert report == json.loads(json.dumps(result.private["alpha-1"]))
    figure = report["models"]["canary-model"]["figure"][0]
    assert figure == {"token": "93", "memos": 1, "run_ids": ["r-000000000002"]}


# --- what is public ---------------------------------------------------------------------------------------


def test_the_public_file_holds_no_token_and_no_memo_text(tmp_path: Path) -> None:
    _result, root, _appendix = _run(tmp_path)
    text = (root / echoes.PUBLIC_PATH).read_text(encoding="utf-8").casefold()
    for canary in ("quillet", "brindle", "ladder", "zorvane", "marrowfield", "17.25", "retooling"):
        assert canary not in text
    public = json.loads(text)
    assert public["method_version"] == echoes.METHOD_VERSION and public["head"] == HEAD
    assert public["reference"]["files"] == 1  # experiment/results/ is never reference text


def test_a_public_string_outside_the_allowed_set_is_refused(tmp_path: Path) -> None:
    root, appendix = make_tree(tmp_path)
    cases = read_cases(root, appendix)
    with pytest.raises(EchoRefusal, match="not allowed"):
        check_public({"counts": [{"label": "alpha-1", "note": "quillet"}]}, cases)


def test_the_public_file_is_written_once(tmp_path: Path) -> None:
    root, appendix = make_tree(tmp_path)
    _result, path, wrote = run_echo_count(root, appendix, HEAD)
    assert wrote
    _result, _path, wrote = run_echo_count(root, appendix, HEAD)
    assert not wrote
    with pytest.raises(EchoRefusal, match="delete it on purpose"):
        run_echo_count(root, appendix, "1" * 40)
    assert json.loads(path.read_text(encoding="utf-8"))["head"] == HEAD


# --- refusals ---------------------------------------------------------------------------------------------


def test_a_dossier_that_does_not_hash_to_the_lock_is_refused(tmp_path: Path) -> None:
    root, appendix = make_tree(tmp_path)
    _write(appendix / "alpha-1" / "dossier.toml", ALPHA_DOSSIER + "# edited\n")
    with pytest.raises(EchoRefusal, match=r"does not hash to case\.lock"):
        run_echo_count(root, appendix, HEAD)
    assert not (root / echoes.PUBLIC_PATH).exists()


def test_a_probe_set_that_disagrees_with_the_lock_is_refused(tmp_path: Path) -> None:
    root, appendix = make_tree(tmp_path)
    index_path = root / "experiment" / "results" / "cases" / "cases.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["cases"][0]["probe_set"] = 2
    index_path.write_text(json.dumps(index), encoding="utf-8")
    with pytest.raises(EchoRefusal, match="probe set"):
        run_echo_count(root, appendix, HEAD)


def test_a_case_with_no_memo_file_is_refused(tmp_path: Path) -> None:
    root, appendix = make_tree(tmp_path)
    (root / "experiment" / "results" / "cases" / "beta-2" / "canary-model-memos.jsonl").unlink()
    with pytest.raises(EchoRefusal, match="no memo file"):
        run_echo_count(root, appendix, HEAD)


def test_a_refusal_message_never_holds_a_token(tmp_path: Path) -> None:
    root, appendix = make_tree(tmp_path)
    _write(appendix / "beta-2" / "scenario.toml", BETA_SCENARIO + "x = 1\n")
    with pytest.raises(EchoRefusal) as caught:
        run_echo_count(root, appendix, HEAD)
    assert "marrowfield" not in str(caught.value).casefold()
