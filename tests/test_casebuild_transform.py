"""Dates and numbers in one pass (Phase 5 code half, build step 5, §4.8)."""

from __future__ import annotations

from datetime import date

import pytest

from horizon_compact.casebuild.dates import FiscalCalendar
from horizon_compact.casebuild.transform import transform

JAN = FiscalCalendar(date(2026, 1, 31))
DEC = FiscalCalendar(date(2025, 12, 31))
FACTOR = 1.2


def run(text: str, calendar: FiscalCalendar = DEC, factor: float = FACTOR):  # type: ignore[no-untyped-def]
    return transform(text, calendar=calendar, factor=factor)


def kinds(result) -> list[str]:  # type: ignore[no-untyped-def]
    return [f.kind for f in result.flags]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Revenue was $1,500.0 million.", "Revenue was $1,800 million."),
        ("Revenue was $11.4 million.", "Revenue was $13.7 million."),
        ("a $2 billion facility", "a $2.40 billion facility"),
        ("fees of $56,050", "fees of $67,300"),
        ("loss of -$9.0 million", "loss of -$10.8 million"),
        ("cost $5M, once", "cost $6.00M, once"),
        ("cost US$250 thousand", "cost US$300 thousand"),
    ],
)
def test_dollar_figures_are_scaled_in_their_own_unit_to_three_digits(
    text: str, expected: str
) -> None:
    result = run(text)
    assert result.text == expected
    assert result.flags == []


@pytest.mark.parametrize(
    "text",
    [
        "Margin rose 3.5% to 12.0 percent, or 40 basis points.",
        "a ten-year program of 10 years, 6 months and 3 quarters",
        "see Item 7, Note 12, Part II and Exhibit 99",
        "the 10-K and 10-Q and a 401(k) plan, in the 3rd place",
    ],
)
def test_percentages_durations_labels_and_form_names_are_left_alone(text: str) -> None:
    result = run(text)
    assert result.text == text and result.flags == []


@pytest.mark.parametrize(
    "text",
    [
        "average pay was $56,050 a year",  # an average is a ratio of two scaled quantities
        "the average annual wage of $56,050",
        "hourly wage of $27",
        "paid $27 an hour",
        "$27 per hour",
        "revenue of $410,000 per employee",
        "$91,780 a year on average",
        "$91,780 per worker",
    ],
)
def test_a_dollar_figure_stated_per_employee_or_per_hour_is_not_scaled(text: str) -> None:
    result = run(text)
    assert result.text == text
    assert result.flags == []
    assert result.counts["dollar_ratio_unscaled"] == 1


def test_a_total_next_to_an_average_is_still_scaled() -> None:
    result = run("average pay was $56,050 a year and total payroll was $70.0 million")
    assert result.text == "average pay was $56,050 a year and total payroll was $84.0 million"


def test_per_share_figures_and_share_counts_are_flagged_for_removal_and_not_scaled() -> None:
    result = run("Earnings were $2.10 per share on 2,500 shares and 4.2 million shares.")
    assert result.text == "Earnings were $2.10 per share on 2,500 shares and 4.2 million shares."
    assert [f.text for f in result.flags] == ["$2.10", "2,500 shares", "4.2 million shares"]
    assert all("remove" in k for k in kinds(result))


def test_a_small_dollar_figure_with_no_unit_is_flagged_and_not_scaled() -> None:
    result = run("down from $19.7 million ($1.01), and $99 against $100")
    assert result.text == "down from $23.6 million ($1.01), and $99 against $120"
    assert [f.text for f in result.flags] == ["$1.01", "$99"]
    assert all("under $100 with no unit" in k for k in kinds(result))


def test_a_small_rate_is_still_a_ratio_and_not_flagged() -> None:
    result = run("paid $25 an hour")
    assert result.text == "paid $25 an hour"
    assert result.flags == []


@pytest.mark.parametrize(
    "text",
    [
        "earned $1.35 per diluted share",
        "earned $1.35 per basic share",
        "earned $1.35 per basic and diluted share",
        "earned $1.35 per diluted common share",
        "earned $1.35/diluted share",
    ],
)
def test_a_basic_or_diluted_per_share_figure_is_flagged_and_not_scaled(text: str) -> None:
    result = run(text)
    assert result.text == text
    assert kinds(result) == ["per-share figure: remove it (§4.8)"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("We employ 1,240 people.", "We employ 1,490 people."),
        ("about 1,240 people", "about 1,490 people"),
        ("1,240 full-time employees", "1,490 full-time employees"),
        ("1,240 part-time hourly workers", "1,490 part-time hourly workers"),
        ("employs approximately 300 at the site", "employs approximately 360 at the site"),
        ("headcount of 1,000", "headcount of 1,200"),
        ("1,240 people, of whom 310 are represented", "1,490 people, of whom 370 are represented"),
    ],
)
def test_headcounts_are_scaled_and_rounded_to_five(text: str, expected: str) -> None:
    result = run(text)
    assert result.text == expected
    assert result.flags == []


