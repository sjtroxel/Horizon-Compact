"""Dates relative to the cut-off's fiscal year (Phase 5 code half, build step 5, §4.8)."""

from __future__ import annotations

from datetime import date

import pytest

from horizon_compact.casebuild.dates import DateError, FiscalCalendar, parse_date, quarter_year

JAN = FiscalCalendar(date(2026, 1, 31))  # a year ending 31 January 2026
DEC = FiscalCalendar(date(2025, 12, 31))


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2025, 2, 1), (0, 1)),  # the first day of year N
        (date(2025, 4, 30), (0, 1)),
        (date(2025, 5, 1), (0, 2)),
        (date(2025, 12, 15), (0, 4)),
        (date(2026, 1, 31), (0, 4)),  # the last day of year N
        (date(2026, 2, 1), (1, 1)),  # the year in progress at the cut-off
        (date(2026, 6, 14), (1, 2)),
        (date(2025, 1, 31), (-1, 4)),
        (date(2023, 8, 10), (-2, 3)),  # the year ending January 2024, its third quarter
    ],
)
def test_a_date_is_placed_in_its_fiscal_year_and_quarter(
    day: date, expected: tuple[int, int]
) -> None:
    assert JAN.locate(day) == expected


def test_a_december_year_end_is_the_calendar_year() -> None:
    assert DEC.december and not JAN.december
    assert DEC.locate(date(2025, 3, 31)) == (0, 1)
    assert DEC.locate(date(2025, 12, 31)) == (0, 4)
    assert DEC.locate(date(2026, 1, 1)) == (1, 1)
    assert DEC.locate(date(2024, 7, 4)) == (-1, 3)


def test_a_leap_day_year_end_moves_with_the_calendar() -> None:
    leap = FiscalCalendar(date(2024, 2, 29))
    assert leap.locate(date(2025, 2, 28)) == (1, 4)  # the month-end of the year after
    assert leap.locate(date(2025, 3, 1)) == (2, 1)


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2025, 12, 27), (1, 1)),
        (date(2026, 3, 28), (1, 2)),  # a day past the month boundary, still Q2
        (date(2026, 6, 27), (1, 3)),
        (date(2026, 10, 3), (1, 4)),  # a 53-week year ends a week past the anchor
        (date(2025, 9, 27), (0, 4)),
    ],
)
def test_a_52_53_week_period_end_is_placed_in_the_period_it_ends(
    day: date, expected: tuple[int, int]
) -> None:
    sep = FiscalCalendar(date(2025, 9, 27))
    assert sep.locate_period_end(day) == expected
    assert sep.locate(date(2026, 3, 28)) == (1, 3)  # by the day alone, the next quarter


def test_a_december_period_end_is_unchanged() -> None:
    assert DEC.locate_period_end(date(2025, 3, 31)) == (0, 1)
    assert DEC.locate_period_end(date(2025, 12, 31)) == (0, 4)
    assert JAN.locate_period_end(date(2026, 1, 31)) == (0, 4)


def test_labels_name_the_year_relative_to_the_latest() -> None:
    assert JAN.year_label(0) == "fiscal year N"
    assert JAN.year_label(-1) == "fiscal year N-1"
    assert JAN.year_label(2) == "fiscal year N+2"
    assert JAN.label(date(2025, 8, 20)) == "fiscal year N, third quarter"
    assert JAN.label(date(2026, 3, 31)) == "fiscal year N+1, first quarter"


def test_a_year_is_read_as_the_fiscal_year_ending_in_it() -> None:
    assert JAN.year_ending_in(2026) == "fiscal year N"
    assert JAN.year_ending_in(2025) == "fiscal year N-1"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("March 31, 2026", date(2026, 3, 31)),
        ("Mar. 31, 2026", date(2026, 3, 31)),
        ("March 1st, 2026", date(2026, 3, 1)),
        ("31 March 2026", date(2026, 3, 31)),
        ("March 2026", date(2026, 3, 31)),  # a month alone is read at its end
        ("February of 2024", date(2024, 2, 29)),
        ("2026-03-31", date(2026, 3, 31)),
        ("3/31/2026", date(2026, 3, 31)),
        ("3/31/26", date(2026, 3, 31)),
    ],
)
def test_every_date_form_is_parsed(text: str, expected: date) -> None:
    assert parse_date(text) == expected


@pytest.mark.parametrize("text", ["February 30, 2026", "13/40/2026", "2026-02-31"])
def test_a_date_that_is_not_real_is_an_error(text: str) -> None:
    with pytest.raises(DateError):
        parse_date(text)


def test_quarter_forms() -> None:
    assert quarter_year("third quarter of fiscal 2025") == (3, 2025)
    assert quarter_year("Fourth Quarter 2024") == (4, 2024)
    assert quarter_year("Q2 FY2026") == (2, 2026)
    assert quarter_year("q1 2025") == (1, 2025)
