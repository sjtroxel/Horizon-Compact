"""Figures from XBRL, for dossier sections 4 and 5 (IMPLEMENTATION §4.6). No model is in the number path.

From the company-facts file, each tagged figure admitted by the cut-off filter on its own ``filed`` date. For
every line, a fixed list of tags is tried in order and the one used is recorded. Rules, from §11's findings:

- **Keyed by ``start`` and ``end``, never by ``fy`` or ``fp``** (they describe the filing, not the figure),
  and ``frame`` is never read. A fiscal year is dated by its ``end``.
- **A period reported in several filings takes the latest admitted one** (a restatement known before the
  cut-off). Two admitted filings of the same day that disagree leave that year out, listed, not guessed.
- **An annual figure is one whose period runs 355 to 375 days** (52 and 53-week years run 364 and 371; the
  real file's annual rows ran 364 or 365). A balance has no ``start``.
- **Three fiscal years ending at the latest admitted annual figure**, found by chaining back from it through
  year ends 350 to 380 days apart.
- **A tag is used only if it has an admitted figure for the latest fiscal year** (decision of this step, for
  review): the first such tag in the list. Years that tag lacks are listed, never filled from another tag,
  since mixing tags across years is a judgment. A line with no such tag is left out and listed, never filled
  from text.
- Only USD figures. Per-share figures and share counts are not read at all (§4.8).

**Only the first tags of the revenue, operating income, operating cash flow, debt and capital-spending lines
were seen in a real file (§11). The other tags are known us-gaap names not yet checked against a real filer;
the search half may add a tag, logged.**
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from horizon_compact.casebuild.cutoff import admit, parse_date, stamp_from_fact

ANNUAL_DAYS = range(355, 376)
YEAR_GAP_DAYS = range(350, 381)
YEARS = 3


@dataclass(frozen=True)
class LineSpec:
    name: str
    section: int
    kind: Literal["flow", "instant"]
    tags: tuple[str, ...]


LINES: tuple[LineSpec, ...] = (
    LineSpec(
        "revenue",
        4,
        "flow",
        (
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
        ),
    ),
    LineSpec("operating_income", 4, "flow", ("OperatingIncomeLoss",)),
    LineSpec("operating_cash_flow", 4, "flow", ("NetCashProvidedByUsedInOperatingActivities",)),
    LineSpec(
        "long_term_debt",
        4,
        "instant",
        ("LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"),
    ),
    LineSpec(
        "cash",
        4,
        "instant",
        (
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ),
    ),
    LineSpec(
        "capital_spending",
        5,
        "flow",
        ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"),
    ),
    LineSpec(
        "research_and_development",
        5,
        "flow",
        (
            "ResearchAndDevelopmentExpense",
            "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        ),
    ),
    LineSpec(
        "dividends_paid", 5, "flow", ("PaymentsOfDividends", "PaymentsOfDividendsCommonStock")
    ),
    LineSpec("share_repurchases", 5, "flow", ("PaymentsForRepurchaseOfCommonStock",)),
    LineSpec("acquisitions", 5, "flow", ("PaymentsToAcquireBusinessesNetOfCashAcquired",)),
)


class FiguresError(Exception):
    """The facts file is not shaped as expected."""


@dataclass(frozen=True)
class Figure:
    value: float
    end: date
    start: date | None
    filed: date
    accession: str
    form: str


@dataclass
class FigureLine:
    name: str
    section: int
    tag: str
    by_year: dict[date, Figure] = field(default_factory=dict)


@dataclass
class FigureTable:
    year_ends: tuple[date, ...]  # latest first
    lines: dict[str, FigureLine]
    omitted: list[dict[str, str | None]]

    def record(self) -> dict[str, Any]:
        """The part of ``build.json`` this step owns: what was used, from which filing, what was left out."""
        return {
            "year_ends": [d.isoformat() for d in self.year_ends],
            "lines": {
                name: {
                    "section": line.section,
                    "tag": line.tag,
                    "years": {
                        end.isoformat(): {
                            "value": fig.value,
                            "filed": fig.filed.isoformat(),
                            "accession": fig.accession,
                            "form": fig.form,
                        }
                        for end, fig in sorted(line.by_year.items(), reverse=True)
                    },
                }
                for name, line in self.lines.items()
            },
            "omitted": self.omitted,
        }


def _tag_facts(facts: Mapping[str, Any], tag: str) -> list[Mapping[str, Any]]:
    block = facts.get("facts")
    if not isinstance(block, Mapping):
        raise FiguresError("the company-facts file has no 'facts' block")
    entry = block.get("us-gaap", {}).get(tag)
    if not isinstance(entry, Mapping):
        return []
    usd = entry.get("units", {}).get("USD", [])
    return [f for f in usd if isinstance(f, Mapping)]


def _admitted(
    facts: Mapping[str, Any], spec: LineSpec, tag: str, cutoff: date
) -> list[tuple[Mapping[str, Any], date, date | None, date]]:
    """Usable figures of one tag: (fact, end, start, filed), admitted by the cut-off filter."""
    found: list[tuple[Mapping[str, Any], date, date | None, date]] = []
    for fact in _tag_facts(facts, tag):
        stamp = stamp_from_fact(fact)
        if not admit(stamp, cutoff):
            continue
        end = parse_date(fact.get("end"), what="end")
        if spec.kind == "flow":
            if "start" not in fact:
                continue
            start = parse_date(fact["start"], what="start")
            if (end - start).days not in ANNUAL_DAYS:
                continue
            found.append((fact, end, start, stamp.filed))
        elif "start" not in fact:
            found.append((fact, end, None, stamp.filed))
    return found


def _year_ends(facts: Mapping[str, Any], cutoff: date) -> tuple[date, ...]:
    ends: set[date] = set()
    for spec in LINES:
        if spec.kind != "flow":
            continue
        for tag in spec.tags:
            ends.update(end for _, end, _, _ in _admitted(facts, spec, tag, cutoff))
    if not ends:
        return ()
    ordered = sorted(ends, reverse=True)
    chain = [ordered[0]]
    for end in ordered[1:]:
        if len(chain) == YEARS:
            break
        if (chain[-1] - end).days in YEAR_GAP_DAYS:
            chain.append(end)
    return tuple(chain)


def _pick(
    candidates: list[tuple[Mapping[str, Any], date, date | None, date]],
) -> Figure | None:
    """The latest-filed figure for one year end; None if same-day filings disagree on its value."""
    latest = max(filed for _, _, _, filed in candidates)
    top = [c for c in candidates if c[3] == latest]
    if len({c[0].get("val") for c in top}) > 1:
        return None
    fact, end, start, filed = top[0]
    return Figure(
        value=fact["val"],
        end=end,
        start=start,
        filed=filed,
        accession=str(fact.get("accn", "")),
        form=str(fact.get("form", "")),
    )


def extract_figures(facts: Mapping[str, Any], cutoff: date) -> FigureTable:
    year_ends = _year_ends(facts, cutoff)
    table = FigureTable(year_ends=year_ends, lines={}, omitted=[])
    if not year_ends:
        table.omitted.append(
            {"line": None, "year_end": None, "reason": "no admitted annual figure at all"}
        )
        return table
    latest = year_ends[0]
    for spec in LINES:
        chosen: tuple[str, dict[date, list[Any]]] | None = None
        for tag in spec.tags:
            by_end: dict[date, list[Any]] = {}
            for candidate in _admitted(facts, spec, tag, cutoff):
                by_end.setdefault(candidate[1], []).append(candidate)
            if latest in by_end:
                chosen = (tag, by_end)
                break
        if chosen is None:
            table.omitted.append(
                {
                    "line": spec.name,
                    "year_end": latest.isoformat(),
                    "reason": "no listed tag has an admitted figure for the latest fiscal year",
                }
            )
            continue
        tag, by_end = chosen
        line = FigureLine(name=spec.name, section=spec.section, tag=tag)
        for end in year_ends:
            if end not in by_end:
                table.omitted.append(
                    {
                        "line": spec.name,
                        "year_end": end.isoformat(),
                        "reason": f"tag {tag} has no admitted figure",
                    }
                )
                continue
            figure = _pick(by_end[end])
            if figure is None:
                reason = f"admitted filings of the same day disagree on tag {tag}"
                table.omitted.append(
                    {"line": spec.name, "year_end": end.isoformat(), "reason": reason}
                )
                continue
            line.by_year[end] = figure
        table.lines[spec.name] = line
    return table
