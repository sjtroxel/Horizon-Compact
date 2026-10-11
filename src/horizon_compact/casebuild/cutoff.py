"""The cut-off filter: the one place a filing's date is compared with the cut-off (IMPLEMENTATION §4.3).

**The rule (decision 3, protocol §12.6): a document is admitted only if its filing date is strictly before the
cut-off date.** The filing date is read, never the period a filing covers, so an amendment filed after the
cut-off is out even though it amends an earlier year. Every document and every tagged figure passes ``admit``;
nothing reaches extraction or the figures without it.

The acceptance time is not a second rule. A filing accepted after the day's close is dated the next business
day, so its filing date already excludes it. The filter only checks that the two agree, with the acceptance
time (UTC in the SEC's data) converted to US Eastern first so a late-evening acceptance is not read a day
late, and refuses a filing where they do not.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")


class CutoffError(Exception):
    """A date is missing or malformed, or a filing's dates disagree. Never treated as admitted."""


@dataclass(frozen=True)
class FilingStamp:
    """What the filter reads about a document or a figure: when it was filed, and when accepted if known."""

    filed: date
    accepted: datetime | None = None  # timezone-aware
    label: str = ""  # an accession number, for error messages only


def parse_date(value: object, *, what: str) -> date:
    if not isinstance(value, str):
        raise CutoffError(f"{what} is missing or not text")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CutoffError(f"{what} is not a date in YYYY-MM-DD form") from exc


def parse_acceptance(value: object) -> datetime:
    """The SEC's ``acceptanceDateTime``, such as ``2026-08-20T14:59:01.000Z``; must carry a timezone."""
    if not isinstance(value, str):
        raise CutoffError("the acceptance time is missing or not text")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CutoffError("the acceptance time is not an ISO date-time") from exc
    if moment.tzinfo is None:
        raise CutoffError("the acceptance time carries no timezone")
    return moment


def stamp_from_submissions_row(row: Mapping[str, Any]) -> FilingStamp:
    """One filing of the submissions table (``filingDate``, ``acceptanceDateTime``, ``accessionNumber``).

    Every filing in the real table carries an acceptance time (§11), so a missing one is bad data and is
    refused, never a skipped check. ``reportDate``, the period covered, is deliberately not read.
    """
    return FilingStamp(
        filed=parse_date(row.get("filingDate"), what="filingDate"),
        accepted=parse_acceptance(row.get("acceptanceDateTime")),
        label=str(row.get("accessionNumber", "")),
    )


def stamp_from_fact(fact: Mapping[str, Any]) -> FilingStamp:
    """One tagged figure of the company-facts file: dated by ``filed``, never ``fy``, ``fp`` or ``frame``."""
    return FilingStamp(
        filed=parse_date(fact.get("filed"), what="filed"), label=str(fact.get("accn", ""))
    )


def check_consistent(stamp: FilingStamp) -> None:
    """The acceptance date in US Eastern must be on or before the filing date."""
    if stamp.accepted is None:
        return
    accepted_day = stamp.accepted.astimezone(EASTERN).date()
    if accepted_day > stamp.filed:
        raise CutoffError(
            f"filing {stamp.label or '(unlabelled)'}: accepted {accepted_day} (US Eastern), "
            f"after its filing date {stamp.filed}"
        )


def admit(stamp: FilingStamp, cutoff: date) -> bool:
    """True if the document or figure was filed strictly before ``cutoff``. Raises if its dates disagree."""
    check_consistent(stamp)
    return stamp.filed < cutoff
