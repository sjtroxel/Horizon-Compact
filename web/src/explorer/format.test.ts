import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  attemptedRuns,
  axisExtent,
  axisPercent,
  axisSpan,
  comparisonRuns,
  confidenceLevel,
  dotY,
  edgeAnchor,
  formatCount,
  formatDifference,
  formatDistance,
  formatLongDate,
  formatPercent,
  formatPoints,
  formatRunDates,
  formatUtc,
  formatWholePercent,
  jitter,
  sessionSpan,
  statusCounts,
  unitBox,
  unitSlot,
  wholePointsDown,
  withoutWithheldPrefix,
  wordingRuns,
  wordsSide,
} from "./format";
import { realCaseFiles, realGrids, realIndex, WEB_ROOT } from "./fixtures";

/** Every comparison the real files carry, with where it came from. */
const everyComparison = [
  ...realGrids.flatMap(({ label, file }) =>
    file.comparisons.map((c) => ({ where: `${label} ${c.first}-${c.second}`, c })),
  ),
  ...realIndex.verdicts.flatMap((v) =>
    v.comparisons.map((c) => ({ where: `index ${v.model_key} ${v.scenario_id} ${c.first}-${c.second}`, c })),
  ),
];

/**
 * The oracle for "whole points, rounded down": read the points off the value's decimal digits, 10 places, with no
 * floating-point multiplication. 0.29999999999999993 prints as 0.3000000000, which is 30.
 */
function pointsFromDigits(difference: number): number {
  const [whole, fraction] = Math.abs(difference).toFixed(10).split(".");
  return Number(whole) * 100 + Number(fraction!.slice(0, 2));
}

describe("display formats", () => {
  it("shows a coded lever share as a whole percentage, and a reason without the file's own leading 'withheld: ' (step 11 pages, items 9 and 11)", () => {
    expect([0, 0.5, 0.624, 1].map(formatWholePercent)).toEqual(["0%", "50%", "62%", "100%"]);
    expect(withoutWithheldPrefix("withheld: because")).toBe("because");
    expect(withoutWithheldPrefix("because")).toBe("because");
    expect(withoutWithheldPrefix("Withheld: because")).toBe("Withheld: because");
  });

  it("shows a share as a percentage to one decimal place, and an axis label to none", () => {
    expect(formatPercent(0.624)).toBe("62.4%");
    expect(formatPercent(1 / 125)).toBe("0.8%");
    expect(formatPercent(0.5, 0)).toBe("50%");
    expect(formatPercent(0)).toBe("0.0%");
  });

  it("shows a difference or an interval end in points, signed, with a real minus sign", () => {
    expect(formatPoints(-0.398)).toBe("−39.8");
    expect(formatPoints(0.1)).toBe("+10.0");
    expect(formatPoints(-0.5, 0)).toBe("−50");
    expect(formatPoints(0)).toBe("0.0");
    expect(formatPoints(-0.0000001)).toBe("0.0"); // never "-0.0"
  });

  it("reads each end of a difference and its interval from the field", () => {
    expect(formatDifference(-0.02, -0.0718, 0.0318)).toBe("−2.0 points, interval −7.2 to +3.2");
    expect(formatDifference(null, null, null)).toBeNull();
  });

  it("shows alpha as the interval's confidence level", () => {
    expect(confidenceLevel(0.003125)).toBe("99.7%");
    expect(confidenceLevel(0.05)).toBe("95.0%");
    for (const model of realIndex.models) expect(confidenceLevel(model.alpha)).toBe("99.7%");
  });

  it("rounds the lead's points down after correcting float noise", () => {
    // The case named in the build prompt: 0.29999999999999993 is 30 points in the data and must not read 29.
    expect(wholePointsDown(0.29999999999999993)).toBe(30);
    expect(wholePointsDown(-0.29999999999999993)).toBe(30);
    expect(wholePointsDown(0.399)).toBe(39);
    expect(wholePointsDown(0.3999)).toBe(39);
    expect(wholePointsDown(0)).toBe(0);
  });

  it("matches the digits of every real difference, in every file", () => {
    let checked = 0;
    for (const { where, c } of everyComparison) {
      for (const value of [c.difference, c.low, c.high]) {
        if (value === null) continue;
        expect(wholePointsDown(value), `${where} ${value}`).toBe(pointsFromDigits(value));
        checked += 1;
      }
    }
    expect(checked).toBeGreaterThan(100);
  });

  it("matches the digits of every real against-the-thesis difference", () => {
    for (const entry of realIndex.against_thesis.entries) {
      expect(wholePointsDown(entry.difference!)).toBe(pointsFromDigits(entry.difference!));
    }
  });
});

