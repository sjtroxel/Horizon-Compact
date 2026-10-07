"""The dossier's data model, renderer and checks (Phase 2 IMPLEMENTATION doc section 12).

Every fixture is a small made-up company, never the real figures. The last tests run the real
``experiment/company/``: its sources, its section-eleven limits and redeployment lines, and every check.
"""

from __future__ import annotations

import tomllib
from decimal import Decimal
from pathlib import Path

import pytest

from horizon_compact.cli import main
from horizon_compact.dossier.check import run_checks
from horizon_compact.dossier.figures import (
    FigureError,
    FigureSet,
    format_value,
    formula_references,
    parse_rows,
    parse_sources,
    resolve,
    round_half_up,
)
from horizon_compact.dossier.render import (
    ASSUMPTIONS_TABLE_PATH,
    CITED_PATH,
    DOSSIER_PATH,
    FIGURES_TABLE_PATH,
    TEMPLATE_PATH,
    balance_report,
    parse_template,
    render_outputs,
    render_text,
    scan_template,
)
from horizon_compact.experiment import Dossier

ROOT = Path(__file__).resolve().parents[1]
HASH = "a" * 64

SOURCES = f"""
[sources.src-a]
short = "Src A"
publisher = "A Made-Up Bureau"
title = "Table 1"
edition = "2030 edition"
released = 2031-01-02
retrieved = 2031-02-03
url = "https://example.invalid/table-1"
file = "table1.dat"
sha256 = "{HASH}"
population = "all made-up firms"
terms = "made up, public domain"
extract = "docs/phases/evidence/phase-2/sources/src-a.csv"
"""

FIGURES = """
[figures.rev_per_emp]
label = "Revenue per employee"
unit = "usd"
value = 450000
source = "src-a"
locator = "row 1, column 2"

[figures.margin]
label = "Operating margin"
unit = "pct"
value = 0.1586
source = "src-a"
locator = "row 2"

[figures.revenue]
label = "Revenue"
unit = "usd_m"
value = 1_500_000_000
assumption = { low = 1_000_000_000, high = 2_000_000_000, range_from = "the decided scale", reason = "midpoint" }

[figures.headcount]
label = "Employees"
unit = "count"
formula = "revenue / rev_per_emp"
round = 10
note = "rounded to the nearest ten"

[figures.payback]
label = "Payback"
unit = "years"
value = 2.5
assumption = { low = 1, high = 4, range_from = "a made-up range", reason = "middle of it", review = "accepted" }

[figures.plant_a]
label = "Plant name"
unit = "label"
value = "7"
assumption = { range_from = "a name, not a quantity", reason = "an identifier" }
"""

TEMPLATE = """@title the Company: a test pack
@group general
Revenue was {revenue}.

@group workforce
It employs {headcount} people at {rev_per_emp} each, a margin of {margin}, repaid in {payback} years.
Plant {plant_a} is the largest.
"""


def build(
    tmp_path: Path,
    *,
    sources: str = SOURCES,
    figures: str | None = FIGURES,
    template: str | None = TEMPLATE,
    extract: bool = True,
    render: bool = True,
) -> Path:
    company = tmp_path / "experiment" / "company"
    company.mkdir(parents=True)
    (company / "sources.toml").write_text(sources, encoding="utf-8")
    if extract:
        path = tmp_path / "docs/phases/evidence/phase-2/sources/src-a.csv"
        path.parent.mkdir(parents=True)
        path.write_text("field,value\nx,1\n", encoding="utf-8")
    if figures is not None:
        (company / "figures.toml").write_text(figures, encoding="utf-8")
    if template is not None:
        (company / "dossier.template.txt").write_text(template, encoding="utf-8")
    if render and figures is not None and template is not None:
        assert main(["dossier", "--root", str(tmp_path), "render"]) == 0
    return tmp_path


def load(figures: str = FIGURES, sources: str = SOURCES) -> FigureSet:
    return resolve(parse_rows(figures), parse_sources(sources))


# --- the data model ---------------------------------------------------------------------------------------