def test_a_scaled_headcount_under_100_is_stated_as_fewer_than_100_and_loses_its_hedge() -> None:
    result = run("The site has about 60 employees and 80 workers.")
    assert result.text == "The site has fewer than 100 employees and fewer than 100 workers."


def test_a_headcount_in_words_or_a_unit_volume_or_a_stray_number_is_flagged_not_dropped() -> None:
    result = run("two thousand employees, 5,000 tons, Plant 6, 12 units, 77 widgets")
    assert result.text == "two thousand employees, 5,000 tons, Plant 6, 12 units, 77 widgets"
    assert [f.text for f in result.flags] == [
        "two thousand employees",
        "5,000 tons",
        "6",
        "12 units",
        "77",
    ]
    assert "headcount in words" in kinds(result)[0]
    assert "unit volume" in kinds(result)[1]
    assert kinds(result)[2] == "unclassified number"


def test_flags_carry_the_line_they_are_on() -> None:
    result = run("a\nb\nPlant 6 and 77 widgets")
    assert [(f.line, f.text) for f in result.flags] == [(3, "6"), (3, "77")]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("on March 31, 2025", "on fiscal year N, first quarter"),
        ("on 31 March 2025", "on fiscal year N, first quarter"),
        ("in Aug. 2025", "in fiscal year N, third quarter"),
        ("on 2025-12-31", "on fiscal year N, fourth quarter"),
        ("on 12/31/2024", "on fiscal year N-1, fourth quarter"),
        ("as of June 14, 2026", "as of fiscal year N+1, second quarter"),
        ("for the fiscal year ended December 31, 2025, we", "for fiscal year N, we"),
        ("for the year ended December 31, 2024, we", "for fiscal year N-1, we"),
        ("the quarter ended September 30, 2025", "fiscal year N, third quarter"),
        ("in the third quarter of fiscal 2025", "in the fiscal year N, third quarter"),
        (
            "Q2 2024 and Q4 FY2025",
            "fiscal year N-1, second quarter and fiscal year N, fourth quarter",
        ),
        ("in fiscal 2024 and fiscal year 2023", "in fiscal year N-1 and fiscal year N-2"),
        ("in 2025, 2024 and 2022", "in fiscal year N, fiscal year N-1 and fiscal year N-3"),
    ],
)
def test_dates_become_relative_to_the_year_just_ended(text: str, expected: str) -> None:
    result = run(text, DEC)
    assert result.text == expected
    assert result.flags == []


def test_a_year_end_other_than_december_flags_the_year_reading_it_assumed() -> None:
    result = run("In fiscal 2025 sales rose; in 2024 they fell.", JAN)
    assert result.text == "In fiscal year N-1 sales rose; in fiscal year N-2 they fell."
    assert len(result.flags) == 2
    assert all("convention assumed" in f.kind for f in result.flags)


SEP = FiscalCalendar(date(2025, 9, 27))  # a 52/53-week year ending on a Saturday near 30 September


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("the first quarter ended December 27, 2025", "fiscal year N+1, first quarter"),
        ("the second quarter ended March 28, 2026", "fiscal year N+1, second quarter"),
        ("the third fiscal quarter ended June 27, 2026", "fiscal year N+1, third quarter"),
        ("for the fiscal year ending October 3, 2026", "for fiscal year N+1"),
        ("for the year ended September 27, 2025", "for fiscal year N"),
        ("the quarter ended March 28, 2026", "fiscal year N+1, second quarter"),
    ],
)
def test_a_period_end_of_a_52_53_week_year_is_placed_in_the_quarter_it_ends(
    text: str, expected: str
) -> None:
    result = run(text, SEP)
    assert result.text == expected
    assert result.flags == []


def test_the_stated_quarter_is_replaced_with_its_phrase_and_leaves_no_stray_ordinal() -> None:
    result = run("results for the first quarter ended March 31, 2025 were filed", DEC)
    assert result.text == "results for fiscal year N, first quarter were filed"


