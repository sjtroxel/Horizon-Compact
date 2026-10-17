"""The cut-off filter (Phase 5 code half, build step 3): strictly before the cut-off, on the filing date."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from edgar_helpers import company_fact, submissions_row
from horizon_compact.casebuild.cutoff import (
    CutoffError,
    FilingStamp,
    admit,
    parse_acceptance,
    stamp_from_fact,
    stamp_from_submissions_row,
)

CUTOFF = date(2026, 6, 15)


@pytest.mark.parametrize(
    ("filed", "admitted"),
    [
        (date(2026, 6, 13), True),
        (date(2026, 6, 14), True),  # the day before the cut-off
        (date(2026, 6, 15), False),  # the cut-off day itself: strict
        (date(2026, 6, 16), False),
    ],
)
def test_each_side_of_the_boundary(filed: date, admitted: bool) -> None:
    assert admit(FilingStamp(filed=filed), CUTOFF) is admitted


def test_a_row_is_dated_by_its_filing_date_not_the_period_it_covers() -> None:
    """An amendment filed after the cut-off is out even though it covers an earlier period."""
    row = submissions_row(2)  # the 10-K: filed 2026-03-02, covers the year to 2026-01-31
    row["filingDate"] = "2026-06-20"  # an amendment, filed late
    stamp = stamp_from_submissions_row(row)
    assert stamp.filed == date(2026, 6, 20)
    assert admit(stamp, CUTOFF) is False


def test_a_row_reads_the_real_field_names() -> None:
    stamp = stamp_from_submissions_row(submissions_row(1))
    assert stamp.filed == date(2026, 5, 8)
    assert stamp.label == "0009999999-26-000002"
    assert stamp.accepted == datetime(2026, 5, 8, 20, 15, 30, tzinfo=UTC)
    assert admit(stamp, CUTOFF) is True


def test_a_fact_is_dated_by_filed_never_by_fiscal_year_or_frame() -> None:
    early = stamp_from_fact(company_fact(filed="2026-06-14", fy=2099, frame="CY2099"))
    late = stamp_from_fact(company_fact(filed="2026-06-15", fy=1999))
    assert admit(early, CUTOFF) is True
    assert admit(late, CUTOFF) is False


def test_late_evening_acceptance_is_read_in_eastern_time_not_utc() -> None:
    """Accepted 02:00 UTC on the 21st is 22:00 on the 20th in New York, consistent with filing on the 20th."""
    stamp = stamp_from_submissions_row(submissions_row(0))
    assert stamp.filed == date(2026, 8, 20)
    assert (
        admit(stamp, date(2026, 8, 21)) is True
    )  # no error, and filed the 20th is before the 21st


def test_standard_time_is_handled_too() -> None:
    accepted = parse_acceptance("2026-01-15T04:30:00.000Z")  # 23:30 on the 14th in New York (EST)
    assert admit(FilingStamp(filed=date(2026, 1, 14), accepted=accepted), date(2026, 2, 1)) is True


def test_an_acceptance_after_the_filing_date_that_straddles_the_cutoff_is_refused() -> None:
    accepted = parse_acceptance("2026-06-15T15:00:00.000Z")  # accepted on the cut-off day
    stamp = FilingStamp(filed=date(2026, 6, 14), accepted=accepted, label="0009999999-26-000099")
    with pytest.raises(CutoffError, match="0009999999-26-000099"):
        admit(stamp, CUTOFF)


def test_an_acceptance_after_the_filing_date_both_before_the_cutoff_is_admitted() -> None:
    """A filing-date adjustment years before the cut-off cannot change admission (2026-10-17, his)."""
    accepted = parse_acceptance("2016-03-08T14:04:21.000Z")
    assert admit(FilingStamp(filed=date(2016, 3, 7), accepted=accepted), CUTOFF) is True


def test_an_acceptance_after_the_filing_date_both_on_or_after_the_cutoff_is_not_admitted() -> None:
    accepted = parse_acceptance("2026-07-02T15:00:00.000Z")
    assert admit(FilingStamp(filed=date(2026, 7, 1), accepted=accepted), CUTOFF) is False
    accepted = parse_acceptance("2026-06-16T15:00:00.000Z")
    assert admit(FilingStamp(filed=date(2026, 6, 15), accepted=accepted), CUTOFF) is False


def test_a_filing_accepted_after_the_close_and_dated_next_day_is_consistent() -> None:
    """Accepted Friday evening, filed Monday: the acceptance date is earlier, which is fine."""
    accepted = parse_acceptance("2026-06-12T23:00:00.000Z")  # 19:00 Friday in New York
    assert admit(FilingStamp(filed=date(2026, 6, 15), accepted=accepted), date(2026, 7, 1)) is True


@pytest.mark.parametrize("bad", [None, "", "2026-13-01", "June 1, 2026", 20260601])
def test_a_missing_or_malformed_filing_date_is_an_error_not_a_pass(bad: object) -> None:
    with pytest.raises(CutoffError):
        stamp_from_submissions_row({"filingDate": bad})
    with pytest.raises(CutoffError):
        stamp_from_fact({"filed": bad})


@pytest.mark.parametrize("bad", ["2026-05-08T20:15:30", "yesterday", 5, None])
def test_a_malformed_or_naive_acceptance_time_is_an_error(bad: object) -> None:
    with pytest.raises(CutoffError):
        parse_acceptance(bad)


@pytest.mark.parametrize("missing", [None, ""])
def test_a_row_without_an_acceptance_time_is_refused_not_admitted(missing: object) -> None:
    row = submissions_row(1)
    row["acceptanceDateTime"] = missing
    with pytest.raises(CutoffError, match="acceptance time"):
        stamp_from_submissions_row(row)
    del row["acceptanceDateTime"]
    with pytest.raises(CutoffError, match="acceptance time"):
        stamp_from_submissions_row(row)


def test_a_figure_needs_no_acceptance_time() -> None:
    """The company-facts file has none; a figure is checked on ``filed`` alone."""
    assert stamp_from_fact(company_fact()).accepted is None
