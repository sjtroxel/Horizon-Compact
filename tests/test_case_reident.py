"""The re-identification check (Phase 5.5 IMPLEMENTATION doc §5.5, K5), on fakes. No SEC, no AWS, no model:
the frames are served by a scripted transport, the case is invented, and every CIK, name and figure here is
a fictional canary (the real cases and the private appendix are never opened).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from horizon_compact import cli
from horizon_compact.casebuild.appendix import CaseAppendix
from horizon_compact.casebuild.edgar import EdgarClient, EdgarError, EdgarNotFound, Response
from horizon_compact.caseprobe import reident
from horizon_compact.caseprobe.reident import (
    PENDING,
    REASON_FEW,
    REASON_SEARCH,
    REASON_UNCONFIRMED,
    FrameRow,
    Interval,
    Ratio,
    ReidentRefused,
    YearFrames,
    build_ratios,
    divide,
    first_sentence,
    frame_url,
    matches,
    run_reident,
    stated_interval,
)
from horizon_compact.protocol.cases import case_lock_text
from horizon_compact.sweep.plan import SweepRefusal

LABEL = "pre-77"
HEAD = "0123456789abcdef0123456789abcdef01234567"
OWN_CIK = 7770001
OWN_NAME = "Quillfeather Canary Holdings"
FACTOR = 1.25
E24, E23, E22 = date(2024, 12, 31), date(2023, 12, 31), date(2022, 12, 31)
Values = dict[date, tuple[float, float, float]]
# The case's true, unscaled figures: (revenue, operating income, operating cash flow) by fiscal year end.
OWN_VALUES: Values = {
    E24: (2_000_000_000, 300_000_000, 400_000_000),
    E23: (1_800_000_000, 240_000_000, 350_000_000),
    E22: (1_500_000_000, -150_000_000, 200_000_000),
}
REVENUE_TAGS = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
)
OPERATING_INCOME, OPERATING_CASH_FLOW = (
    "OperatingIncomeLoss",
    "NetCashProvidedByUsedInOperatingActivities",
)
FIRST_SENTENCE = "The Company makes widgets for the U.S. market."
DOSSIER = (
    'title = "The Company: background for the decision"\n'
    "text = '''\n"
    "SECTION ONE: THE COMPANY\n\n"
    f"{FIRST_SENTENCE} It employs many people.\n\n"
    "SECTION SIX: THE SITUATION NOW\n\n"
    "Demand for widgets has fallen sharply. The board must decide what to do about the Plant.\n"
    "'''\n"
)
NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


@dataclass
class Filer:
    cik: int
    values: dict[date, tuple[float, float, float]]
    revenue_tag: str = "Revenues"
    skip: frozenset[str] = (
        frozenset()
    )  # "operating_income" or "operating_cash_flow": no row in that frame


def scaled_copy(cik: int, k: int, values: Values | None = None, **changes: Any) -> Filer:
    """A decoy with the case's ratios exactly, at k times its size: scaling hides size, not shape."""
    scaled = {end: (r * k, o * k, c * k) for end, (r, o, c) in (values or OWN_VALUES).items()}
    return Filer(cik, scaled, **changes)


def other_filer(cik: int, margin: Fraction, values: Values | None = None) -> Filer:
    """A filer of the case's size whose operating margin is not the case's."""
    shaped: Values = {
        end: (r, int(r * margin), c) for end, (r, _, c) in (values or OWN_VALUES).items()
    }
    return Filer(cik, shaped)


def frame_body(rows: list[tuple[int, date, float]]) -> bytes:
    data = [
        {
            "accn": f"0000000000-26-{index:06d}",
            "cik": cik,
            "end": end.isoformat(),
            "entityName": f"CANARY ENTITY {cik}",
            "loc": "ZZ",
            "start": date(end.year - 1, end.month, end.day).isoformat(),
            "val": value,
        }
        for index, (cik, end, value) in enumerate(rows)
    ]
    return json.dumps({"taxonomy": "us-gaap", "tag": "x", "uom": "USD", "data": data}).encode()