def test_a_stated_quarter_that_its_end_date_contradicts_is_flagged() -> None:
    result = run("the second quarter ended September 30, 2025", DEC)
    assert result.text == "fiscal year N, third quarter"
    assert kinds(result) == ["quarter named does not match its end date: check it"]


def test_a_period_of_any_length_is_placed_by_its_day() -> None:
    result = run("the period ended March 28, 2026", SEP)
    assert result.text == "fiscal year N+1, third quarter"


def test_a_full_date_is_exact_for_any_year_end_and_needs_no_flag() -> None:
    result = run("for the fiscal year ended January 31, 2026 and on March 8, 2026", JAN)
    assert result.text == "for fiscal year N and on fiscal year N+1, first quarter"
    assert result.flags == []


@pytest.mark.parametrize("text", ["on March 15, we paid", "since May 3 the plant"])
def test_a_month_and_day_without_a_year_is_flagged_and_left(text: str) -> None:
    result = run(text)
    assert result.text == text
    assert kinds(result) == ["date without a year: not relative-able"]


def test_a_date_that_is_not_real_is_flagged_and_left() -> None:
    result = run("on February 30, 2025")
    assert result.text == "on February 30, 2025"
    assert kinds(result) == ["date that is not a real date"]


def test_a_year_inside_a_figure_or_a_longer_number_is_not_read_as_a_year() -> None:
    result = run("$2,025 million and 12,025 people and 2025.5 and 1-2025")
    assert result.text.startswith(
        "$2,430 million and 14,430"
    )  # scaled as a dollar figure and a headcount
    assert "fiscal year" not in result.text.split("and 2025.5")[0]


def test_the_labels_it_writes_are_not_flagged_as_numbers() -> None:
    result = run("fiscal year N-1: $800.0 million\nfiscal year N+1: not available")
    assert result.flags == []
    assert result.text == "fiscal year N-1: $960 million\nfiscal year N+1: not available"


def test_newlines_survive_so_line_numbers_stay_true() -> None:
    text = "a $1.0 million\n\nb 3.5%\nc"
    assert run(text).text.count("\n") == text.count("\n")


def test_one_pay_figure_and_one_headcount_on_a_line_are_checked_after_rounding() -> None:
    result = run("Payroll was $70.0 million for 1,240 employees.")
    assert result.text == "Payroll was $84.0 million for 1,490 employees."
    assert len(result.pay_checks) == 1
    assert result.pay_checks[0].passed and result.pay_checks[0].line == 1


def test_a_pay_line_with_a_small_group_is_recorded_as_not_checked() -> None:
    result = run("Payroll was $1.0 million for 60 employees.")
    assert result.pay_checks[0].passed and "not checked" in result.pay_checks[0].note


def test_a_line_with_several_pay_or_headcount_figures_is_flagged_for_a_hand_check() -> None:
    result = run("Payroll was $70.0 million and wages $5.0 million for 1,240 employees.")
    assert "pay per head not checked: several figures on one line" in kinds(result)
    assert "check by hand" in result.pay_checks[0].note


def test_a_line_with_money_but_no_pay_words_is_not_a_pay_check() -> None:
    result = run("Revenue was $70.0 million and we have 1,240 employees.")
    assert result.pay_checks == []


def test_the_record_lists_counts_flags_and_checks() -> None:
    record = run("Payroll was $70.0 million for 1,240 employees; Plant 6.").record()
    assert record["counts"] == {"dollar": 1, "headcount": 1}
    assert [f["text"] for f in record["flags"]] == ["6"]
    assert len(record["pay_checks"]) == 1


# --- Opus review fixes, 2026-10-11 ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "the codec 2025 release",
            "the codec fiscal year N release",
        ),  # "dec" inside a word is no month
        ("Dismay 3, 2025", "Dismay 3, fiscal year N"),
        ("a Primary 5, 2026 note", "a Primary 5, fiscal year N+1 note"),
    ],
)
def test_a_month_name_inside_a_longer_word_is_not_a_month(text: str, expected: str) -> None:
    assert run(text).text == expected


@pytest.mark.parametrize(
    "text",
    [
        "Revenue per employee of $410,000",
        "pay per hour of $27",
        "spending per capita was $1,200",
    ],
)
def test_a_ratio_named_before_its_figure_is_not_scaled(text: str) -> None:
    result = run(text)
    assert result.text == text
    assert result.counts["dollar_ratio_unscaled"] == 1


def test_a_hedge_is_dropped_before_fewer_than_100_in_either_headcount_form() -> None:
    assert run("It employs approximately 60.").text == "It employs fewer than 100."
    assert run("It employs approximately 1,000.").text == "It employs approximately 1,200."
