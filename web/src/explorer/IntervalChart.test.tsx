import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { orderedComparisons } from "./chartData";
import { IntervalChart, rowOfComparison } from "./charts";
import type { IntervalRow } from "./charts";
import { explorerLabels as L } from "./copy";
import { realGrids } from "./fixtures";
import { axisPercent, formatDifference, formatPoints, wordsSide } from "./format";

afterEach(cleanup);

const names = L.objectiveNames;
const AXIS = { low: -1, high: 1 };
const rowsOf = (label: string) =>
  orderedComparisons(realGrids.find((g) => g.label === label)!.file).map(rowOfComparison);

function draw(rows: readonly IntervalRow[]) {
  return render(<IntervalChart rows={rows} names={names} label={L.intervalChartLabel} />);
}

describe("the interval chart's labels on the marks (step 11)", () => {
  it("writes each verdict word in the plot, beside its interval, on the side of the axis with more room, and not in a column apart", () => {
    // Every real model and scenario: 5 comparisons each, a mix of every verdict and some rows with no interval.
    let drawn = 0;
    for (const { label } of realGrids.filter((g) => g.label.startsWith("grid "))) {
      const rows = rowsOf(label);
      const { container, unmount } = draw(rows);
      const chartRows = container.querySelectorAll(".interval-row:not(.interval-axis)");
      expect(chartRows, label).toHaveLength(rows.length);
      rows.forEach((row, i) => {
        const element = chartRows[i]!;
        const word = element.querySelector<SVGTextElement>("svg text.verdict-word")!;
        expect(word.textContent, `${label} ${row.first}-${row.second}`).toBe(L.verdictWords[row.verdict]);
        // No separate verdict column: the word is inside the plot's svg, which is the row's second cell.
        expect(element.querySelector(".interval-verdict")).toBeNull();
        expect(element.children).toHaveLength(2);
        if (row.difference === null || row.low === null || row.high === null) {
          expect(element.querySelector("line.interval")).toBeNull();
          expect(element.querySelector(".interval-none")!.textContent).toBe(L.intervalRowNotAssessable);
          expect(element.querySelector("text.diff-value")).toBeNull();
          return;
        }
        const right = wordsSide(row.low, row.high, AXIS.low, AXIS.high) === "right";
        // It starts a gap past the interval's high end, or ends a gap before its low end.
        expect(word.getAttribute("x")).toBe(axisPercent(right ? row.high : row.low, AXIS.low, AXIS.high));
        expect(word.getAttribute("text-anchor")).toBe(right ? "start" : "end");
        expect(Number(word.getAttribute("dx")) > 0).toBe(right);
        // It sits level with the interval's line, in the same svg.
        const line = element.querySelector("line.interval")!;
        expect(word.closest("svg")).toBe(line.closest("svg"));
        drawn += 1;
      });
      unmount();
    }
    expect(drawn).toBeGreaterThan(20);
  });

  it("writes the difference at its dot, with formatPoints of the field and nothing computed", () => {
    for (const label of ["grid haiku-5-5 s1", "grid gpt-oss-openrouter s2", "grid haiku-5-5 s3"]) {
      const rows = rowsOf(label);
      const { container, unmount } = draw(rows);
      rows.forEach((row, i) => {
        const element = container.querySelectorAll(".interval-row:not(.interval-axis)")[i]!;
        const value = element.querySelector("text.diff-value");
        if (row.difference === null) {
          expect(value).toBeNull();
          return;
        }
        expect(value!.textContent).toBe(formatPoints(row.difference));
        expect(value!.getAttribute("x")).toBe(axisPercent(row.difference, AXIS.low, AXIS.high));
        expect(element.querySelector("circle.diff")!.getAttribute("cx")).toBe(value!.getAttribute("x"));
      });
      unmount();
    }
  });

  it("labels each row's plot for a screen reader with the pair, the verdict and the numbers (the words in it are drawn text)", () => {
    const rows = rowsOf("grid gpt-oss-openrouter s2"); // has a not-assessable row
    const { container } = draw(rows);
    const plots = [...container.querySelectorAll<SVGElement>(".interval-row:not(.interval-axis) svg")];
    rows.forEach((row, i) => {
      const numbers = formatDifference(row.difference, row.low, row.high);
      const expected = `${row.first} vs ${row.second}: ${L.verdictWords[row.verdict]}${numbers === null ? "" : `, ${numbers}`}`;
      expect(plots[i]!.getAttribute("role")).toBe("img");
      expect(plots[i]!.getAttribute("aria-label")).toBe(expected);
    });
    expect(rows.some((r) => r.verdict === "not_assessable")).toBe(true);
  });

  it("carries no explanation of its own: the unit line is the figure's, and the key is in the 'about these results' section", () => {
    const { container } = draw(rowsOf("grid haiku-5-5 s1"));
    expect(container.querySelector(".axis-caption")).toBeNull();
    expect(container.textContent).not.toContain(L.intervalAxis);
    expect(container.querySelector(".chart-key")).toBeNull();
  });
});
