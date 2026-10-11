"""Figures from XBRL (Phase 5 code half, build step 4, §4.6)."""

from __future__ import annotations

from datetime import date

import pytest

from edgar_helpers import annual, balance, facts_file
from horizon_compact.casebuild.cutoff import CutoffError
from horizon_compact.casebuild.figures import FiguresError, extract_figures

CUTOFF = date(2026, 6, 15)
JAN26, JAN25, JAN24 = date(2026, 1, 31), date(2025, 1, 31), date(2024, 1, 31)


def _revenue_history() -> list[dict[str, object]]:
    return [
        annual(2024, 800, "2024-03-04", "r24"),
        annual(2025, 900, "2025-03-03", "r25"),
        annual(2026, 1000, "2026-03-02", "r26"),
    ]


def test_three_fiscal_years_ending_at_the_latest_admitted_annual_figure() -> None:
    table = extract_figures(facts_file({"Revenues": _revenue_history()}), CUTOFF)
    assert table.year_ends == (JAN26, JAN25, JAN24)
    line = table.lines["revenue"]
    assert line.tag == "Revenues"
    assert {end: fig.value for end, fig in line.by_year.items()} == {
        JAN26: 1000,
        JAN25: 900,
        JAN24: 800,
    }
    assert line.section == 4


def test_a_year_reported_again_as_a_comparative_takes_the_latest_admitted_filing() -> None:
    history = [*_revenue_history(), annual(2025, 950, "2026-03-02", "r25-restated", fy=2026)]
    table = extract_figures(facts_file({"Revenues": history}), CUTOFF)
    figure = table.lines["revenue"].by_year[JAN25]
    assert figure.value == 950
    assert figure.accession == "r25-restated"


def test_a_restatement_filed_after_the_cutoff_is_never_seen() -> None:
    history = [*_revenue_history(), annual(2026, 777, "2026-07-01", "r26-late")]
    table = extract_figures(facts_file({"Revenues": history}), CUTOFF)
    assert table.lines["revenue"].by_year[JAN26].value == 1000
    on_the_day = [*_revenue_history(), annual(2026, 777, "2026-06-15", "r26-same-day")]
    assert (
        extract_figures(facts_file({"Revenues": on_the_day}), CUTOFF)
        .lines["revenue"]
        .by_year[JAN26]
        .value
        == 1000
    )


def test_a_year_that_only_exists_after_the_cutoff_does_not_move_the_latest_year() -> None:
    history = [*_revenue_history(), annual(2027, 1200, "2026-07-01", "r27-late")]
    assert extract_figures(facts_file({"Revenues": history}), CUTOFF).year_ends[0] == JAN26


def test_fy_and_fp_and_frame_are_never_read() -> None:
    """One annual period carries ``fy`` 2025 in one filing and 2026 in the next; neither moves the year."""
    history = [
        annual(2026, 1000, "2026-03-02", "a", fy=1999, frame="CY1999"),
        annual(2025, 900, "2025-03-03", "b", fy=2077),
        annual(2024, 800, "2024-03-04", "c", fp="Q9"),
    ]
    table = extract_figures(facts_file({"Revenues": history}), CUTOFF)
    assert table.year_ends == (JAN26, JAN25, JAN24)


def test_quarterly_and_nine_month_rows_are_not_annual_figures() -> None:
    quarter = annual(2026, 250, "2026-03-02", "q", start="2025-11-01")  # 91 days
    nine_months = annual(2026, 700, "2026-03-02", "n", start="2025-05-01")  # 275 days
    table = extract_figures(
        facts_file({"Revenues": [quarter, nine_months, *_revenue_history()]}), CUTOFF
    )
    assert table.lines["revenue"].by_year[JAN26].value == 1000


@pytest.mark.parametrize(
    "start", ["2025-02-02", "2025-01-27"]
)  # 364 and 370 days: 52 and 53-week years
def test_fifty_two_and_fifty_three_week_years_count_as_annual(start: str) -> None:
    table = extract_figures(
        facts_file({"Revenues": [annual(2026, 1000, "2026-03-02", start=start)]}), CUTOFF
    )
    assert table.year_ends == (JAN26,)


def test_the_first_tag_with_a_latest_year_figure_is_used_and_recorded() -> None:
    older_tag = [annual(2024, 800, "2024-03-04"), annual(2025, 900, "2025-03-03")]  # stops at FY25
    newer_tag = [annual(2025, 901, "2026-03-02"), annual(2026, 1000, "2026-03-02")]
    table = extract_figures(
        facts_file(
            {
                "Revenues": older_tag,
                "RevenueFromContractWithCustomerExcludingAssessedTax": newer_tag,
                "OperatingIncomeLoss": _revenue_history(),
            }
        ),
        CUTOFF,
    )
    line = table.lines["revenue"]
    assert line.tag == "RevenueFromContractWithCustomerExcludingAssessedTax"
    # The years that tag lacks are listed, not filled from the other tag.
    assert JAN24 not in line.by_year
    assert {
        "line": "revenue",
        "year_end": JAN24.isoformat(),
        "reason": f"tag {line.tag} has no admitted figure",
    } in table.omitted


