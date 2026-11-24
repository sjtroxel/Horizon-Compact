"""The README's numbers are tested (Phase 7 IMPLEMENTATION doc step 3 and section 5.2, tests 1 to 4).

The pattern is Musical Mycelium's ``tests/test_published_numbers.py``, with the digit census of
``web/src/explorer/methods.test.ts`` added. A marked figure is ``<!-- n:key -->value<!-- /n -->``;
``src/horizon_compact/site/readme_figures.py`` computes every key from the committed explorer data.

The checks run on a skeleton, ``tests/fixtures/readme-skeleton.md``, always, and on ``README.md`` and
``docs/plain-english.md`` whenever they exist (neither did when this file was written; step 4 writes the
first). The skeleton's marked values are placeholders, so test 1 renders it from the data first. If a check
fails on a real file, run ``make readme``; if the diff surprises you, that is the point.

**Out of this file, by his decision of 2026-11-24:** section 5.2's test 5 (the scope sentence waits for his
words at step 4) and section 5.3's audit-ID test (it waits for ``docs/v1-audit.md`` and its format at
step 6).

The last group plants one fault each in a copy of the skeleton, in ``tmp_path``, and asserts the check
reports it. Those tests stay in the suite: a check that cannot fail protects nothing.
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Callable
from pathlib import Path

import pytest

from horizon_compact.site import readme_figures
from horizon_compact.site.readme_figures import (
    EXPLORER_DATA,
    GOVERNED,
    KEYS,
    MARKER,
    MINUS,
    REPO_ROOT,
    ReadmeFiguresRefusal,
    confidence_level,
    figures,
    format_count,
    format_points,
    malformed_markers,
    marked,
    render,
    rewrite,
    run_years,
    stale,
    unknown_keys,
    unmarked_keys,
    whole_points_down,
)

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "readme-skeleton.md"
REAL_FILES = [REPO_ROOT / name for name in GOVERNED if (REPO_ROOT / name).exists()]
TARGETS = [FIXTURE, *REAL_FILES]
TARGET_IDS = [path.name for path in TARGETS]

# --- the digit census ----------------------------------------------------------------------------------

#: Years that are history and not results. The run years come from the data (``run_years``) beside these.
FIXED_YEARS = ("1620", "2019", "2024")

#: Names that hold a digit and are not figures. The cases' labels are added from the data. (The same idea
#: as the methods page's NAMES in methods.test.ts.)
NAMES = ("Haiku 5.5", "gpt-oss-120b", "prereg-v1", "sha256", "CC BY 4.0")

#: Anything else a README may carry unmarked, one entry and one reason each. Keep it short: a number that
#: is a result is marked, not listed here. An entry is added with the step that needs it, never in advance.
ALLOWLIST: dict[str, str] = {
    "S3": "the name of the AWS storage service the write-once records sit in, not a count",
    # Step 4, the README. The scenario briefs are his approved words from web/src/explorer/his.json, and their
    # numbers are the made-up company's design, fixed in the hashed scenario files at the tag: not results.
    "125": "s1's design: the office and finance staff the AI tools could replace (his.json scenarioBriefs)",
    "190": "s3's design: Plant 6's employees (his.json scenarioBriefs)",
    "Plant 6": "s3's plant, by the name the scenario and the site give it",
    "2027": "the year in Haiku 5.5's earliest retirement date, as Anthropic's deprecations page gives it",
}

_MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"

# Each class, in the order it is blanked. A blanked span keeps its length and its newlines, so the line
# numbers in a report are the file's own. The first five hold text that is not prose (code, comments,
# markup, links).
_MASKS: tuple[tuple[str, str, int], ...] = (
    ("fenced code", r"```.*?```", re.DOTALL),
    ("html comment", r"<!--.*?-->", re.DOTALL),
    ("html tag", r"<[A-Za-z/][^>]*>", 0),
    ("link target", r"\]\([^)\n]*\)", 0),
    ("url", r"https?://[^\s)>\]]+", 0),
    # A code span that is a path or a file name (a "/" or a ".ext"): its digits name a file, not a
    # result. A code span that is not (`make check`, `990`) is still read as prose. The pattern finds
    # every code span, left to right, and _blank_if_path blanks only the path-like ones (a pattern that
    # tested for the path inside it would also match the prose between two code spans).
    ("path in code", r"`[^`\n]+`", 0),
    # A date: an ISO date (with a time to the minute), "October 14", "October 29 to October 30". The year
    # after a long date is left to the year pass, so only an allowed year passes ("October 14, 1200" fails).
    ("iso date", r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?: ?UTC|Z)?)?", 0),
    (
        "long date",
        rf"(?:{_MONTHS}) \d{{1,2}}(?!\d)(?: to (?:(?:{_MONTHS}) )?\d{{1,2}}(?!\d))?",
        0,
    ),
    # A protocol or planning reference: a section, a planning doc, a protocol number, a phase or a step of
    # the build. (A build phase is a planning reference; the numbers inside a sentence about it are still
    # checked.)
    ("section", r"§\s?\d+(?:\.\d+)*[a-z]?", 0),
    ("planning doc", r"planning/\d+[a-z]?", 0),
    ("protocol", r"[Pp]rotocol(?: section)? \d+(?:\.\d+)*", 0),
    ("phase or step", r"(?:[Pp]hases?|[Ss]teps?) \d+(?:\.\d+)?", 0),
    # A version: after "v" or the word "version", never a bare decimal (a bare "19.1" is a result).
    ("version", r"(?<![A-Za-z0-9])v\d+(?:\.\d+)*(?![A-Za-z0-9])", 0),
    ("version word", r"(?i:versions?) \d+(?:\.\d+)*", 0),
    # A scenario or a wording as the data names them, s1 to s4 and w1 to w3 (lower case only, so S3 stays
    # the storage service).
    ("scenario or wording", r"(?<![A-Za-z0-9])[sw][1-4](?![A-Za-z0-9])", 0),
)

#: An ordered-list marker ("1. ", "2) ") at the start of a line. It is blanked only where Markdown would
#: render it as a list item: at the start of a block (after a blank line) or after another list line. A
#: hard-wrapped sentence whose next line starts "20. All" or "990." is prose, and its number is checked.
_LIST_MARKER = re.compile(r"[ \t]*\d+[.)](?=[ \t])")
_LIST_LINE = re.compile(r"[ \t]*(?:\d+[.)]|[-*+])[ \t]")


def _blank(match: re.Match[str]) -> str:
    return re.sub(r"[^\n]", " ", match.group(0))


def _blank_if_path(match: re.Match[str]) -> str:
    span = match.group(0)
    return _blank(match) if re.search(r"/|\.[A-Za-z]{1,5}\b", span) else span


_REPLACERS: dict[str, Callable[[re.Match[str]], str]] = {"path in code": _blank_if_path}


def _blank_list_markers(blanked: str, original: list[str]) -> str:
    """Blank each list marker whose line, in the original text, follows a blank line or another list
    line (a list item's indented continuation counts as a list line)."""
    lines = blanked.split("\n")
    for number, line in enumerate(lines):
        marker = _LIST_MARKER.match(line)
        if not marker:
            continue
        previous = original[number - 1] if number else ""
        if not previous.strip() or _LIST_LINE.match(previous) or previous.startswith(("   ", "\t")):
            lines[number] = " " * marker.end() + line[marker.end() :]
    return "\n".join(lines)


def _bounded(literal: str) -> str:
    return rf"(?<![A-Za-z0-9]){re.escape(literal)}(?![A-Za-z0-9])"


def census(text: str, *, years: frozenset[str], names: tuple[str, ...]) -> list[str]:
    """The digits in ``text`` that are not inside a marker and not an allowed class, one line each with
    its line number. An empty list passes."""
    blanked = MARKER.sub(_blank, text)
    for label, pattern, flags in _MASKS:
        blanked = re.sub(pattern, _REPLACERS.get(label, _blank), blanked, flags=flags)
    blanked = _blank_list_markers(blanked, text.split("\n"))
    for name in sorted(names, key=len, reverse=True):
        blanked = re.sub(_bounded(name), _blank, blanked)
    for year in sorted(years):
        blanked = re.sub(rf"(?<![\d.,]){year}(?!\d)", _blank, blanked)
    for entry in ALLOWLIST:
        blanked = re.sub(_bounded(entry), _blank, blanked)
    original = text.splitlines()
    problems: list[str] = []
    for number, line in enumerate(blanked.splitlines(), start=1):
        for match in re.finditer(r"\d[\d.,]*", line):
            shown = original[number - 1].strip()[:90]
            problems.append(f"line {number}: {match.group(0)!r} in {shown!r}")
    return problems


def _case_labels() -> tuple[str, ...]:
    data = REPO_ROOT / EXPLORER_DATA
    index = json.loads((data / "index.json").read_text(encoding="utf-8"))
    cases = json.loads((data / index["files"]["cases"]).read_text(encoding="utf-8"))
    return tuple(case["label"] for case in cases["cases"])


def census_of(text: str) -> list[str]:
    return census(
        text,
        years=frozenset(FIXED_YEARS) | run_years(),
        names=(*NAMES, *_case_labels()),
    )


# --- fixtures ------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def values() -> dict[str, str]:
    return figures()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _rendered_fixture(values: dict[str, str]) -> str:
    return render(_read(FIXTURE), values)


# --- test 1: every marked figure matches its source ----------------------------------------------------


@pytest.mark.parametrize("path", TARGETS, ids=TARGET_IDS)
def test_every_marked_figure_matches_its_source(path: Path, values: dict[str, str]) -> None:
    text = _read(path)
    if path == FIXTURE:
        text = render(text, values)  # its values are placeholders by design
    problems = stale(text, values)
    assert not problems, f"{path.name} has stale figures -- run `make readme`:\n" + "\n".join(
        problems
    )


# --- test 2: every marker names a key the generator computes -------------------------------------------


@pytest.mark.parametrize("path", TARGETS, ids=TARGET_IDS)
def test_every_marker_names_a_figure_the_generator_computes(
    path: Path, values: dict[str, str]
) -> None:
    """A typo in a key would leave a number unprotected while looking protected."""
    text = _read(path)
    assert not malformed_markers(text), f"{path.name}: {malformed_markers(text)}"
    unknown = unknown_keys(text, values)
    assert not unknown, f"{path.name} has markers with no source: {unknown}"


# --- test 3: every key the generator computes is still marked ------------------------------------------


def test_every_key_the_generator_computes_is_marked_in_the_skeleton(values: dict[str, str]) -> None:
    """Deleting a marker and retyping the number by hand must fail somewhere, and this is where. A figure
    that stops being published has to be removed from the generator on purpose."""
    missing = unmarked_keys([_read(FIXTURE)], values)
    assert not missing, f"keys computed but not marked in the skeleton: {missing}"


@pytest.mark.skipif(not REAL_FILES, reason="neither README.md nor docs/plain-english.md exists yet")
def test_every_key_the_generator_computes_is_marked_in_the_real_files(
    values: dict[str, str],
) -> None:
    """Across the governed files together: the plain-English write-up need not carry every figure, the
    pair must."""
    missing = unmarked_keys([_read(path) for path in REAL_FILES], values)
    assert not missing, (
        f"figures computed but not marked in {[p.name for p in REAL_FILES]}: {missing}. "
        "Mark the number, or remove the key from readme_figures.py on purpose."
    )


# --- test 4: the digit census --------------------------------------------------------------------------


@pytest.mark.parametrize("path", TARGETS, ids=TARGET_IDS)
def test_no_digit_stands_outside_a_marker_unless_it_belongs_to_an_allowed_class(path: Path) -> None:
    problems = census_of(_read(path))
    assert not problems, (
        f"{path.name} has digits that are neither marked nor an allowed class (a date, a year, a model "
        "or case name, a section reference, a version, or an ALLOWLIST entry with its reason). Mark the "
        "figure in readme_figures.py, or allow it here with its reason:\n" + "\n".join(problems)
    )


@pytest.mark.parametrize(
    "prose",
    [
        "Run on October 14, 2026, again on 2026-10-15 and on October 29 to October 30, 2026.",
        "The Mayflower Compact of 1620 and the 2019 statement, retrospective of 2024.",
        "Haiku 5.5 and gpt-oss-120b, the prereg-v1 tag, closure-07 and pre-224.",
        "See planning/06 §4 and §4.6.5, protocol 1.5, Phase 6.5, step 3 and v1.0.0 or version 0.6.5.",
        "On s1 and w3 the records sit in S3.",
        "1. A list item.\n2) Another.",
        "Some prose.\n\n1. A list item,\n   wrapped.\n2. Another.",
        "The cut-offs: June 2026 and June 2024.",
        "Run `make setup`, then `make check`, and/or read `docs/v1-audit.md`.",
        "[the audit](docs/v1-audit.md) at https://example.org/a1 and `docs/phases/phase-7/cost.md`.",
        '```\nuv run hc check --cap 25\n```\n<!-- audit:A12 -->\n<img src="x-2.png" width="720">',
        "A figure: <!-- n:grid_runs_haiku -->990<!-- /n --> runs.",
    ],
)
def test_the_census_passes_each_allowed_class(prose: str) -> None:
    assert census_of(prose) == []


@pytest.mark.parametrize(
    "prose",
    [
        "About 41 percent kept their jobs.",
        "It cost $46.",
        "The difference was 19.1 points.",
        "A 99.7% interval.",
        "990 runs.",
        "Over 20 years.",
        "Run in 2031.",
        "Haiku 5.52 and gpt-oss-1200b.",
        "A `990` in code that is not a path.",
        "An unclosed <!-- n:grid_runs_haiku -->990 runs.",
        # Found in Opus's review of step 3: each passed the first census.
        "Run `make setup`, then 41 of the runs and/or more, then `make check`.",
        "Use `uv`, e.g. 41 runs, then `make`.",
        "The grid ran a total of\n990.\n",
        "The readings numbered\n20. All of them were no good match.",
        "On October 14, 1200 runs failed.",
    ],
)
def test_the_census_fails_each_number_that_belongs_to_no_class(prose: str) -> None:
    assert census_of(prose) != []


def test_the_census_reports_the_line_it_found_the_number_on() -> None:
    problems = census_of("First line.\nSecond line, 41 of them.\nThird line.")
    assert len(problems) == 1
    assert problems[0].startswith("line 2: '41'")


# --- the generator's own contract ----------------------------------------------------------------------


def test_the_key_table_and_the_generator_agree_on_the_keys(values: dict[str, str]) -> None:
    assert sorted(values) == sorted(KEYS)
    for key, (source, mirrors) in KEYS.items():
        assert re.fullmatch(r"[a-z][a-z0-9_]*", key), key
        assert source
        assert mirrors, f"{key} names no formatter it mirrors"


def test_the_figures_hold_what_the_sources_hold(values: dict[str, str]) -> None:
    """Pinned to the official results, which are frozen: if the data legitimately changes, these pins and
    the README move together (test_site_explorer already holds the data equal to a fresh build)."""
    assert values["haiku_cd_s1_difference"] == f"{MINUS}19.1"
    assert values["haiku_cd_s1_points_down"] == "19"
    assert values["haiku_cd_s1_interval"] == f"{MINUS}29.3 to {MINUS}9.0"
    assert values["haiku_cd_s1_confidence"] == "99.7%"
    assert values["against_thesis_count"] == "2"
    assert values["cases_exploratory_closures"] == "5"
    assert values["cases_leakage_disclosed"] == "3"


def test_the_run_counts_equal_an_independent_sum_over_the_grid_cells(
    values: dict[str, str],
) -> None:
    """The cells' ``attempted`` against the generator's ``objective_rates`` sum: two fields of the same
    files."""
    data = REPO_ROOT / EXPLORER_DATA
    for model, key in (
        ("haiku-5-5", "grid_runs_haiku"),
        ("gpt-oss-openrouter", "grid_runs_gpt_oss"),
    ):
        total = 0
        for scenario in ("s1", "s2", "s3", "s4"):
            path = data / "grid" / model / f"{scenario}.json"
            grid = json.loads(path.read_text(encoding="utf-8"))
            total += sum(cell["attempted"] for cell in grid["cells"])
        assert values[key] == format_count(total)


def test_the_case_counts_equal_a_count_from_the_files_themselves(values: dict[str, str]) -> None:
    data = REPO_ROOT / EXPLORER_DATA / "cases"
    readings = [
        reading
        for path in sorted(data.glob("*/*.json"))
        for reading in json.loads(path.read_text(encoding="utf-8"))["readings"]
    ]
    assert values["cases_readings"] == format_count(len(readings))
    assert values["cases_readings_no_good_match"] == format_count(
        sum(1 for reading in readings if reading["label"] == "no_good_match")
    )


def test_the_sentence_all_the_readings_are_no_good_match_is_still_true(
    values: dict[str, str],
) -> None:
    """The claim, not the digits: the README says every reading is "no good match". The markers keep both
    counts right; this keeps the word "all" from going quietly false."""
    assert values["cases_readings"] == values["cases_readings_no_good_match"], (
        "a reading now has another label: the README's 'all readings are no good match' is false"
    )


def test_the_other_c_against_d_figures_hold_what_the_sources_hold(values: dict[str, str]) -> None:
    """Pinned like the lead (step 4): the README states each of these in a sentence."""
    assert values["haiku_cd_s3_difference"] == "+86.7"
    assert values["haiku_cd_s3_points_down"] == "86"
    assert values["haiku_cd_s4_difference"] == f"{MINUS}41.6"
    assert values["haiku_cd_s4_points_down"] == "41"
    assert values["gpt_oss_cd_s1_points_down"] == "45"
    assert values["gpt_oss_cd_s3_points_down"] == "38"


def test_every_c_against_d_figure_the_readme_states_is_a_split() -> None:
    """The README says each of these comparisons "came out different": the word must stay true."""
    index = json.loads((REPO_ROOT / EXPLORER_DATA / "index.json").read_text(encoding="utf-8"))
    for _short, model_key, scenario_id in readme_figures.CD_FIGURES:
        verdicts = [
            comparison["final_verdict"]
            for verdict in index["verdicts"]
            if verdict["model_key"] == model_key and verdict["scenario_id"] == scenario_id
            for comparison in verdict["comparisons"]
            if (comparison["first"], comparison["second"]) == ("C", "D")
        ]
        assert verdicts == ["split"], (model_key, scenario_id, verdicts)


def test_the_c_against_d_figures_are_every_split_in_the_grid(values: dict[str, str]) -> None:
    """The README states every C against D split in numbers and calls the rest inconclusive: the figures'
    list must be exactly the grid's splits."""
    splits = {
        (model, scenario_id)
        for model, _model_key in readme_figures.VERDICT_MODELS
        for scenario_id in readme_figures.VERDICT_SCENARIOS
        if values[readme_figures.verdict_key(model, scenario_id, "C", "D")] == "split"
    }
    assert splits == {(short, scenario) for short, _key, scenario in readme_figures.CD_FIGURES}


def test_where_both_models_split_c_against_d_they_split_the_same_way(
    values: dict[str, str],
) -> None:
    """The README says so in words; the signs of the marked differences must keep it true."""
    for scenario_id in readme_figures.VERDICT_SCENARIOS:
        signs = {
            values[f"{short}_cd_{scenario_id}_difference"][0]
            for short, _key, scenario in readme_figures.CD_FIGURES
            if scenario == scenario_id
        }
        assert len(signs) <= 1, (scenario_id, signs)


def test_every_case_is_an_exploratory_closure(values: dict[str, str]) -> None:
    """The README says the exploratory cases are "all closures": the closure count is every case."""
    index = json.loads((REPO_ROOT / EXPLORER_DATA / "index.json").read_text(encoding="utf-8"))
    cases = json.loads(
        (REPO_ROOT / EXPLORER_DATA / index["files"]["cases"]).read_text(encoding="utf-8")
    )
    assert values["cases_exploratory_closures"] == format_count(len(cases["cases"]))


def test_one_confidence_level_covers_both_models() -> None:
    """The README states one confidence level for every interval it shows, on either model."""
    index = json.loads((REPO_ROOT / EXPLORER_DATA / "index.json").read_text(encoding="utf-8"))
    assert len({model["alpha"] for model in index["models"]}) == 1


def test_the_verdict_words_are_the_sites() -> None:
    """The grid's words are copy.ts's verdictWords, entry for entry."""
    copy = (REPO_ROOT / "web" / "src" / "explorer" / "copy.ts").read_text(encoding="utf-8")
    block = re.search(r"verdictWords: \{(.*?)\}", copy, re.DOTALL)
    assert block is not None
    site = dict(re.findall(r'(\w+): "([^"]+)"', block.group(1)))
    assert site == readme_figures.VERDICT_WORDS


def test_the_verdict_grid_holds_what_the_sources_hold(values: dict[str, str]) -> None:
    """A few cells pinned, one of each word, so a shifted grid fails by name."""
    assert values["verdict_haiku_s1_cd"] == "split"
    assert values["verdict_haiku_s1_bd"] == "no split"
    assert values["verdict_haiku_s2_cd"] == "inconclusive"
    assert values["verdict_gpt_oss_s2_ac"] == "not assessable"


def test_the_against_thesis_figures_are_every_entry_the_site_lists() -> None:
    """The README states every result against the thesis, not a selection: a new entry fails here until its
    figures are added."""
    index = json.loads((REPO_ROOT / EXPLORER_DATA / "index.json").read_text(encoding="utf-8"))
    entries = [
        (entry["model_key"], entry["scenario_id"], entry["first"], entry["second"])
        for entry in index["against_thesis"]["entries"]
    ]
    assert entries == [row[1:] for row in readme_figures.AGAINST_FIGURES]


def test_the_roundtable_pattern_appears_in_no_cell(values: dict[str, str]) -> None:
    """The README says the pattern the statement predicts (A and B split, C and D no split) appears on no
    scenario for either model. The grid's markers keep each cell right; this keeps that sentence true."""
    for model, _model_key in readme_figures.VERDICT_MODELS:
        for scenario_id in readme_figures.VERDICT_SCENARIOS:
            ab = values[readme_figures.verdict_key(model, scenario_id, "A", "B")]
            cd = values[readme_figures.verdict_key(model, scenario_id, "C", "D")]
            assert not (ab == "split" and cd == "no split"), (model, scenario_id)


def test_c_and_d_never_came_out_no_split(values: dict[str, str]) -> None:
    """The README says C and D were never "no split": on every cell they split or the runs could not tell."""
    for model, _model_key in readme_figures.VERDICT_MODELS:
        for scenario_id in readme_figures.VERDICT_SCENARIOS:
            cd = values[readme_figures.verdict_key(model, scenario_id, "C", "D")]
            assert cd in ("split", "inconclusive"), (model, scenario_id, cd)


def test_the_lead_comparison_is_still_a_split() -> None:
    """The claim, not the digits: the README leads with "C and D split" on the lead scenario. The markers
    keep its numbers right; this keeps the word "split" from going quietly false (Opus's review of step 3)."""
    index = json.loads((REPO_ROOT / EXPLORER_DATA / "index.json").read_text(encoding="utf-8"))
    first, second = readme_figures.LEAD_PAIR
    verdicts = [
        comparison["final_verdict"]
        for verdict in index["verdicts"]
        if verdict["model_key"] == readme_figures.MAIN_MODEL
        and verdict["scenario_id"] == readme_figures.LEAD_SCENARIO
        for comparison in verdict["comparisons"]
        if comparison["first"] == first and comparison["second"] == second
    ]
    assert verdicts == ["split"], verdicts


def test_the_run_years_come_from_the_data() -> None:
    assert run_years() == {"2026"}


# --- the site's formatting, in Python ------------------------------------------------------------------


def test_the_points_format_is_the_sites() -> None:
    assert format_points(-0.1913) == f"{MINUS}19.1"
    assert format_points(0.044) == "+4.4"
    assert format_points(-0.0004) == "0.0"  # never "-0.0" (format.ts)
    assert format_points(0.0) == "0.0"
    assert format_points(-0.0718) == f"{MINUS}7.2"
    assert format_points(0.3, 0) == "+30"


def test_a_tie_rounds_up_as_javascript_does_not_to_even_as_python_does() -> None:
    """toFixed(2) of 0.125 is "0.13" in JavaScript; Python's format gives "0.12". The text is the site's."""
    assert readme_figures._to_fixed(0.125, 2) == "0.13"
    assert readme_figures._to_fixed(12.25, 1) == "12.3"
    assert readme_figures._to_fixed(2.5, 0) == "3"
    assert f"{0.125:.2f}" == "0.12"  # the difference this function exists for


def test_whole_points_down_is_the_sites_with_its_float_correction() -> None:
    assert whole_points_down(0.29999999999999993) == 30
    assert whole_points_down(-0.1913) == 19
    assert whole_points_down(0.0099) == 0


def test_the_confidence_level_and_the_count_formats_are_the_sites() -> None:
    assert confidence_level(0.003125) == "99.7%"
    assert confidence_level(0.05) == "95.0%"
    assert format_count(990) == "990"
    assert format_count(1200) == "1,200"
    assert format_count(1234567) == "1,234,567"


def test_the_generator_calls_no_network_no_aws_client_and_no_clock() -> None:
    tree = ast.parse(Path(readme_figures.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {"boto3", "botocore", "socket", "ssl", "urllib", "http", "requests", "anthropic"}
    forbidden |= {"datetime", "time", "random"}
    assert not (imported & forbidden), imported & forbidden


def test_a_missing_source_is_a_refusal_not_a_guess(tmp_path: Path) -> None:
    with pytest.raises(ReadmeFiguresRefusal, match=r"index\.json"):
        figures(tmp_path)


# --- make readme ---------------------------------------------------------------------------------------


def _blank_values(text: str) -> str:
    return MARKER.sub(lambda match: f"<!-- n:{match.group(1)} --><!-- /n -->", text)


def test_render_changes_nothing_but_the_marked_values(values: dict[str, str]) -> None:
    text = _read(FIXTURE)
    out = render(text, values)
    assert out != text
    assert _blank_values(out) == _blank_values(text)
    assert render(out, values) == out  # idempotent


def test_an_unknown_marker_is_a_refusal_in_render() -> None:
    with pytest.raises(ReadmeFiguresRefusal, match="no source"):
        render("<!-- n:nodez -->1<!-- /n -->", {"nodes": "1"})


def test_rewrite_fixes_a_stale_file_skips_a_missing_one_and_touches_nothing_else(
    tmp_path: Path, values: dict[str, str]
) -> None:
    readme = tmp_path / "README.md"
    prose = "Some prose that must not change.\n"
    readme.write_text(prose + "Runs: <!-- n:grid_runs_haiku -->1<!-- /n -->.\n", encoding="utf-8")
    messages = rewrite(tmp_path, values)
    assert _read(readme) == (
        prose + f"Runs: <!-- n:grid_runs_haiku -->{values['grid_runs_haiku']}<!-- /n -->.\n"
    )
    assert any(m.startswith("skipped docs/plain-english.md") for m in messages)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["README.md"]  # nothing else was written
    assert rewrite(tmp_path, values)[0] == "README.md: the marked figures are already current"


def test_rewrite_refuses_a_file_with_a_malformed_marker(
    tmp_path: Path, values: dict[str, str]
) -> None:
    (tmp_path / "README.md").write_text("<!-- n:grid_runs_haiku -->990 runs\n", encoding="utf-8")
    with pytest.raises(ReadmeFiguresRefusal, match="malformed"):
        rewrite(tmp_path, values)


def test_the_makefile_target_exists_and_is_in_help() -> None:
    makefile = _read(REPO_ROOT / "Makefile")
    assert re.search(r"^readme:.*## ", makefile, re.MULTILINE)
    assert "python -m horizon_compact.site.readme_figures" in makefile
    assert re.search(r"^\.PHONY:.*\breadme\b", makefile.replace("\\\n", " "), re.MULTILINE)


# --- planted faults: each check fails on the fault it exists to catch ----------------------------------


def _planted(tmp_path: Path, mutate: Callable[[str], str], values: dict[str, str]) -> str:
    """A faulty copy of the rendered skeleton, written to ``tmp_path`` and read back."""
    path = tmp_path / "faulty.md"
    path.write_text(mutate(_rendered_fixture(values)), encoding="utf-8")
    return _read(path)


def test_the_planted_clean_copy_passes_every_check(tmp_path: Path, values: dict[str, str]) -> None:
    text = _planted(tmp_path, lambda t: t, values)
    assert stale(text, values) == []
    assert unknown_keys(text, values) == []
    assert unmarked_keys([text], values) == []
    assert census_of(text) == []


def test_a_changed_digit_in_a_marked_value_is_reported_as_stale(
    tmp_path: Path, values: dict[str, str]
) -> None:
    real = values["grid_runs_haiku"]
    wrong = ("1" if real[0] != "1" else "2") + real[1:]
    text = _planted(
        tmp_path,
        lambda t: t.replace(
            f"<!-- n:grid_runs_haiku -->{real}<", f"<!-- n:grid_runs_haiku -->{wrong}<"
        ),
        values,
    )
    problems = stale(text, values)
    assert len(problems) == 1
    assert problems[0].startswith("n:grid_runs_haiku")
    assert wrong in problems[0]
    assert real in problems[0]


def test_a_marker_with_an_unknown_key_is_reported(tmp_path: Path, values: dict[str, str]) -> None:
    text = _planted(
        tmp_path,
        lambda t: t.replace("<!-- n:against_thesis_count -->", "<!-- n:against_thesis_cuont -->"),
        values,
    )
    assert unknown_keys(text, values) == ["against_thesis_cuont"]
    assert unmarked_keys([text], values) == [
        "against_thesis_count"
    ]  # and the real key is now unmarked


def test_a_removed_marker_is_reported_as_an_unmarked_key_and_by_the_census(
    tmp_path: Path, values: dict[str, str]
) -> None:
    real = values["cases_leakage_disclosed"]
    text = _planted(
        tmp_path,
        lambda t: t.replace(f"<!-- n:cases_leakage_disclosed -->{real}<!-- /n -->", real),
        values,
    )
    assert unmarked_keys([text], values) == ["cases_leakage_disclosed"]
    assert any(f"'{real}'" in line for line in census_of(text)), (
        "the retyped number must fail the census"
    )


def test_a_marker_missing_its_closer_is_reported_as_malformed(
    tmp_path: Path, values: dict[str, str]
) -> None:
    text = _planted(tmp_path, lambda t: t.replace("<!-- /n -->", "", 1), values)
    assert malformed_markers(text)


def test_an_unmarked_number_in_prose_fails_the_census(
    tmp_path: Path, values: dict[str, str]
) -> None:
    text = _planted(tmp_path, lambda t: t + "\nAbout 41 percent kept their jobs.\n", values)
    problems = census_of(text)
    assert len(problems) == 1
    assert "'41'" in problems[0]
    assert marked(text) == marked(
        _rendered_fixture(values)
    )  # the markers themselves were untouched