def frames_of(filers: list[Filer], cy_of: dict[date, int]) -> dict[str, bytes]:
    rows: dict[tuple[str, int], list[tuple[int, date, float]]] = {}
    for filer in filers:
        for end, (revenue, income, cash) in filer.values.items():
            year = cy_of[end]
            rows.setdefault((filer.revenue_tag, year), []).append((filer.cik, end, revenue))
            if "operating_income" not in filer.skip:
                rows.setdefault((OPERATING_INCOME, year), []).append((filer.cik, end, income))
            if "operating_cash_flow" not in filer.skip:
                rows.setdefault((OPERATING_CASH_FLOW, year), []).append((filer.cik, end, cash))
    return {frame_url(tag, year): frame_body(found) for (tag, year), found in rows.items()}


class Transport:
    """Serves the frames; a frame it was not given is SEC's 404; any other URL fails the test."""

    def __init__(self, served: dict[str, bytes]) -> None:
        self.served = served
        self.requested: list[str] = []

    def get(self, url: str, headers: Any) -> Response:
        self.requested.append(url)
        if not url.startswith("https://data.sec.gov/api/xbrl/frames/us-gaap/"):
            raise AssertionError(f"unexpected request: {url}")
        if url in self.served:
            return Response(200, self.served[url])
        return Response(404, b"")


@dataclass
class World:
    root: Path
    appendix: Path
    transport: Transport
    filers: list[Filer]
    cy_of: dict[date, int]
    case: CaseAppendix = field(init=False)

    def __post_init__(self) -> None:
        self.case = CaseAppendix(self.appendix, LABEL)

    def sec(self) -> EdgarClient:
        return EdgarClient(
            appendix=self.case,
            transport=self.transport,
            user_agent="Test Agent test@example.com",
            sleep=lambda seconds: None,
            now=lambda: NOW,
        )

    @property
    def public(self) -> Path:
        return self.root / "experiment" / "results" / "cases" / LABEL / "reident.json"

    @property
    def record(self) -> Path:
        return self.case.directory / "reident-record.json"

    @property
    def search(self) -> Path:
        return self.case.directory / "reident-search.toml"


def build_json(case_values: Values | None = None) -> dict[str, Any]:
    values = case_values or OWN_VALUES
    ends = tuple(values)

    def line(tag: str, index: int) -> dict[str, Any]:
        return {
            "section": 4,
            "tag": tag,
            "years": {
                end.isoformat(): {"value": values[end][index], "form": "10-K"} for end in ends
            },
        }

    build: dict[str, Any] = {
        "build_version": 1,
        "label": LABEL,
        "factor": FACTOR,
        "section_inputs": {
            "figures": {
                "year_ends": [end.isoformat() for end in ends],
                "lines": {
                    "revenue": line("Revenues", 0),
                    "operating_income": line(OPERATING_INCOME, 1),
                    "operating_cash_flow": line(OPERATING_CASH_FLOW, 2),
                },
                "omitted": [],
            }
        },
    }
    return build


def make_world(
    tmp_path: Path,
    *,
    decoys: int = 24,
    others: int = 6,
    cy_of: dict[date, int] | None = None,
    own: Filer | None = None,
    extra: list[Filer] | None = None,
    values: Values | None = None,
    probe_set: int = 1,
    build: dict[str, Any] | None = None,
) -> World:
    """The case's true ``values`` (by fiscal year end) are in its build record, in its own filer's rows
    (unless ``own`` says otherwise) and, scaled or reshaped, in the decoys' and the others'."""
    root, appendix = tmp_path / "repo", tmp_path / "appendix"
    case_values = values or OWN_VALUES
    cy_of = cy_of or {end: end.year for end in case_values}
    case = CaseAppendix(appendix, LABEL)
    dossier_path = case.dossier_path_for(probe_set)
    write(dossier_path, DOSSIER)
    digest = hashlib.sha256(DOSSIER.encode("utf-8")).hexdigest()
    write(
        root / f"experiment/cases/{LABEL}/case.lock",
        case_lock_text(
            LABEL,
            probe_set,
            {"dossier_sha256": digest, "scenario_sha256": "a" * 64, "rubric_sha256": "b" * 64},
        ),
    )
    entry = {"label": LABEL, "probe_set": probe_set, "type": "closure", "text": "x"}
    write(root / "docs/phases/evidence/phase-5/freeze.json", json.dumps({"cases": [entry]}))
    write(case.build_path, json.dumps(build or build_json(case_values)))
    write(case.sources_path, json.dumps({"cik": f"{OWN_CIK:010d}", "sources": []}))
    filers = [own or Filer(OWN_CIK, dict(case_values))]
    filers += [scaled_copy(7771000 + n, 2 + n, case_values) for n in range(decoys)]
    filers += [other_filer(7772000 + n, Fraction(1 + n, 100), case_values) for n in range(others)]
    filers += extra or []
    return World(root, appendix, Transport(frames_of(filers, cy_of)), filers, cy_of)


