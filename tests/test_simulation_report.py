"""The committed simulation evidence (Phase 3 doc 14.4, step 10): the summary and the matcher's calibration
are exactly what the report makes from the committed results, and the matcher's thresholds file holds the
values the results set."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from horizon_compact.analysis.matcher import THRESHOLDS_FILE, load_thresholds
from horizon_compact.simulation import report
from horizon_compact.simulation.report import table, wilson

EVIDENCE = Path(__file__).resolve().parents[1] / "docs" / "phases" / "evidence" / "phase-3"


def committed() -> dict[str, Any]:
    return json.loads((EVIDENCE / report.RESULTS_NAME).read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_the_committed_results_are_a_full_run() -> None:
    doc = committed()
    assert doc["mode"] == "full"
    assert len(doc["code_sha256"]) == 64
    assert doc["constants"]["alpha"] == 0.05 / 16


def test_the_committed_summary_is_what_the_report_makes_of_the_committed_results() -> None:
    text = (EVIDENCE / report.SUMMARY_NAME).read_text(encoding="utf-8")
    assert text == report.summary(committed())


def test_the_committed_matcher_calibration_is_what_the_report_makes() -> None:
    text = (EVIDENCE / report.MATCHER_NAME).read_text(encoding="utf-8")
    assert text == report.matcher_calibration(committed())


def test_the_thresholds_file_is_what_the_report_writes_from_the_results() -> None:
    assert THRESHOLDS_FILE.read_text(encoding="utf-8") == report.thresholds_toml(committed())


def test_the_matchers_thresholds_are_the_ones_the_results_set() -> None:
    matcher = committed()["matcher"]
    thresholds = load_thresholds(THRESHOLDS_FILE)
    assert set(thresholds) == set(matcher)
    for shape, t in thresholds.items():
        assert t.d_star == matcher[shape]["d_star"], shape
        expected_k = matcher[shape]["k_star"]
        if (
            expected_k is None
        ):  # no k reached 80%: one more than the dimensions, so nothing is matched
            dims = max(
                int(k) for k in matcher[shape]["identification_by_dimensions_at_design_spread"]
            )
            assert t.k_star == dims + 1, shape
        else:
            assert t.k_star == expected_k, shape


# --- the report's helpers -----------------------------------------------------------------------------------


def test_wilson_by_hand() -> None:
    # 1 of 10 at 95%: the textbook interval is (0.0179, 0.4042).
    lo, hi = wilson(1, 10)
    assert lo == pytest.approx(0.01788, abs=1e-4)
    assert hi == pytest.approx(0.40415, abs=1e-4)
    assert wilson(0, 0) == (0.0, 1.0)
    assert wilson(0, 100)[0] == pytest.approx(0.0, abs=1e-15)


def test_a_pipe_in_a_cell_is_escaped() -> None:
    lines = table(["a|b"], [["`x|y`"]])
    assert lines[0] == "| a\\|b |"
    assert lines[2] == "| `x\\|y` |"