def test_a_sourced_an_assumption_and_a_derived_row_each_load_and_resolve() -> None:
    fs = load()
    assert fs.rows["rev_per_emp"].kind == "sourced"
    assert fs.rows["revenue"].kind == "assumption"
    assert fs.rows["headcount"].kind == "derived"
    # 1.5e9 / 450,000 = 3,333.3, rounded half up to the nearest ten.
    assert fs.resolved["headcount"].value == Decimal(3330)
    assert fs.references["headcount"] == {"revenue", "rev_per_emp"}


@pytest.mark.parametrize(
    "row",
    [
        # two kinds at once
        'label = "x"\nunit = "usd"\nvalue = 1\nsource = "src-a"\nlocator = "l"\nformula = "1 + 1"',
        'label = "x"\nunit = "usd"\nvalue = 1\nsource = "src-a"\nlocator = "l"\n'
        'assumption = { low = 0, high = 2, range_from = "r", reason = "w" }',
        # none
        'label = "x"\nunit = "usd"\nvalue = 1',
        'label = "x"\nunit = "usd"',
        # a source without a locator, a derived row with a value
        'label = "x"\nunit = "usd"\nvalue = 1\nsource = "src-a"',
        'label = "x"\nunit = "usd"\nvalue = 1\nformula = "2 + 2"',
        # an assumption needs a range and a reason
        'label = "x"\nunit = "usd"\nvalue = 1\nassumption = { range_from = "r", reason = "w" }',
        'label = "x"\nunit = "usd"\nvalue = 1\nassumption = { low = 0, high = 2, range_from = "", reason = "w" }',
        'label = "x"\nunit = "usd"\nvalue = 1\nassumption = { low = 3, high = 2, range_from = "r", reason = "w" }',
        # a bound the unit cannot show (a count range of 0.5 to 2 would print as 1 to 2; a pct of 15.05%)
        'label = "x"\nunit = "count"\nvalue = 1\nassumption = { low = 0.5, high = 2, range_from = "r", reason = "w" }',
        'label = "x"\nunit = "pct"\nvalue = 0.2\nassumption = { low = 0.1505, high = 0.3, range_from = "r", reason = "w" }',
        # a label has no range or rounding, and a number row's value is a number
        'label = "x"\nunit = "label"\nvalue = "a"\nassumption = { low = 0, high = 1, range_from = "r", reason = "w" }',
        'label = "x"\nunit = "label"\nvalue = "a"\nround = 2\nassumption = { range_from = "r", reason = "w" }',
        'label = "x"\nunit = "usd"\nvalue = "a"\nassumption = { low = 0, high = 1, range_from = "r", reason = "w" }',
        'label = "x"\nunit = "usd"\nvalue = true\nassumption = { low = 0, high = 1, range_from = "r", reason = "w" }',
    ],
)
def test_a_row_that_is_not_exactly_one_valid_kind_is_refused(row: str) -> None:
    with pytest.raises(FigureError):
        parse_rows(f"[figures.bad]\n{row}\n")