def run(world: World) -> Any:
    return run_reident(world.root, LABEL, appendix=world.appendix, head=HEAD, sec=world.sec())


def public(world: World) -> dict[str, Any]:
    loaded = json.loads(world.public.read_text("utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def record(world: World) -> dict[str, Any]:
    loaded = json.loads(world.record.read_text("utf-8"))
    assert isinstance(loaded, dict)
    return loaded


def fill_search(
    world: World, answers: list[bool | None], *, queries: dict[int, str] | None = None
) -> None:
    """His step: the template with each entry's engine, date and answer filled in (None leaves one open)."""
    text = world.search.read_text("utf-8")
    parts = text.split("[[search]]")
    out = [parts[0]]
    for index, chunk in enumerate(parts[1:]):
        query = (queries or {}).get(index)
        if query is not None:
            chunk = re.sub(r'query = ".*"', f"query = {json.dumps(query)}", chunk, count=1)
        if index < len(answers) and answers[index] is not None:
            chunk = chunk.replace('engine = ""', 'engine = "a canary engine"')
            chunk = chunk.replace('searched_on = ""', 'searched_on = "2026-10-29"')
            chunk = chunk.replace(
                "# company_on_first_page = false",
                f"company_on_first_page = {'true' if answers[index] else 'false'}",
            )
        out.append(chunk)
    write(world.search, "[[search]]".join(out))


# --- the figures and their tolerance ----------------------------------------------------------------------


def test_a_figure_is_the_interval_its_three_digit_rounding_and_its_rendering_allow() -> None:
    # $2,000.0 million x 1.25 = 2,500 million: half a unit of the third digit is 5 million, and the
    # rendering to $0.1 million (half of it, 0.05 million, times the factor) widens it by 0.0625 million.
    assert stated_interval(2_000_000_000, FACTOR) == Interval(
        Fraction(2_494_937_500), Fraction(2_505_062_500)
    )
    # whole dollars under $1 million: 56,050 x 1.25 = 70,062.5, stated 70,100 (half a unit is 50).
    assert stated_interval(56_050, FACTOR) == Interval(
        Fraction(70_049_375, 1000), Fraction(70_150_625, 1000)
    )


def test_a_coarsened_figure_is_centred_on_its_two_digits_with_both_roundings_half_units() -> None:
    # $1,236.0 million x 1.25 = 1,545: three digits give 1,550, two give 1,600, 55 away from the true value,
    # more than the two-digit half-unit (50) alone allows. Width 50 + 5 + the rendering's 0.0625.
    interval = stated_interval(1_236_000_000, FACTOR, coarsened=True)
    assert interval == Interval(Fraction(1_544_937_500), Fraction(1_655_062_500))
    assert interval.contains(Fraction(1_236_000_000) * Fraction(5, 4))
    assert not Interval(Fraction(1_550_000_000), Fraction(1_650_000_000)).contains(
        Fraction(1_545_000_000)
    )


def test_a_negative_figure_keeps_its_sign_and_its_width() -> None:
    # -$150.0 million x 1.25 = -187.5, stated -188 (half a unit 0.5), plus the rendering's 0.0625.
    assert stated_interval(-150_000_000, FACTOR) == Interval(
        Fraction(-188_562_500), Fraction(-187_437_500)
    )


def test_a_quotient_takes_its_extremes_at_the_corners_signs_included() -> None:
    assert divide(
        Interval(Fraction(8), Fraction(12)), Interval(Fraction(2), Fraction(4))
    ) == Interval(Fraction(2), Fraction(6))
    assert divide(
        Interval(Fraction(8), Fraction(12)), Interval(Fraction(-4), Fraction(-2))
    ) == Interval(Fraction(-6), Fraction(-2))
    assert divide(
        Interval(Fraction(-3), Fraction(5)), Interval(Fraction(2), Fraction(4))
    ) == Interval(Fraction(-3, 2), Fraction(5, 2))
    assert divide(Interval(Fraction(1), Fraction(2)), Interval(Fraction(0), Fraction(4))) is None
    assert divide(Interval(Fraction(1), Fraction(2)), Interval(Fraction(-1), Fraction(1))) is None


def test_the_ratios_come_from_the_build_record_as_the_plan_names_them() -> None:
    ratios, dropped = build_ratios(build_json())
    assert dropped == []
    assert [r.kind for r in ratios] == ["revenue_growth"] * 2 + ["operating_margin"] * 3 + [
        "cash_flow_over_revenue"
    ] * 3
    assert len(ratios) == 8
    revenue, income = stated_interval(2_000_000_000, FACTOR), stated_interval(300_000_000, FACTOR)
    margin = next(r for r in ratios if r.kind == "operating_margin" and r.ends == (E24,))
    assert margin.interval == Interval(income.lo / revenue.hi, income.hi / revenue.lo)
    earlier = stated_interval(1_800_000_000, FACTOR)
    growth = next(r for r in ratios if r.kind == "revenue_growth" and r.ends == (E24, E23))
    assert growth.interval == Interval(revenue.lo / earlier.hi - 1, revenue.hi / earlier.lo - 1)
    # the factor cancels: the true ratio of the unscaled figures is inside
    assert growth.interval.contains(Fraction(2_000, 1_800) - 1)
    assert margin.interval.contains(Fraction(300, 2000))


def test_a_negative_operating_income_gives_a_negative_margin_interval() -> None:
    ratios, _ = build_ratios(build_json())
    margin = next(r for r in ratios if r.kind == "operating_margin" and r.ends == (E22,))
    assert margin.interval.hi < 0 and margin.interval.contains(Fraction(-150, 1500))


def test_a_ratio_whose_denominator_interval_holds_zero_is_dropped_and_recorded() -> None:
    build = build_json()
    build["section_inputs"]["figures"]["lines"]["revenue"]["years"][E23.isoformat()]["value"] = 0
    ratios, dropped = build_ratios(build)
    assert {(d["kind"], tuple(d["ends"])) for d in dropped} == {
        ("revenue_growth", (E24.isoformat(), E23.isoformat())),
        ("operating_margin", (E23.isoformat(),)),
        ("cash_flow_over_revenue", (E23.isoformat(),)),
    }
    assert all(d["why"] == "the denominator's interval holds zero" for d in dropped)
    assert len(ratios) == 5


def test_a_line_or_year_the_build_lacks_drops_the_ratios_that_need_it() -> None:
    build = build_json()
    del build["section_inputs"]["figures"]["lines"]["operating_income"]
    del build["section_inputs"]["figures"]["lines"]["operating_cash_flow"]["years"][E22.isoformat()]
    ratios, dropped = build_ratios(build)
    assert len(ratios) == 2 + 2  # both growths, cash flow in two years
    assert sum(1 for d in dropped if d["kind"] == "operating_margin") == 3
    assert {d["why"] for d in dropped} == {"a figure it needs is not in build.json"}


def test_a_value_at_the_intervals_edge_matches_and_one_just_past_it_does_not() -> None:
    ratio = Ratio("operating_margin", (E24,), Interval(Fraction(1, 2), Fraction(3, 4)))

    def margin(income: Fraction) -> bool:
        data = {
            E24: YearFrames(
                revenue={1: FrameRow(E24, Fraction(4))},
                operating_income={1: FrameRow(E24, income)},
                operating_cash_flow={},
            )
        }
        return matches([ratio], 1, data)

    assert margin(Fraction(3)) and margin(Fraction(2))  # 3/4 and 1/2 exactly
    assert not margin(Fraction(30001, 10000)) and not margin(Fraction(19999, 10000))


def test_a_stated_figure_that_cannot_be_rendered_is_refused() -> None:
    build = build_json()
    build["section_inputs"]["figures"]["lines"]["revenue"]["tag"] = "NotARevenueTag"
    with pytest.raises(ReidentRefused, match="not one of the tags"):
        reident.figure_half(None, cik=OWN_CIK, build=build)  # type: ignore[arg-type]


# --- the figure half --------------------------------------------------------------------------------------


def test_a_case_that_hides_among_25_passes_the_figure_half_and_leaves_the_description_pending(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path)
    result = run(world)
    assert (result.status, result.ratios_used, result.matching, result.own_confirmed) == (
        PENDING,
        8,
        25,
        True,
    )
    assert result.public is None and not world.public.exists()
    assert result.template == world.search and world.search.is_file()
    kept = record(world)
    assert kept["matching"]["count"] == 25 and OWN_CIK in kept["matching"]["ciks"]
    assert kept["own"] == {"found": True, "not_found_for": [], "matched": True}
    assert len(kept["ratios"]) == 8 and kept["dropped"] == []
    assert any("per-employee" in line for line in kept["assumptions"])
    assert all("sha256" in frame and "url" in frame for frame in kept["frames"])


def test_a_case_that_is_unique_in_the_frames_is_withheld_with_the_fixed_reason(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path, decoys=0)
    result = run(world)
    assert (result.status, result.matching, result.own_confirmed) == ("withheld", 1, True)
    assert (
        public(world)["reason"]
        == REASON_FEW
        == ("withheld: its scale-free figures match fewer than 20 filers in SEC's structured data")
    )
    assert result.template is None and not world.search.exists()


@pytest.mark.parametrize(("decoys", "status"), [(18, "withheld"), (19, PENDING)])
def test_the_threshold_is_20_filers_the_case_included(
    tmp_path: Path, decoys: int, status: str
) -> None:
    world = make_world(tmp_path, decoys=decoys)
    result = run(world)
    assert result.matching == decoys + 1 and result.status == status


def test_a_filer_missing_a_value_a_ratio_needs_is_not_a_match(tmp_path: Path) -> None:
    lacking = scaled_copy(7773000, 5, skip=frozenset({"operating_cash_flow"}))
    world = make_world(tmp_path, decoys=19, extra=[lacking])
    assert (
        run(world).matching == 20
    )  # the 19 decoys and the case; the filer without cash flow is out


def test_a_filer_reporting_revenue_under_a_later_tag_is_still_compared(tmp_path: Path) -> None:
    later = scaled_copy(7773000, 5, revenue_tag="SalesRevenueNet")
    world = make_world(tmp_path, decoys=18, extra=[later])
    assert run(world).matching == 20
    asked = {url.rsplit("/", 3)[-3] for url in world.transport.requested}
    assert set(REVENUE_TAGS) <= asked  # every common tag was tried; a 404 frame is an empty one


def test_a_filer_whose_income_and_revenue_are_for_different_periods_is_not_a_match(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path, decoys=19, extra=[scaled_copy(7773000, 5)])
    # its operating income row ends a different day than its revenue row: no ratio from the two
    year = E24.year
    revenue_frame = json.loads(world.transport.served[frame_url("Revenues", year)])
    for row in revenue_frame["data"]:
        if row["cik"] == 7773000:
            row["end"] = "2024-12-28"
    world.transport.served[frame_url("Revenues", year)] = json.dumps(revenue_frame).encode()
    assert run(world).matching == 20


def test_the_frame_is_found_by_the_own_filers_end_even_in_the_neighbouring_calendar_year(
    tmp_path: Path,
) -> None:
    june = (date(2024, 6, 30), date(2023, 6, 30), date(2022, 6, 30))
    values = dict(zip(june, OWN_VALUES.values(), strict=True))
    # SEC files a fiscal year in its closest calendar-year frame: here the year before, the year after, and
    # the year itself.
    cy_of = {june[0]: 2023, june[1]: 2024, june[2]: 2022}
    world = make_world(tmp_path, values=values, cy_of=cy_of)
    result = run(world)
    assert result.own_confirmed and result.matching == 25
    assert record(world)["fiscal_year_frames"] == {
        june[2].isoformat(): 2022,
        june[1].isoformat(): 2024,
        june[0].isoformat(): 2023,
    }
    # fetched only as needed: the year itself first, and no frame twice
    asked = [u for u in world.transport.requested if "/Revenues/" in u]
    assert asked[0] == frame_url("Revenues", 2024) and len(asked) == len(set(asked))


def test_a_case_whose_own_filer_is_in_no_frame_is_withheld_as_unconfirmed(tmp_path: Path) -> None:
    world = make_world(
        tmp_path, own=Filer(7779999, dict(OWN_VALUES))
    )  # a different filer is in the frames
    result = run(world)
    assert (result.status, result.own_confirmed, result.matching) == ("withheld", False, None)
    assert public(world)["reason"] == REASON_UNCONFIRMED
    assert record(world)["own"]["found"] is False


def test_a_case_whose_own_filer_is_found_but_outside_its_own_intervals_is_withheld_as_unconfirmed(
    tmp_path: Path,
) -> None:
    restated = {end: (r, o * 2, c) for end, (r, o, c) in OWN_VALUES.items()}
    world = make_world(tmp_path, own=Filer(OWN_CIK, restated))
    result = run(world)
    assert (result.status, result.own_confirmed) == ("withheld", False)
    assert result.matching is not None and result.matching >= 20  # the others would have passed it
    assert public(world)["reason"] == REASON_UNCONFIRMED
    assert record(world)["own"] == {"found": True, "not_found_for": [], "matched": False}


def test_a_build_with_no_usable_ratio_cannot_confirm_the_case(tmp_path: Path) -> None:
    build = build_json()
    del build["section_inputs"]["figures"]["lines"]["revenue"]
    world = make_world(tmp_path, build=build)
    result = run(world)
    assert (result.status, result.ratios_used, result.own_confirmed) == ("withheld", 0, False)
    assert public(world)["reason"] == REASON_UNCONFIRMED and world.transport.requested == []


# --- the description half ---------------------------------------------------------------------------------


def test_the_template_holds_the_first_sentence_and_three_empty_slots(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    text = world.search.read_text("utf-8")
    assert f'query = "{FIRST_SENTENCE}"' in text
    assert text.count("[[search]]") == 4 and text.count('query = ""') == 3
    assert not (world.public).exists()


def test_the_first_sentence_does_not_stop_at_an_abbreviation() -> None:
    assert first_sentence("The U.S. firm, Acme Inc. of the north, sells it. It grew.") == (
        "The U.S. firm, Acme Inc. of the north, sells it."
    )
    assert first_sentence("One line with no stop") == "One line with no stop"


def test_a_rerun_with_the_description_unanswered_is_pending_and_writes_nothing(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path)
    run(world)
    before = world.search.read_text("utf-8")
    result = run(world)
    assert result.status == PENDING and result.template is None and result.public is None
    assert world.search.read_text("utf-8") == before and not world.public.exists()
    fill_search(world, [None])
    assert run(world).status == PENDING


def test_a_filled_slot_left_unanswered_keeps_the_description_pending(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    fill_search(world, [False, None], queries={1: "Demand for widgets has fallen sharply."})
    result = run(world)
    assert result.status == PENDING and "1 filled" in result.note and not world.public.exists()


def test_every_query_answered_false_passes_and_writes_the_public_file_once(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    fill_search(
        world, [False, False], queries={1: "The board must decide what to do about the Plant"}
    )
    result = run(world)
    assert result.status == "passed" and result.public == world.public
    kept = public(world)
    assert kept["status"] == "passed" and kept["reason"] is None and kept["threshold"] == 20
    assert kept["exploratory"] is True and kept["case"] == LABEL
    with pytest.raises(ReidentRefused, match="never overwritten"):
        run(world)


def test_any_true_withholds_even_beside_an_unanswered_entry(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    fill_search(world, [None, True], queries={1: "Demand for widgets has fallen sharply."})
    result = run(world)
    assert result.status == "withheld"
    assert (
        public(world)["reason"]
        == REASON_SEARCH
        == ("withheld: its description found the company in a web search")
    )


def test_the_templates_queries_must_be_as_the_dossier_writes_them(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    fill_search(world, [False, False], queries={1: "A phrase the dossier never wrote"})
    with pytest.raises(ReidentRefused, match="not as written in the situation section"):
        run(world)
    fill_search(world, [False], queries={0: "A first line the dossier never wrote.", 1: ""})
    with pytest.raises(ReidentRefused, match="not the start of the overview"):
        run(world)
    assert not world.public.exists()


def test_a_template_for_another_dossier_or_an_answer_without_a_query_is_refused(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path)
    run(world)
    text = world.search.read_text("utf-8")
    write(world.search, text.replace('dossier_sha256 = "', 'dossier_sha256 = "0'))
    with pytest.raises(ReidentRefused, match="not this case's"):
        run(world)
    write(world.search, text)
    fill_search(world, [False, None, False])  # an answer in slot 3, whose query is empty
    with pytest.raises(ReidentRefused, match="an answer but no query"):
        run(world)


# --- what is written and what is refused ------------------------------------------------------------------


def test_nothing_public_or_printed_holds_a_name_a_cik_or_a_year(tmp_path: Path) -> None:
    world = make_world(tmp_path, decoys=0)
    run(world)
    text = world.public.read_text("utf-8")
    assert set(public(world)) == {
        "reident_version",
        "case",
        "exploratory",
        "status",
        "reason",
        "threshold",
        "provenance",
    }
    assert set(public(world)["provenance"]) == {
        "head",
        "build_sha256",
        "dossier_sha256",
        "record_sha256",
        "search_sha256",
    }
    assert not re.search(r"\b(?:19|20)\d{2}\b", text) and "CY" not in text and "http" not in text
    for secret in (str(OWN_CIK), "CANARY ENTITY", OWN_NAME, "7771", "7772"):
        assert secret not in text
    assert (
        public(world)["provenance"]["record_sha256"]
        == hashlib.sha256(world.record.read_bytes()).hexdigest()
    )


def test_an_existing_public_file_is_refused_before_anything_is_fetched(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    write(world.public, "kept\n")
    with pytest.raises(ReidentRefused, match="never overwritten"):
        run(world)
    assert world.transport.requested == [] and not world.record.exists()
    assert world.public.read_text("utf-8") == "kept\n"


def test_a_rerun_whose_record_would_differ_is_refused(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    stored = record(world)
    stored["matching"]["count"] += 1
    write(world.record, json.dumps(stored))
    with pytest.raises(ReidentRefused, match="differs from what this run found"):
        run(world)
    assert not world.public.exists()


def test_a_rerun_from_the_cache_asks_the_sec_for_nothing_and_finds_the_same_record(
    tmp_path: Path,
) -> None:
    world = make_world(tmp_path)
    run(world)
    asked = len(world.transport.requested)
    before = world.record.read_bytes()
    run(world)
    cached_404s = sum(1 for f in record(world)["frames"] if not f["found"])
    assert (
        len(world.transport.requested) == asked + cached_404s
    )  # only the frames SEC does not have
    assert world.record.read_bytes() == before


def test_the_frames_asked_for_are_the_years_and_tags_the_check_needs(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    run(world)
    for url in world.transport.requested:
        assert re.fullmatch(
            r"https://data\.sec\.gov/api/xbrl/frames/us-gaap/\w+/USD/CY20(22|23|24)\.json", url
        )
    # three years x (four revenue tags, income, cash flow), the first candidate year each time
    assert len(set(world.transport.requested)) == 18


@pytest.mark.parametrize(
    "damage",
    ["dossier", "lock_label", "build", "cik", "freeze"],
)
def test_a_case_that_is_not_frozen_or_not_whole_is_refused_before_anything_is_fetched(
    tmp_path: Path, damage: str
) -> None:
    world = make_world(tmp_path)
    if damage == "dossier":
        write(world.case.dossier_path, DOSSIER + "# changed\n")
    elif damage == "lock_label":
        world.root.joinpath(f"experiment/cases/{LABEL}/case.lock").unlink()
    elif damage == "build":
        world.case.build_path.unlink()
    elif damage == "cik":
        write(world.case.sources_path, json.dumps({"sources": []}))
    else:
        write(world.root / "docs/phases/evidence/phase-5/freeze.json", json.dumps({"cases": []}))
    with pytest.raises(SweepRefusal):
        run(world)
    assert world.transport.requested == [] and not world.record.exists()


def test_a_coarsened_case_is_checked_on_its_own_dossier_and_says_how(tmp_path: Path) -> None:
    world = make_world(tmp_path, probe_set=2, decoys=0)
    run(world)
    kept = record(world)
    assert any("probe set above 1" in line for line in kept["assumptions"])
    assert (world.case.directory / "set-2" / "dossier.toml").is_file()
    assert kept["own"]["matched"] is True  # its own figures sit inside the wider intervals
    plain = build_ratios(build_json())[0]
    wide = build_ratios(build_json(), coarsened=True)[0]
    assert all(
        w.interval.lo <= p.interval.lo and p.interval.hi <= w.interval.hi
        for p, w in zip(plain, wide, strict=True)
    )


def test_the_sec_not_found_is_its_own_error_and_a_block_is_not_swallowed(tmp_path: Path) -> None:
    assert issubclass(EdgarNotFound, EdgarError)
    world = make_world(tmp_path)
    blocked = Transport({})
    blocked.get = lambda url, headers: Response(429, b"")  # type: ignore[method-assign]
    world.transport = blocked
    with pytest.raises(EdgarError, match="429"):
        run(world)
    assert not world.record.exists() and not world.public.exists()


def test_a_frame_that_is_not_shaped_as_expected_is_refused(tmp_path: Path) -> None:
    world = make_world(tmp_path)
    world.transport.served[frame_url("Revenues", 2024)] = json.dumps(
        {"data": [{"cik": 1}]}
    ).encode()
    with pytest.raises(ReidentRefused, match="not shaped as expected"):
        run(world)
    twice = frame_body([(5, E24, 1), (5, E24, 2)])
    world.transport.served[frame_url("Revenues", 2024)] = twice
    with pytest.raises(ReidentRefused, match="not shaped as expected"):
        run(world)


# --- the command line -------------------------------------------------------------------------------------


def patch_cli(monkeypatch: pytest.MonkeyPatch, world: World, *, dirty: str = "") -> None:
    monkeypatch.setattr(cli, "default_repo_root", lambda: world.root)
    monkeypatch.setattr(cli, "open_case", lambda label: CaseAppendix(world.appendix, label))
    monkeypatch.setattr(cli, "sec_user_agent", lambda: "Test Agent test@example.com")
    monkeypatch.setattr(cli, "UrllibTransport", lambda: world.transport)
    monkeypatch.setattr(
        cli,
        "EdgarClient",
        lambda **kwargs: EdgarClient(**kwargs, sleep=lambda seconds: None, now=lambda: NOW),
    )
    monkeypatch.setattr(cli, "_git", lambda *args: dirty if args[0] == "status" else HEAD)


def test_the_command_prints_a_status_and_counts_and_never_a_name_a_cik_or_a_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = make_world(tmp_path, decoys=0)
    patch_cli(monkeypatch, world)
    assert cli.main(["case", "reident", LABEL]) == 0
    out = capsys.readouterr().out
    assert "status: withheld" in out and "ratios used: 8 (at most 8)" in out
    assert "the case's own included: 1" in out and "found and matching: yes" in out
    assert f"wrote experiment/results/cases/{LABEL}/reident.json" in out
    for secret in (
        str(OWN_CIK),
        "CANARY ENTITY",
        "http",
        "data.sec.gov",
        "CY20",
        "Revenues",
        "7771",
    ):
        assert secret not in out
    assert cli.main(["case", "reident", LABEL]) == 2  # the public file exists: refused
    err = capsys.readouterr().err
    assert "never overwritten" in err and str(OWN_CIK) not in err and "http" not in err


def test_the_command_for_a_pending_description_names_the_file_to_fill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = make_world(tmp_path)
    patch_cli(monkeypatch, world)
    assert cli.main(["case", "reident", LABEL]) == 0
    out = capsys.readouterr().out
    assert "status: pending" in out and "wrote reident-search.toml in the case's folder" in out
    assert "the case's own included: 25" in out
    assert str(world.appendix) not in out and not world.public.exists()
    assert cli.main(["case", "reident", LABEL]) == 0
    assert "nothing written" in capsys.readouterr().out


def test_uncommitted_code_is_refused_by_the_command_and_nothing_is_fetched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    world = make_world(tmp_path)
    patch_cli(monkeypatch, world, dirty=" M src/horizon_compact/caseprobe/reident.py")
    assert cli.main(["case", "reident", LABEL]) == 2
    assert "differ from HEAD" in capsys.readouterr().err
    assert (
        world.transport.requested == [] and not world.public.exists() and not world.record.exists()
    )


def test_the_check_is_a_sweep_refusal_and_needs_no_scipy() -> None:
    assert issubclass(ReidentRefused, SweepRefusal)
    code = (
        "import sys, horizon_compact.caseprobe.reident, horizon_compact.cli; "
        "assert 'scipy' not in sys.modules, 'scipy was imported'"
    )
    done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