describe("integer sums of run counts", () => {
  it("sum valid_runs to the per-wording counts, for every comparison in every real grid and thinking file", () => {
    let comparisons = 0;
    for (const { label, file } of realGrids) {
      for (const c of file.comparisons) {
        const runs = comparisonRuns(c);
        const first = c.per_wording.reduce((a, w) => a + w.n_first, 0);
        const second = c.per_wording.reduce((a, w) => a + w.n_second, 0);
        expect(runs, `${label} ${c.first}-${c.second}`).toEqual({ first, second });
        comparisons += 1;
      }
    }
    expect(comparisons).toBe(9 * 5); // eight grid files and the thinking file, five comparisons each
  });

  it("counts a comparison that is not assessable as 0 and 0, which a caller must not show as runs compared", () => {
    const file = realGrids.find((g) => g.label === "grid gpt-oss-openrouter s2")!.file;
    const c = file.comparisons.find((x) => x.final_verdict === "not_assessable")!;
    expect(c.valid_runs).toEqual([]);
    expect(comparisonRuns(c)).toEqual({ first: 0, second: 0 });
  });

  it("add up a scenario's attempted runs from objective_rates, and agree with the cells", () => {
    for (const { label, file } of realGrids) {
      const fromCells = file.cells.reduce((a, cell) => a + cell.attempted, 0);
      expect(attemptedRuns(file.objective_rates), label).toBe(fromCells);
    }
    const gpt = realGrids.find((g) => g.label === "grid gpt-oss-openrouter s1")!.file;
    expect(attemptedRuns(gpt.objective_rates)).toBe(300);
    expect(gpt.descriptive.runs).toBe(292);
  });
});

describe("pixel positions", () => {
  it("map a value to a percentage of the axis", () => {
    expect(axisPercent(0.5, 0, 1)).toBe("50%");
    expect(axisPercent(0, -1, 1)).toBe("50%");
    expect(axisPercent(-1, -1, 1)).toBe("0%");
    expect(axisSpan(-0.1, 0.1, -1, 1)).toBe("10%");
  });

  it("end an axis at the floor, or at the highest value when that is higher", () => {
    expect(axisExtent([])).toBe(1);
    expect(axisExtent([0.2, 0.9])).toBe(1);
    expect(axisExtent([0.2, 14.5, 3])).toBe(14.5);
    expect(axisExtent([], 2)).toBe(2);
  });

  it("jitter is the same for the same run id, within its amplitude, and differs between runs", () => {
    expect(jitter("r-025287a73180", 18)).toBe(jitter("r-025287a73180", 18));
    const ids = realGrids[0]!.file.descriptive.per_run.map((r) => r.run_id);
    const values = ids.map((id) => jitter(id, 18));
    for (const v of values) {
      expect(v).toBeGreaterThanOrEqual(-9);
      expect(v).toBeLessThanOrEqual(9);
    }
    expect(new Set(values).size).toBeGreaterThan(ids.length * 0.9);
    expect(dotY(40, "r-025287a73180", 18)).toBe(20 + jitter("r-025287a73180", 18));
  });

  it("place unit-chart dots ten to a row, and keep one row for an empty group", () => {
    expect(unitSlot(0, 10, 12)).toEqual({ x: 6, y: 6 });
    expect(unitSlot(9, 10, 12)).toEqual({ x: 114, y: 6 });
    expect(unitSlot(10, 10, 12)).toEqual({ x: 6, y: 18 });
    expect(unitBox(0, 10, 12)).toEqual({ width: 120, height: 12 });
    expect(unitBox(10, 10, 12)).toEqual({ width: 120, height: 12 });
    expect(unitBox(11, 10, 12)).toEqual({ width: 120, height: 24 });
  });
});