def test_an_unknown_field_is_refused() -> None:
    with pytest.raises(FigureError, match="Extra inputs"):
        parse_rows(
            '[figures.bad]\nlabel = "x"\nunit = "usd"\nvalue = 1\nnotes = "hi"\nformula = "1"\n'
        )


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (
            '[figures.a]\nlabel = "a"\nunit = "usd"\nvalue = 1\nsource = "nope"\nlocator = "l"\n',
            "unknown source",
        ),
        (
            '[figures.a]\nlabel = "a"\nunit = "usd"\nformula = "missing + 1"\n',
            "unknown row missing",
        ),
        (
            '[figures.a]\nlabel = "a"\nunit = "usd"\nformula = "b + 1"\n'
            '[figures.b]\nlabel = "b"\nunit = "usd"\nformula = "a + 1"\n',
            "cycle: a -> b -> a",
        ),
        ('[figures.a]\nlabel = "a"\nunit = "usd"\nformula = "a + 1"\n', "cycle: a -> a"),
        (
            '[figures.a]\nlabel = "a"\nunit = "usd"\nvalue = 5\n'
            'assumption = { low = 1, high = 4, range_from = "r", reason = "w" }\n',
            "outside its own range",
        ),
        ('[figures.a]\nlabel = "a"\nunit = "usd"\nformula = "1 / 0"\n', "divides by zero"),
        (
            '[figures.n]\nlabel = "n"\nunit = "label"\nvalue = "x"\n'
            'assumption = { range_from = "r", reason = "w" }\n'
            '[figures.a]\nlabel = "a"\nunit = "usd"\nformula = "n + 1"\n',
            "label, not a number",
        ),
        (
            '[figures.a]\nlabel = "a"\nunit = "usd"\nvalue = 1\nround = 0.5\n'
            'assumption = { low = 0, high = 2, range_from = "r", reason = "w" }\n',
            "multiple of",
        ),
    ],
)
def test_bad_references_cycles_ranges_and_arithmetic_are_each_refused(
    rows: str, message: str
) -> None:
    with pytest.raises(FigureError, match=message):
        load(rows)


def test_an_assumption_may_cite_the_sources_its_range_comes_from() -> None:
    row = (
        '[figures.a]\nlabel = "a"\nunit = "usd"\nvalue = 2\n'
        'assumption = {{ low = 1, high = 3, range_from = "r", reason = "w", range_sources = {sources} }}\n'
    )
    fs = load(row.format(sources='["src-a"]'))
    assert fs.rows["a"].assumption is not None
    assert fs.rows["a"].assumption.range_sources == ["src-a"]
    with pytest.raises(FigureError, match="unknown range source 'nope'"):
        load(row.format(sources='["nope"]'))
    with pytest.raises(FigureError, match="non-empty list of distinct"):
        load(row.format(sources="[]"))
    with pytest.raises(FigureError, match="non-empty list of distinct"):
        load(row.format(sources='["src-a", "src-a"]'))


def test_a_source_cited_only_as_a_range_source_is_not_reported_as_uncited(tmp_path: Path) -> None:
    from horizon_compact.dossier.check import cited_sources

    rows = parse_rows(
        '[figures.a]\nlabel = "a"\nunit = "usd"\nvalue = 2\n'
        'assumption = { low = 1, high = 3, range_from = "r", reason = "w", range_sources = ["src-a"] }\n'
    )
    assert cited_sources(rows) == {"src-a"}


@pytest.mark.parametrize(
    "formula",
    [
        "a ** 2",
        "a % 2",
        "abs(a)",
        "a if a else a",
        "a < 2",
        "__import__('os')",
        "a; b",
        "a.real",
        "a[0]",
        "'text'",
        "1 +",
        "",
    ],
)
def test_a_formula_may_hold_only_ids_numbers_operators_and_parentheses(formula: str) -> None:
    with pytest.raises(FigureError):
        formula_references(formula)


def test_a_valid_formula_that_would_divide_by_zero_if_every_row_were_one_is_accepted() -> None:
    # Found drafting the real figures: cash = ev * r / (1 - r). Collecting ids must not evaluate.
    assert formula_references("ev * r / (1 - r)") == {"ev", "r"}
    rows = (
        '[figures.r]\nlabel = "r"\nunit = "pct"\nvalue = 0.25\n'
        'assumption = { low = 0, high = 0.5, range_from = "x", reason = "w" }\n'
        '[figures.c]\nlabel = "c"\nunit = "ratio"\nformula = "r / (1 - r)"\n'
    )
    assert load(rows).resolved["c"].value == Decimal("0.33")


def test_formulas_follow_ordinary_precedence_and_support_unary_minus() -> None:
    rows = (
        '[figures.a]\nlabel = "a"\nunit = "count"\nvalue = 6\n'
        'assumption = { low = 0, high = 10, range_from = "r", reason = "w" }\n'
        '[figures.b]\nlabel = "b"\nunit = "count"\nformula = "-a + (a + 2) * 3 / 2 - 1"\n'
    )
    assert load(rows).resolved["b"].value == Decimal(5)  # -6 + 8 * 3 / 2 - 1