def test_a_line_whose_tags_have_no_latest_year_is_left_out_and_listed() -> None:
    facts = {
        "Revenues": _revenue_history(),
        "OperatingIncomeLoss": [annual(2025, 90, "2025-03-03")],
    }
    table = extract_figures(facts_file(facts), CUTOFF)
    assert "operating_income" not in table.lines
    assert any(
        o["line"] == "operating_income" and o["year_end"] == JAN26.isoformat()
        for o in table.omitted
    )


def test_a_line_with_no_tag_present_at_all_is_listed_not_invented() -> None:
    table = extract_figures(facts_file({"Revenues": _revenue_history()}), CUTOFF)
    assert "dividends_paid" not in table.lines
    assert any(o["line"] == "dividends_paid" for o in table.omitted)


def test_balances_are_taken_at_the_fiscal_year_ends_by_their_end_date() -> None:
    facts = {
        "Revenues": _revenue_history(),
        "LongTermDebt": [balance(2026, 300, "2026-03-02"), balance(2025, 350, "2025-03-03")],
        "CashAndCashEquivalentsAtCarryingValue": [balance(2026, 40, "2026-03-02")],
    }
    table = extract_figures(facts_file(facts), CUTOFF)
    assert {e: f.value for e, f in table.lines["long_term_debt"].by_year.items()} == {
        JAN26: 300,
        JAN25: 350,
    }
    assert table.lines["cash"].section == 4
    assert table.lines["long_term_debt"].by_year[JAN26].start is None


def test_a_balance_at_a_quarter_end_is_not_a_year_end_figure() -> None:
    quarter_end = balance(2026, 55, "2026-05-08")
    quarter_end["end"] = "2026-04-30"
    facts = {"Revenues": _revenue_history(), "LongTermDebt": [quarter_end]}
    table = extract_figures(facts_file(facts), CUTOFF)
    assert "long_term_debt" not in table.lines


def test_a_balance_row_given_a_start_is_not_read_as_a_balance() -> None:
    facts = {"Revenues": _revenue_history(), "LongTermDebt": [annual(2026, 300, "2026-03-02")]}
    assert "long_term_debt" not in extract_figures(facts_file(facts), CUTOFF).lines


def test_two_same_day_filings_that_disagree_leave_the_year_out_listed() -> None:
    history = [*_revenue_history(), annual(2026, 1001, "2026-03-02", "other")]
    table = extract_figures(facts_file({"Revenues": history}), CUTOFF)
    assert JAN26 not in table.lines["revenue"].by_year
    assert any("disagree" in str(o["reason"]) for o in table.omitted)


def test_two_same_day_filings_that_agree_are_fine() -> None:
    history = [*_revenue_history(), annual(2026, 1000, "2026-03-02", "dup")]
    assert (
        extract_figures(facts_file({"Revenues": history}), CUTOFF)
        .lines["revenue"]
        .by_year[JAN26]
        .value
        == 1000
    )


def test_a_stray_annual_length_period_off_the_fiscal_calendar_is_skipped_in_the_chain() -> None:
    stray = annual(2026, 1, "2026-03-02", "stray", start="2024-08-01", end="2025-07-31")
    table = extract_figures(facts_file({"Revenues": [*_revenue_history(), stray]}), CUTOFF)
    assert table.year_ends == (JAN26, JAN25, JAN24)


def test_only_us_gaap_usd_figures_are_read() -> None:
    other_taxonomy = facts_file({"Revenues": _revenue_history()}, taxonomy="ifrs-full")
    assert extract_figures(other_taxonomy, CUTOFF).year_ends == ()
    shares = facts_file({"Revenues": _revenue_history()})
    shares["facts"]["us-gaap"]["Revenues"]["units"] = {"shares": _revenue_history()}
    assert extract_figures(shares, CUTOFF).lines == {}


def test_a_file_with_no_admitted_annual_figure_gives_an_empty_table_with_a_reason() -> None:
    table = extract_figures(facts_file({"Revenues": [annual(2026, 1, "2026-07-01")]}), CUTOFF)
    assert table.lines == {}
    assert table.omitted[0]["reason"] == "no admitted annual figure at all"


def test_a_malformed_filed_date_in_a_read_tag_is_an_error() -> None:
    bad = annual(2026, 1000, "2026-03-02")
    bad["filed"] = "March 2"
    with pytest.raises(CutoffError):
        extract_figures(facts_file({"Revenues": [bad]}), CUTOFF)


def test_a_file_without_a_facts_block_is_an_error() -> None:
    with pytest.raises(FiguresError):
        extract_figures({"cik": 1}, CUTOFF)


def test_the_record_lists_tag_value_filing_and_omissions() -> None:
    record = extract_figures(facts_file({"Revenues": _revenue_history()}), CUTOFF).record()
    assert record["year_ends"] == ["2026-01-31", "2025-01-31", "2024-01-31"]
    year = record["lines"]["revenue"]["years"]["2026-01-31"]
    assert year == {"value": 1000, "filed": "2026-03-02", "accession": "r26", "form": "10-K"}
    assert record["lines"]["revenue"]["tag"] == "Revenues"
    assert isinstance(record["omitted"], list)
