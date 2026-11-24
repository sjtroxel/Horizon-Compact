"""The README's marked figures (Phase 7 IMPLEMENTATION doc step 3 and section 5).

Every number in ``README.md`` and ``docs/plain-english.md`` that comes from the experiment is written
between two invisible markers, ``<!-- n:key -->value<!-- /n -->``. This module computes each key's value
from committed files and rewrites the values in place (``make readme``). ``tests/test_readme_figures.py``
fails when a marked value disagrees with its source, when a marker names a key this module does not
compute, when a computed key is not marked, and when a digit stands outside a marker without being a
date, a name, a section reference or a version.

**What it reads:** ``web/explorer-data/`` only, the committed data the site itself reads (``index.json``
and the files it lists), which a test already holds equal to a fresh build from the three official
results files and the case results. So the README cannot say what the site does not. **What it never
does:** call a network, an AWS client or a clock. Standard library only.

**It formats as the site does.** ``web/src/explorer/format.ts`` is the only place the site turns a data
number into text; the functions below are its Python twins, and each key's entry in ``KEYS`` names the
one it mirrors. The one trap is rounding: JavaScript's ``toFixed`` rounds an exact tie upward, Python's
``format`` rounds it to the even digit, so ``_to_fixed`` does the first on the number's exact value.

**No cost key yet.** The phase 7 cost record does not exist until step 9, which extends the sources then.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from math import floor
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPLORER_DATA = "web/explorer-data"

#: The two files whose figures are marked (step 4 writes the first, step 5 the second). A missing one is
#: skipped.
GOVERNED: tuple[str, ...] = ("README.md", "docs/plain-english.md")

#: ``<!-- n:key -->value<!-- /n -->`` on one line. Group 1 is the key, group 2 the value.
MARKER = re.compile(r"<!-- n:([a-z][a-z0-9_]*) -->(.*?)<!-- /n -->")
_OPENER = "<!-- n:"
_CLOSER = "<!-- /n -->"

MINUS = chr(0x2212)  # a real minus sign, as the site writes it

# Which models and scenarios the keys speak of. The README's lead is s1, C against D, on the main model
# (step 4); a C against D comparison on another scenario or model is one more entry in ``CD_FIGURES``.
MAIN_MODEL = "haiku-5-5"
SECOND_MODEL = "gpt-oss-openrouter"
LEAD_SCENARIO = "s1"
LEAD_PAIR = ("C", "D")

#: The C against D comparisons the README states in numbers (README step 4): the lead, then every other
#: scenario where the pair split, on either model. Each gets five keys (``_difference_keys``); a test holds
#: this list to the grid's C against D splits.
CD_FIGURES: tuple[tuple[str, str, str], ...] = (
    ("haiku", MAIN_MODEL, "s1"),
    ("haiku", MAIN_MODEL, "s3"),
    ("haiku", MAIN_MODEL, "s4"),
    ("gpt_oss", SECOND_MODEL, "s1"),
    ("gpt_oss", SECOND_MODEL, "s3"),
)

#: The words every case's ``exploratory_label`` carries when the case was first disclosed before the main
#: model's training cut-off. There is no structured field for this disclosure: the label is the
#: disclosure, shown beside each case on the site. A reworded label counts 0 here and the stale-figure
#: test fails.
LEAKAGE_PHRASE = "first disclosed before the main model's training cut-off"

NO_GOOD_MATCH = "no_good_match"  # web/src/explorer/caseData.ts, NO_GOOD_MATCH

#: The results against the thesis the README states in numbers (README step 4), as (key part, model key,
#: scenario, first, second). A test holds this to ``against_thesis.entries``, so a new entry fails until it
#: is here.
AGAINST_FIGURES: tuple[tuple[str, str, str, str, str], ...] = (
    ("haiku", MAIN_MODEL, "s1", "B", "D"),
    ("haiku", MAIN_MODEL, "s3", "B", "D"),
)

#: The verdict grid (README step 4): every main comparison, on every scenario, for both models. The key's
#: model part and the data's model key, then the comparisons in the order the site lists them (the
#: Roundtable's pair first).
VERDICT_MODELS: tuple[tuple[str, str], ...] = (("haiku", MAIN_MODEL), ("gpt_oss", SECOND_MODEL))
VERDICT_PAIRS: tuple[tuple[str, str], ...] = (
    ("C", "D"),
    ("A", "C"),
    ("B", "D"),
    ("A", "B"),
    ("A", "D"),
)
VERDICT_SCENARIOS: tuple[str, ...] = ("s1", "s2", "s3", "s4")

#: The site's words for a verdict (web/src/explorer/copy.ts, verdictWords).
VERDICT_WORDS: dict[str, str] = {
    "split": "split",
    "no_split": "no split",
    "inconclusive": "inconclusive",
    "not_assessable": "not assessable",
}


def verdict_key(model: str, scenario_id: str, first: str, second: str) -> str:
    """``verdict_haiku_s1_cd``: one cell of the verdict grid."""
    return f"verdict_{model}_{scenario_id}_{first.lower()}{second.lower()}"


#: Every key, with where its value comes from and the site function whose formatting it mirrors. A test
#: holds this table and ``figures()`` to the same keys.
KEYS: dict[str, tuple[str, str]] = {
    "haiku_cd_s1_confidence": (
        "index.json models: Haiku 5.5's `alpha` (a test holds gpt-oss-120b's equal, so one level covers both)",
        "format.ts confidenceLevel (100 minus alpha as a percentage, one decimal)",
    ),
    "grid_runs_haiku": (
        "grid/haiku-5-5/s1..s4.json: `objective_rates[].attempted`, summed over the four scenarios",
        "format.ts attemptedRuns (one scenario) and formatCount; attempted, not valid",
    ),
    "grid_runs_gpt_oss": (
        "grid/gpt-oss-openrouter/s1..s4.json: `objective_rates[].attempted`, summed over the scenarios",
        "format.ts attemptedRuns (one scenario) and formatCount; attempted, not valid",
    ),
    "against_thesis_count": (
        "index.json against_thesis: the length of `entries`",
        "AgainstThesis.tsx lists the entries; formatCount",
    ),
    "cases_exploratory_closures": (
        "cases/index.json cases: those with `exploratory` true and `type` closure",
        "Cases.tsx lists the cases; formatCount",
    ),
    "cases_leakage_disclosed": (
        "cases/index.json cases: those whose `exploratory_label` holds LEAKAGE_PHRASE",
        "Cases.tsx shows each label; formatCount",
    ),
    "cases_readings": (
        "every case result file in index.json `files.case_results`: the length of `readings`, summed",
        "caseData.ts everyReadingNoGoodMatch reads the same lists; formatCount",
    ),
    "cases_readings_no_good_match": (
        "the same files: readings whose `label` is no_good_match",
        "caseData.ts NO_GOOD_MATCH; formatCount",
    ),
}


for _short, _model_key, _scenario in CD_FIGURES:
    _where = f"index.json verdicts: {_model_key}, {_scenario}, C minus D"
    KEYS.update(
        {
            f"{_short}_cd_{_scenario}_difference": (
                f"{_where}, `difference`",
                "format.ts formatPoints (one decimal, signed, real minus)",
            ),
            f"{_short}_cd_{_scenario}_points_down": (
                f"{_where}, the same `difference`",
                "format.ts wholePointsDown (absolute, whole points, rounded down), as sentences.ts uses it",
            ),
            f"{_short}_cd_{_scenario}_interval": (
                f"{_where}, `low` and `high`",
                "format.ts formatPoints on each end, as AgainstThesis.tsx joins them",
            ),
            f"{_short}_cd_{_scenario}_runs_c": (
                f"{_where}, `valid_runs`, second entries summed",
                "format.ts comparisonRuns (first) and formatCount",
            ),
            f"{_short}_cd_{_scenario}_runs_d": (
                f"{_where}, `valid_runs`, third entries summed",
                "format.ts comparisonRuns (second) and formatCount",
            ),
        }
    )

for _short, _model_key, _scenario, _first, _second in AGAINST_FIGURES:
    _where = (
        f"index.json against_thesis entries: {_model_key}, {_scenario}, {_first} minus {_second}"
    )
    _prefix = f"against_{_short}_{_scenario}_{_first.lower()}{_second.lower()}"
    KEYS.update(
        {
            f"{_prefix}_difference": (
                f"{_where}, `difference`",
                "format.ts formatPoints, as AgainstThesis.tsx shows it",
            ),
            f"{_prefix}_interval": (
                f"{_where}, `low` and `high`",
                "format.ts formatPoints on each end, as AgainstThesis.tsx joins them",
            ),
            f"{_prefix}_runs_{_first.lower()}": (
                f"{_where}, `valid_runs`, second entries summed",
                "format.ts comparisonRuns (first) and formatCount",
            ),
            f"{_prefix}_runs_{_second.lower()}": (
                f"{_where}, `valid_runs`, third entries summed",
                "format.ts comparisonRuns (second) and formatCount",
            ),
        }
    )

KEYS.update(
    {
        verdict_key(model, scenario_id, first, second): (
            f"index.json verdicts: {model_key}, {scenario_id}, {first} against {second}, `final_verdict`",
            "copy.ts verdictWords",
        )
        for model, model_key in VERDICT_MODELS
        for scenario_id in VERDICT_SCENARIOS
        for first, second in VERDICT_PAIRS
    }
)


class ReadmeFiguresRefusal(Exception):
    """A source is missing or does not hold what a figure needs, or a marker names no figure. The message
    says which. Nothing is invented in its place."""


# --- the site's formatting, in Python -------------------------------------------------------------------


def _to_fixed(value: float, digits: int) -> str:
    """JavaScript's ``Number.prototype.toFixed`` for a non-negative number: the exact value, rounded half up.

    Python's own rounding takes an exact tie to the even digit (0.125 to two places is 0.12), JavaScript's
    takes it up (0.13), and the site's text is JavaScript's.
    """
    quantum = Decimal(1).scaleb(-digits)
    return format(Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP), "f")


def format_points(difference: float, digits: int = 1) -> str:
    """``formatPoints``: a difference or an interval end in points (one point is 0.01), signed, with a real
    minus sign; a value that rounds to zero carries no sign."""
    text = _to_fixed(abs(difference * 100), digits)
    if Decimal(text) == 0:
        return text
    return f"{MINUS if difference < 0 else '+'}{text}"


def whole_points_down(difference: float) -> int:
    """``wholePointsDown``: the absolute value in whole points, rounded down, with the site's 1e-9
    correction for float noise (0.29999999999999993 is 30 points in the data)."""
    return floor(abs(difference) * 100 + 1e-9)


def confidence_level(alpha: float) -> str:
    """``confidenceLevel``: 0.003125 is "99.7%"."""
    return f"{_to_fixed((1 - alpha) * 100, 1)}%"


def format_count(count: int) -> str:
    """``formatCount``: a whole count with commas between the thousands."""
    return f"{count:,}"


# --- the sources ----------------------------------------------------------------------------------------


def _load(data_dir: Path, relative: str) -> Any:
    path = data_dir / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ReadmeFiguresRefusal(f"cannot read {EXPLORER_DATA}/{relative}: {error}") from error


def _one_comparison(
    index: Mapping[str, Any], model_key: str, scenario_id: str, first: str, second: str
) -> dict[str, Any]:
    found = [
        comparison
        for verdict in index["verdicts"]
        if verdict["model_key"] == model_key and verdict["scenario_id"] == scenario_id
        for comparison in verdict["comparisons"]
        if comparison["first"] == first and comparison["second"] == second
    ]
    if len(found) != 1:
        raise ReadmeFiguresRefusal(
            f"index.json holds {len(found)} comparisons for {model_key} {scenario_id} "
            f"{first} against {second}; the figures need exactly one"
        )
    comparison: dict[str, Any] = found[0]
    if comparison["difference"] is None or comparison["low"] is None or comparison["high"] is None:
        raise ReadmeFiguresRefusal(
            f"{model_key} {scenario_id} {first} against {second} has no difference or interval"
        )
    return comparison


def _alpha(index: Mapping[str, Any], model_key: str) -> float:
    for model in index["models"]:
        if model["model_key"] == model_key:
            return float(model["alpha"])
    raise ReadmeFiguresRefusal(f"index.json lists no model {model_key}")


def _difference_keys(index: Mapping[str, Any]) -> dict[str, str]:
    first, second = LEAD_PAIR
    values = {"haiku_cd_s1_confidence": confidence_level(_alpha(index, MAIN_MODEL))}
    for short, model_key, scenario_id in CD_FIGURES:
        comparison = _one_comparison(index, model_key, scenario_id, first, second)
        difference = float(comparison["difference"])
        low, high = float(comparison["low"]), float(comparison["high"])
        prefix = f"{short}_cd_{scenario_id}"
        values[f"{prefix}_difference"] = format_points(difference)
        values[f"{prefix}_points_down"] = str(whole_points_down(difference))
        values[f"{prefix}_interval"] = f"{format_points(low)} to {format_points(high)}"
        values[f"{prefix}_runs_c"] = format_count(sum(int(e[1]) for e in comparison["valid_runs"]))
        values[f"{prefix}_runs_d"] = format_count(sum(int(e[2]) for e in comparison["valid_runs"]))
    return values


def _against_keys(index: Mapping[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    entries = index["against_thesis"]["entries"]
    for short, model_key, scenario_id, first, second in AGAINST_FIGURES:
        found = [
            entry
            for entry in entries
            if (entry["model_key"], entry["scenario_id"], entry["first"], entry["second"])
            == (model_key, scenario_id, first, second)
        ]
        if len(found) != 1 or found[0]["low"] is None or found[0]["high"] is None:
            raise ReadmeFiguresRefusal(
                f"against_thesis holds {len(found)} usable entries for {model_key} {scenario_id} "
                f"{first} against {second}; the figures need exactly one"
            )
        entry = found[0]
        prefix = f"against_{short}_{scenario_id}_{first.lower()}{second.lower()}"
        values[f"{prefix}_difference"] = format_points(float(entry["difference"]))
        values[f"{prefix}_interval"] = (
            f"{format_points(float(entry['low']))} to {format_points(float(entry['high']))}"
        )
        values[f"{prefix}_runs_{first.lower()}"] = format_count(
            sum(int(e[1]) for e in entry["valid_runs"])
        )
        values[f"{prefix}_runs_{second.lower()}"] = format_count(
            sum(int(e[2]) for e in entry["valid_runs"])
        )
    return values


def _verdict_keys(index: Mapping[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for model, model_key in VERDICT_MODELS:
        for scenario_id in VERDICT_SCENARIOS:
            for first, second in VERDICT_PAIRS:
                found = [
                    comparison["final_verdict"]
                    for verdict in index["verdicts"]
                    if verdict["model_key"] == model_key and verdict["scenario_id"] == scenario_id
                    for comparison in verdict["comparisons"]
                    if comparison["first"] == first and comparison["second"] == second
                ]
                if len(found) != 1 or found[0] not in VERDICT_WORDS:
                    raise ReadmeFiguresRefusal(
                        f"index.json holds {found!r} for {model_key} {scenario_id} {first} against "
                        f"{second}; the grid needs exactly one known verdict"
                    )
                values[verdict_key(model, scenario_id, first, second)] = VERDICT_WORDS[found[0]]
    return values


def _grid_runs(data_dir: Path, index: Mapping[str, Any], model_key: str) -> int:
    files = index["files"]["grid"].get(model_key)
    if not files:
        raise ReadmeFiguresRefusal(f"index.json lists no grid files for {model_key}")
    total = 0
    for relative in files.values():
        grid = _load(data_dir, relative)
        total += sum(int(rate["attempted"]) for rate in grid["objective_rates"])
    return total


def _case_keys(data_dir: Path, index: Mapping[str, Any]) -> dict[str, str]:
    cases = _load(data_dir, index["files"]["cases"])["cases"]
    closures = [c for c in cases if c["exploratory"] is True and c["type"] == "closure"]
    leaked = [c for c in cases if LEAKAGE_PHRASE in (c.get("exploratory_label") or "")]
    labels: list[str] = []
    for per_model in index["files"]["case_results"].values():
        for relative in per_model.values():
            labels.extend(reading["label"] for reading in _load(data_dir, relative)["readings"])
    return {
        "cases_exploratory_closures": format_count(len(closures)),
        "cases_leakage_disclosed": format_count(len(leaked)),
        "cases_readings": format_count(len(labels)),
        "cases_readings_no_good_match": format_count(labels.count(NO_GOOD_MATCH)),
    }


def figures(root: Path | None = None) -> dict[str, str]:
    """Every marked figure's value, from the committed explorer data under ``root`` (the repository by
    default)."""
    data_dir = (root or REPO_ROOT) / EXPLORER_DATA
    index = _load(data_dir, "index.json")
    values = _difference_keys(index)
    values["grid_runs_haiku"] = format_count(_grid_runs(data_dir, index, MAIN_MODEL))
    values["grid_runs_gpt_oss"] = format_count(_grid_runs(data_dir, index, SECOND_MODEL))
    values["against_thesis_count"] = format_count(len(index["against_thesis"]["entries"]))
    values.update(_case_keys(data_dir, index))
    values.update(_against_keys(index))
    values.update(_verdict_keys(index))
    return values


def run_years(root: Path | None = None) -> frozenset[str]:
    """The years of the run dates in ``index.json``'s ``runs`` block: a year the README may name without a
    marker, because it is a date and not a result."""
    index = _load((root or REPO_ROOT) / EXPLORER_DATA, "index.json")
    years: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", node):
            years.add(node[:4])

    walk(index.get("runs", {}))
    return frozenset(years)


# --- the markers ----------------------------------------------------------------------------------------


def marked(text: str) -> list[tuple[str, str]]:
    """Every (key, value) marker in the text, in order."""
    return [(match.group(1), match.group(2)) for match in MARKER.finditer(text)]


def malformed_markers(text: str) -> list[str]:
    """Opening or closing markers that do not pair into a one-line marker: a typo that would leave a number
    looking protected."""
    problems: list[str] = []
    pairs = len(MARKER.findall(text))
    if text.count(_OPENER) != pairs:
        problems.append("an opening marker without its closing marker on the same line")
    if text.count(_CLOSER) != pairs:
        problems.append("a closing marker without its opening marker on the same line")
    return problems


def stale(text: str, values: Mapping[str, str]) -> list[str]:
    """One line per marked figure whose value is not the source's. A marker with no source is not reported
    here (``unknown_keys`` does)."""
    return [
        f"n:{key} -- the file says {value!r}, the source says {values[key]!r}"
        for key, value in marked(text)
        if key in values and value != values[key]
    ]


def unknown_keys(text: str, values: Mapping[str, str]) -> list[str]:
    """Keys marked in the text that the generator does not compute, sorted."""
    return sorted({key for key, _ in marked(text)} - values.keys())


def unmarked_keys(texts: list[str], values: Mapping[str, str]) -> list[str]:
    """Keys the generator computes that no text marks, sorted."""
    return sorted(values.keys() - {key for text in texts for key, _ in marked(text)})


def render(text: str, values: Mapping[str, str]) -> str:
    """The text with each marked value replaced by the source's, and nothing else changed. A marker whose
    key has no source is a refusal, not a pass-through."""
    unknown = unknown_keys(text, values)
    if unknown:
        raise ReadmeFiguresRefusal(f"markers with no source: {unknown}")

    def fill(match: re.Match[str]) -> str:
        key = match.group(1)
        return f"{_OPENER}{key} -->{values[key]}{_CLOSER}"

    return MARKER.sub(fill, text)


def rewrite(root: Path, values: Mapping[str, str]) -> list[str]:
    """Rewrite the governed files under ``root`` that exist; return one message per file. Writes only a
    file whose marked figures changed."""
    messages: list[str] = []
    for name in GOVERNED:
        path = root / name
        if not path.exists():
            messages.append(f"skipped {name}: it does not exist yet")
            continue
        text = path.read_text(encoding="utf-8")
        problems = malformed_markers(text)
        if problems:
            raise ReadmeFiguresRefusal(f"{name} has a malformed marker: {'; '.join(problems)}")
        changed = stale(text, values)
        if not changed:
            messages.append(f"{name}: the marked figures are already current")
            continue
        path.write_text(render(text, values), encoding="utf-8")
        messages.append(f"{name}: rewrote {len(changed)} figure(s)")
        messages.extend(f"  {line}" for line in changed)
    return messages


def main() -> int:
    """``make readme``: rewrite the marked figures in the governed files, from the committed data."""
    try:
        for message in rewrite(REPO_ROOT, figures()):
            print(message)
    except ReadmeFiguresRefusal as refusal:
        print(f"make readme: {refusal}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