def test_a_source_needs_a_real_hash_and_its_own_short_label() -> None:
    with pytest.raises(FigureError, match="64 lowercase hex"):
        parse_sources(SOURCES.replace(HASH, "xyz"))
    second = SOURCES.replace("src-a", "src-b")
    with pytest.raises(FigureError, match="own short label"):
        parse_sources(SOURCES + second.split("\n", 1)[1])


def test_rounding_is_half_up_not_bankers() -> None:
    assert round_half_up(Decimal("0.1585"), Decimal("0.001")) == Decimal("0.159")
    assert round_half_up(Decimal("0.1575"), Decimal("0.001")) == Decimal("0.158")
    assert round_half_up(Decimal(2500), Decimal(1000)) == Decimal(3000)


@pytest.mark.parametrize(
    ("unit", "value", "shown"),
    [
        ("usd", Decimal(58740), "$58,740"),
        ("usd", Decimal(-1500), "-$1,500"),
        ("usd_m", Decimal(1_500_000_000), "$1,500.0 million"),
        ("usd_m", Decimal(1_234_500_000), "$1,234.5 million"),
        ("pct", Decimal("0.159"), "15.9%"),
        ("count", Decimal(3330), "3,330"),
        ("years", Decimal("2.5"), "2.5"),
        ("years", Decimal(2), "2"),
        ("ratio", Decimal("1.95"), "1.95"),
        ("label", "7", "7"),
    ],
)
def test_each_unit_renders_as_specified(unit: str, value: Decimal | str, shown: str) -> None:
    assert format_value(unit, value) == shown


def test_the_resolved_value_after_rounding_is_what_the_text_and_later_formulas_see() -> None:
    fs = load()
    assert fs.resolved["margin"].value == Decimal("0.159")  # 0.1586 rounded to its step
    assert fs.resolved["margin"].shown == "15.9%"


# --- the template -----------------------------------------------------------------------------------------


def test_the_template_may_not_hold_a_digit_outside_a_placeholder() -> None:
    _, problems = scan_template(TEMPLATE.replace("a margin", "a 5 margin"))
    assert any("digit '5'" in problem for problem in problems)
    for sneaky in ("a ² margin", "a ½ margin", "a ٣ margin"):
        _, problems = scan_template(TEMPLATE.replace("a margin", sneaky))
        assert problems, sneaky
    _, problems = scan_template(TEMPLATE.replace("a test pack", "a 2030 pack"))
    assert any("title" in problem for problem in problems)


def test_a_placeholder_id_may_contain_digits() -> None:
    template = parse_template("@title t\nPlant {plant_2_headcount}.\n")
    assert template.references() == ["plant_2_headcount"]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("no title here\n", "no @title"),
        ("@title a\n@title b\n", "second @title"),
        ("Some text\n@title late\n", "before the text"),
        ("@title a\n@mood happy\n", "unknown marker"),
        ("@title a\n@group nobody\n", "unknown group"),
        ("@title a\nrevenue {revenue:,}\n", "not a plain"),
        ("@title a\nrevenue {revenue!r}\n", "not a plain"),
        ("@title a\nrevenue {Revenue}\n", "not a plain"),
        ("@title a\nrevenue {revenue\n", "line 2"),
        ("@title a {x}\n", "plain text"),
    ],
)
def test_template_problems_are_collected_with_their_line(text: str, message: str) -> None:
    template, problems = scan_template(text)
    assert template is None
    assert any(message in problem for problem in problems), problems


def test_every_row_id_in_the_template_must_exist() -> None:
    fs = load()
    template = parse_template("@title t\nRevenue {revenue} and {ghost}.\n")
    with pytest.raises(Exception, match="ghost"):
        render_text(template, fs, cited=False)


def test_marker_lines_are_not_rendered_and_blank_runs_collapse() -> None:
    fs = load()
    template = parse_template("@title t\nOne.\n\n@group workforce\n\nTwo {plant_a}.\n")
    assert render_text(template, fs, cited=False) == "One.\n\nTwo 7.\n"