describe("the rule: no number is computed outside format.ts", () => {
  const files = [
    "charts.tsx",
    "ScenarioView.tsx",
    "AgainstThesis.tsx",
    "sentences.ts",
    "chartData.ts",
    "parts.tsx",
    "models.ts",
    // C5: the memo reader, the real cases, the studies and what they read.
    "MemoReader.tsx",
    "Cases.tsx",
    "Studies.tsx",
    "distanceChart.tsx",
    "caseData.ts",
    "memoData.ts",
    "views.tsx",
    "route.ts",
    "links.ts",
    // C6: the story and the boundary around the lazy views.
    "Story.tsx",
    "ViewBoundary.tsx",
    // Step 11 (the redesign batch): the shell, the switch and every figure's frame.
    "Shell.tsx",
    "ModelSwitch.tsx",
    "ChartCard.tsx",
    "RunDetails.tsx",
    "caseParts.tsx",
    // C7: the share cards and the build scripts that draw them (their pixel positions are rule 3's, no data value).
    "cards.ts",
    "../../scripts/write-cards.mjs",
    "../../scripts/card-render.mjs",
    "../../scripts/load-ts.mjs",
  ];
  it("holds no Math call, no reduce and no running total in the views, the charts or the templates", () => {
    for (const file of files) {
      const source = readFileSync(resolve(WEB_ROOT, "src/explorer", file), "utf8")
        .split("\n")
        .filter((line) => !/^\s*(\/\/|\*|\/\*)/.test(line))
        .join("\n");
      expect(source, file).not.toMatch(/\bMath\./);
      expect(source, file).not.toMatch(/\.reduce\(/);
      expect(source, file).not.toMatch(/[^=!<>]\+=|\+\+/);
    }
  });
});

describe("formatDistance (C5)", () => {
  it("writes a distance as the file has it to three places, and an axis tick to one", () => {
    expect(formatDistance(0.5456778377115402)).toBe("0.546");
    expect(formatDistance(1)).toBe("1.000");
    expect(formatDistance(0.5, 1)).toBe("0.5");
    expect(formatDistance(0)).toBe("0.000");
  });

  it("is pinned to the source field for every distance, interval end and gap in the real case files", () => {
    let checked = 0;
    for (const { file } of realCaseFiles) {
      for (const reading of file.readings) {
        for (const d of reading.distances) {
          for (const value of [d.distance, d.low, d.high]) {
            expect(formatDistance(value)).toBe(value.toFixed(3));
            expect(Number(formatDistance(value))).toBeCloseTo(value, 3);
            checked++;
          }
        }
      }
    }
    expect(checked).toBe(10 * 2 * 5 * 3);
  });
});

describe("the redesign's pixel-position helpers and run sums (step 11)", () => {
  it("puts an interval's words on the side of the axis with more room, ties to the right, and the choice is pure position", () => {
    expect(wordsSide(-0.2, 0.1, -1, 1)).toBe("right"); // 0.9 of room on the right, 0.8 on the left
    expect(wordsSide(-0.1, 0.2, -1, 1)).toBe("left"); // 0.8 on the right, 0.9 on the left
    expect(wordsSide(-0.5, 0.5, -1, 1)).toBe("right"); // a tie goes right
    expect(wordsSide(0.4, 0.9, -1, 1)).toBe("left");
    expect(wordsSide(-0.9, -0.4, -1, 1)).toBe("right");
  });

  it("anchors text at an axis point so it stays on the plot: from its start near the low end, to its end near the high end", () => {
    expect(edgeAnchor(-0.95, -1, 1)).toBe("start");
    expect(edgeAnchor(0, -1, 1)).toBe("middle");
    expect(edgeAnchor(0.95, -1, 1)).toBe("end");
    expect(edgeAnchor(1, -1, 1)).toBe("end");
    expect(edgeAnchor(-1, -1, 1)).toBe("start");
  });

  it("sums one wording's valid and attempted runs across the goals, as integers of the file's own cells", () => {
    const grid = realGrids.find((g) => g.label === "grid haiku-5-5 s1")!.file;
    const w2 = wordingRuns(grid, "w2");
    let valid = 0;
    let attempted = 0;
    for (const cell of grid.cells) {
      if (cell.wording_id === "w2") {
        valid += cell.valid;
        attempted += cell.attempted;
      }
    }
    expect(w2.attempted).toBe(attempted);
    expect(w2.valid).toBe(valid); // every valid run is a descriptive run in this file
    expect(w2.attempted).toBeLessThan(attemptedRuns(grid.objective_rates)); // one wording of three
    expect(wordingRuns(grid, "nope")).toEqual({ valid: 0, attempted: 0 });
  });
});

describe("the methods page's counts and dates (Phase 6.5 step 4)", () => {
  it("sums every real scenario's cells into the attempted, valid and refused runs and the failures by type", () => {
    for (const { label, file } of realGrids) {
      const counts = statusCounts(file.cells);
      expect(counts.attempted, label).toBe(attemptedRuns(file.objective_rates));
      let valid = 0;
      for (const cell of file.cells) valid += cell.valid;
      expect(counts.valid, label).toBe(valid);
      // Every attempt is valid, refused or failed: the sums close without a total of failures being derived.
      let failed = 0;
      for (const [, runs] of counts.failed) failed += runs;
      expect(counts.valid + counts.refused + failed, label).toBe(counts.attempted);
    }
  });

  it("merges a failure type across cells, sorted by type, and leaves a cell with none out", () => {
    const counts = statusCounts([
      {
        attempted: 5,
        valid: 3,
        refused: 0,
        failed_by_type: [
          ["truncated", 1],
          ["schema_invalid", 1],
        ],
      },
      { attempted: 5, valid: 4, refused: 0, failed_by_type: [["truncated", 1]] },
      { attempted: 5, valid: 5, refused: 0, failed_by_type: [] },
    ]);
    expect(counts).toEqual({
      attempted: 15,
      valid: 12,
      refused: 0,
      failed: [
        ["schema_invalid", 1],
        ["truncated", 2],
      ],
    });
  });

  it("writes a whole count with commas between thousands, and nothing else", () => {
    expect(formatCount(0)).toBe("0");
    expect(formatCount(999)).toBe("999");
    expect(formatCount(1000)).toBe("1,000");
    expect(formatCount(1322)).toBe("1,322");
    expect(formatCount(104785272)).toBe("104,785,272");
  });

  it("writes a UTC moment to the minute, and returns any other offset as written", () => {
    expect(formatUtc("2026-10-14T09:52:25.086417+00:00")).toBe("2026-10-14 09:52");
    expect(formatUtc("2026-10-14T23:18:07+00:00")).toBe("2026-10-14 23:18");
    expect(formatUtc("2026-10-14T23:18:07Z")).toBe("2026-10-14 23:18");
    expect(formatUtc("2026-10-14T09:52:25+02:00")).toBe("2026-10-14T09:52:25+02:00");
    expect(formatUtc("not a moment")).toBe("not a moment");
  });

  it("picks the earliest start and the latest finish, and none for no sessions", () => {
    expect(sessionSpan([])).toBeNull();
    const a = {
      started_at: "2026-10-14T09:52:27.211690+00:00",
      finished_at: "2026-10-14T15:11:46.304286+00:00",
    };
    const b = {
      started_at: "2026-10-14T15:47:45.658799+00:00",
      finished_at: "2026-10-14T23:18:07.721747+00:00",
    };
    expect(sessionSpan([a, b])).toEqual({ first: a.started_at, last: b.finished_at });
    expect(sessionSpan([b, a])).toEqual({ first: a.started_at, last: b.finished_at });
    expect(sessionSpan([a])).toEqual({ first: a.started_at, last: a.finished_at });
  });
});

describe("the run dates in words (Phase 7 step 2)", () => {
  it("writes a calendar date as the month's name, the day and the year", () => {
    expect(formatLongDate("2026-10-14")).toBe("October 14, 2026");
    expect(formatLongDate("2027-01-02")).toBe("January 2, 2027");
    expect(formatLongDate("2026-12-31")).toBe("December 31, 2026");
  });

  it("knows the leap day, and the days a month does not have", () => {
    expect(formatLongDate("2028-02-29")).toBe("February 29, 2028");
    expect(formatLongDate("2000-02-29")).toBe("February 29, 2000");
    for (const bad of ["2027-02-29", "2100-02-29", "2026-04-31", "2026-13-01", "2026-00-10", "2026-10-00"]) {
      expect(formatLongDate(bad)).toBe(bad); // as written, never repaired
    }
  });

  it("returns anything that is not YYYY-MM-DD as written", () => {
    for (const odd of ["", "October 14", "2026-10-14T09:52:25+00:00", "26-10-14", "2026-1-4"]) {
      expect(formatLongDate(odd)).toBe(odd);
    }
  });

  it("writes one day as a date, and two days of one year with the year said once", () => {
    expect(formatRunDates("2026-10-14", "2026-10-14")).toBe("October 14, 2026");
    expect(formatRunDates("2026-10-29", "2026-10-30")).toBe("October 29 to October 30, 2026");
    expect(formatRunDates("2026-10-29", "2026-11-02")).toBe("October 29 to November 2, 2026");
  });

  it("writes two days in different years each in full, and an impossible date as written", () => {
    expect(formatRunDates("2026-12-31", "2027-01-01")).toBe("December 31, 2026 to January 1, 2027");
    expect(formatRunDates("2026-10-29", "2026-10-99")).toBe("October 29, 2026 to 2026-10-99");
    expect(formatRunDates("2026-10-99", "2026-10-99")).toBe("2026-10-99");
  });

  it("never reads the clock or a time zone: the same text for any date, whatever the machine says", () => {
    const real = Date;
    const was = process.env.TZ;
    try {
      process.env.TZ = "Pacific/Kiritimati"; // UTC+14, where a UTC date would slip a day
      expect(formatLongDate("2026-10-14")).toBe("October 14, 2026");
      process.env.TZ = "Pacific/Pago_Pago"; // UTC-11
      expect(formatLongDate("2026-10-14")).toBe("October 14, 2026");
    } finally {
      if (was === undefined) delete process.env.TZ;
      else process.env.TZ = was;
      expect(Date).toBe(real);
    }
  });
});
