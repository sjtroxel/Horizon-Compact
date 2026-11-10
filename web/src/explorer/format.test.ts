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
  formatDifference,
  formatPercent,
  formatPoints,
  jitter,
  unitBox,
  unitSlot,
  wholePointsDown,
} from "./format";
import { realGrids, realIndex, WEB_ROOT } from "./fixtures";

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