def test_the_balance_report_counts_words_per_group() -> None:
    fs = load()
    template = parse_template(TEMPLATE)
    words = balance_report(template, fs)
    assert words["general"] == 4  # "Revenue was $1,500.0 million."
    assert words["workforce"] == 20
    assert words["customers"] == 0


# --- the outputs ------------------------------------------------------------------------------------------


def test_the_cited_version_puts_the_right_label_after_each_number(tmp_path: Path) -> None:
    root = build(tmp_path)
    cited = (root / CITED_PATH).read_text(encoding="utf-8")
    assert "Revenue was $1,500.0 million [assumption A1]." in cited
    assert "employs 3,330 [derived D1] people at $450,000 [Src A] each" in cited
    assert "a margin of 15.9% [Src A]" in cited
    assert "repaid in 2.5 [assumption A2] years" in cited
    assert "Plant 7 is the largest." in cited  # a label gets no bracket
    assert "## Sources" in cited
    assert "**Src A**: A Made-Up Bureau" in cited


def test_the_models_version_has_no_citation_and_loads_as_a_dossier(tmp_path: Path) -> None:
    root = build(tmp_path)
    data = tomllib.loads((root / DOSSIER_PATH).read_text(encoding="utf-8"))
    dossier = Dossier.model_validate(data)
    assert dossier.title == "the Company: a test pack"
    assert "[" not in dossier.text
    assert "nearest ten" not in dossier.text  # a note is for the public tables only
    assert "Revenue was $1,500.0 million." in dossier.text
    assert dossier.text.endswith("is the largest.\n")


def test_the_cited_and_the_models_version_carry_the_same_numbers(tmp_path: Path) -> None:
    fs = load()
    template = parse_template(TEMPLATE)
    plain = render_text(template, fs, cited=False)
    cited = render_text(template, fs, cited=True)
    import re

    assert re.sub(r" \[[^\]]+\]", "", cited) == plain


def test_the_tables_list_every_row_and_the_assumptions_with_his_review(tmp_path: Path) -> None:
    root = build(tmp_path)
    figures = (root / FIGURES_TABLE_PATH).read_text(encoding="utf-8")
    for key in ("rev_per_emp", "margin", "revenue", "headcount", "payback", "plant_a"):
        assert f"`{key}`" in figures
    assert "derived D1: revenue / rev_per_emp. Note: rounded to the nearest ten" in figures
    assumptions = (root / ASSUMPTIONS_TABLE_PATH).read_text(encoding="utf-8")
    assert (
        "| A1 | Revenue (`revenue`) | $1,500.0 million | $1,000.0 million to $2,000.0 million |"
        in assumptions
    )
    assert "| accepted |" in assumptions  # payback's review
    assert "none (a name, not a quantity)" in assumptions


def test_rendering_is_the_same_in_every_process(tmp_path: Path) -> None:
    """Found in step 6: the cited sources list followed a set's order, which changes per process with
    Python's string hashing, so a render could differ from the committed file. Render under several seeds."""
    import os
    import subprocess
    import sys

    second = SOURCES.replace("src-a", "src-b").replace("Src A", "Src B")
    figures = (
        '[figures.a]\nlabel = "a"\nunit = "usd"\nvalue = 1\nsource = "src-a"\nlocator = "l"\n'
        '[figures.b]\nlabel = "b"\nunit = "usd"\nvalue = 2\nsource = "src-b"\nlocator = "l"\n'
        '[figures.c]\nlabel = "c"\nunit = "usd"\nformula = "a + b"\n'
    )
    root = build(
        tmp_path,
        sources=SOURCES + second,
        figures=figures,
        template="@title t\nTotal {c}.\n",
        render=False,
    )
    extract_b = root / "docs/phases/evidence/phase-2/sources/src-b.csv"
    extract_b.write_text("field,value\nx,1\n", encoding="utf-8")
    seen = set()
    for seed in ("0", "1", "2", "3", "4", "5"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        code = "import sys; from horizon_compact.cli import main; sys.exit(main(sys.argv[1:]))"
        subprocess.run(
            [sys.executable, "-c", code, "dossier", "--root", str(root), "render"],
            check=True,
            env=env,
            capture_output=True,
        )
        seen.add((root / CITED_PATH).read_text(encoding="utf-8"))
    assert len(seen) == 1


def test_rendering_twice_gives_the_same_bytes() -> None:
    fs = load()
    template = parse_template(TEMPLATE)
    assert render_outputs(template, fs) == render_outputs(template, fs)


# --- the checks -------------------------------------------------------------------------------------------


def test_a_fresh_render_passes_every_check(tmp_path: Path) -> None:
    report = run_checks(build(tmp_path))
    assert report.ok, report.failures
    assert any("balance, words per group" in note for note in report.notes)
    assert any("estimated length" in note for note in report.notes)
    assert main(["dossier", "--root", str(tmp_path), "check"]) == 0


def test_a_hand_edited_output_fails_the_equality_check(tmp_path: Path) -> None:
    root = build(tmp_path)
    for relative in (DOSSIER_PATH, CITED_PATH, FIGURES_TABLE_PATH, ASSUMPTIONS_TABLE_PATH):
        path = root / relative
        original = path.read_text(encoding="utf-8")
        path.write_text(original + " ", encoding="utf-8")
        report = run_checks(root)
        assert any(
            relative in failure and "differs from a fresh render" in failure
            for failure in report.failures
        )
        assert main(["dossier", "--root", str(root), "check"]) == 1
        path.write_text(original, encoding="utf-8")
    assert run_checks(root).ok


def test_a_changed_figure_without_a_re_render_fails_the_check(tmp_path: Path) -> None:
    root = build(tmp_path)
    figures = root / "experiment/company/figures.toml"
    figures.write_text(
        figures.read_text(encoding="utf-8").replace("value = 2.5", "value = 3"), encoding="utf-8"
    )
    assert not run_checks(root).ok
    assert main(["dossier", "--root", str(root), "render"]) == 0
    assert run_checks(root).ok


def test_a_missing_rendered_file_fails_the_check(tmp_path: Path) -> None:
    root = build(tmp_path)
    (root / CITED_PATH).unlink()
    assert any("is missing; run" in failure for failure in run_checks(root).failures)


def test_an_orphan_row_fails_the_check(tmp_path: Path) -> None:
    orphan = FIGURES + (
        '\n[figures.unused]\nlabel = "Unused"\nunit = "usd"\nvalue = 1\n'
        'assumption = { low = 0, high = 2, range_from = "r", reason = "w" }\n'
    )
    root = build(tmp_path, figures=orphan)
    failures = run_checks(root).failures
    assert any("never uses" in failure and "unused" in failure for failure in failures)


def test_a_row_used_only_through_a_formula_is_not_an_orphan(tmp_path: Path) -> None:
    # margin and rev_per_emp are used by the template; drop their placeholders and keep a formula over them.
    template = "@title t\nRevenue {revenue} and {headcount}.\n"
    report = run_checks(build(tmp_path, template=template))
    assert any("never uses" in failure and "margin" in failure for failure in report.failures)
    assert not any(
        "rev_per_emp" in failure for failure in report.failures
    )  # reached through headcount


def test_a_digit_in_the_template_fails_the_check(tmp_path: Path) -> None:
    root = build(tmp_path, template=TEMPLATE.replace("a margin", "a 5 margin"), render=False)
    failures = run_checks(root).failures
    assert any("digit" in failure for failure in failures)
    assert main(["dossier", "--root", str(root), "render"]) == 2  # render refuses it too


def test_an_unknown_row_in_the_template_fails_the_check(tmp_path: Path) -> None:
    root = build(tmp_path, template=TEMPLATE + "And {ghost}.\n", render=False)
    assert any("ghost" in failure for failure in run_checks(root).failures)


def test_a_missing_extract_fails_the_check(tmp_path: Path) -> None:
    root = build(tmp_path, extract=False)
    assert any(
        "extract" in failure and "does not exist" in failure
        for failure in run_checks(root).failures
    )


def test_a_missing_figures_file_or_template_fails_with_no_skip(tmp_path: Path) -> None:
    no_template = run_checks(build(tmp_path / "a", template=None))
    assert any("missing: dossier.template.txt" in failure for failure in no_template.failures)
    neither = run_checks(build(tmp_path / "b", figures=None, template=None))
    assert any(
        "missing: figures.toml, dossier.template.txt" in failure for failure in neither.failures
    )
    assert not any(note.startswith("SKIPPED") for note in neither.notes)


def test_the_length_estimate_warns_above_seven_thousand_tokens(tmp_path: Path) -> None:
    long_template = (
        "@title t\nRevenue {revenue}, {headcount}, {rev_per_emp}, {margin}, {payback}, {plant_a}.\n"
        + ("word " * 5300 + "\n")
    )
    notes = run_checks(build(tmp_path, template=long_template)).notes
    assert any(note.startswith("WARNING") for note in notes)


def test_a_missing_sources_file_fails(tmp_path: Path) -> None:
    assert any("sources.toml is missing" in failure for failure in run_checks(tmp_path).failures)


# --- the real files ---------------------------------------------------------------------------------------


def test_the_real_sources_load_and_every_extract_exists() -> None:
    sources = parse_sources((ROOT / "experiment/company/sources.toml").read_text(encoding="utf-8"))
    assert len(sources) >= 3
    for name, source in sources.items():
        assert (ROOT / source.extract).is_file(), name
    # The terms the rows rest on are recorded, not assumed.
    assert all(source.terms and source.sha256 for source in sources.values())


# Section eleven's line for each lever the menu can use as a source (planning/07 section 3.1), by the words
# that open it. DoD 3: a maximum for every source lever, and the redeployment opportunity in numbers.
LIMIT_LINES = {
    "L1": "Payroll by function, the most that can be removed",
    "L3": "Research and development: the full budget",
    "L4": "Wages and hours:",
    "L5": "Prices to customers:",
    "L6": "Environmental projects:",
    "L7": "Dividends and repurchases:",
    "L8": "Cash:",
    "L9": "Suppliers:",
}


def _source_levers() -> set[str]:
    """The levers in the menu table whose 'As a source' cell is not a dash."""
    table = (ROOT / "docs/planning/07-EVAL-SPEC.md").read_text(encoding="utf-8")
    levers = set()
    for line in table.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        is_lever_row = len(cells) == 6 and cells[1].startswith("L") and cells[1][1:].isdigit()
        if is_lever_row and cells[4] not in {"—", "-", ""}:
            levers.add(cells[1])
    return levers


def test_the_limits_section_has_a_line_for_every_lever_that_can_be_a_source() -> None:
    assert _source_levers() == set(LIMIT_LINES), (
        "the menu's source levers changed: update LIMIT_LINES"
    )
    text = tomllib.loads((ROOT / "experiment/company/dossier.toml").read_text(encoding="utf-8"))[
        "text"
    ]
    section = text.split("SECTION ELEVEN: LIMITS ON EACH LINE", 1)[1]
    for lever, opening in LIMIT_LINES.items():
        assert opening in section, f"section eleven has no line for {lever}: {opening!r}"


def test_the_redeployment_opportunity_is_stated_in_numbers() -> None:
    text = tomllib.loads((ROOT / "experiment/company/dossier.toml").read_text(encoding="utf-8"))[
        "text"
    ]
    section = text.split("SECTION TEN: TECHNOLOGY AND WORK", 1)[1].split("SECTION ELEVEN", 1)[0]
    for opening in (
        "Hiring.",
        "Cost per person",
        "Months of training",
        "Years until the cost of retraining",
    ):
        assert opening in section, opening


def test_the_real_company_folder_passes_every_check() -> None:
    report = run_checks(ROOT)
    assert report.ok, report.failures
    assert TEMPLATE_PATH.endswith("dossier.template.txt")
