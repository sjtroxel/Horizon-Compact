import { describe, expect, it } from "vitest";
import {
  choiceOrder,
  findComparison,
  goalCell,
  goalClass,
  goalLines,
  goalRunCount,
  goalSplit,
  leverShare,
  orderedComparisons,
  runsOfGoal,
  SENTENCE_ORDER,
} from "./chartData";
import { axisExtent } from "./format";
import { realGrids, realIndex } from "./fixtures";

const goals = realIndex.objectives.map((o) => o.id);

describe("what the chart draws is what the file counts", () => {
  it("has as many runs for each goal as the goal's descriptive cell says, in every real file", () => {
    for (const { label, file } of realGrids) {
      for (const goal of goals) {
        expect(runsOfGoal(file, goal).length, `${label} ${goal}`).toBe(goalRunCount(file, goal));
      }
      const total = goals.reduce((n, goal) => n + goalRunCount(file, goal), 0);
      expect(total, label).toBe(file.descriptive.runs);
      expect(file.descriptive.per_run.length, label).toBe(file.descriptive.runs);
    }
  });

  it("counts gpt-oss-120b's s1 B at 56 dots while A vs B counts its own kept wordings", () => {
    const file = realGrids.find((g) => g.label === "grid gpt-oss-openrouter s1")!.file;
    expect(goalRunCount(file, "B")).toBe(56);
    expect(runsOfGoal(file, "B")).toHaveLength(56);
    const ab = findComparison(file, "A", "B")!;
    expect(ab.dropped_wordings.map((w) => w.wording_id)).toEqual(["w2"]);
    expect(ab.valid_runs).toEqual([
      ["w1", 20, 19],
      ["w3", 20, 20],
    ]);
  });

  it("groups each choice scenario's runs by choice exactly as its split counts them", () => {
    let groups = 0;
    for (const { label, file } of realGrids.filter((g) => g.file.kind === "choice_rate")) {
      const order = choiceOrder(file);
      expect(order.length, label).toBeGreaterThanOrEqual(2);
      for (const goal of goals) {
        const split = goalSplit(file, goal)!;
        expect(
          split.counts.map(([c]) => c),
          `${label} ${goal}`,
        ).toEqual(order);
        expect(split.runs, `${label} ${goal}`).toBe(goalRunCount(file, goal));
        for (const [choice, n] of split.counts) {
          const made = runsOfGoal(file, goal).filter((r) => r.choice === choice);
          expect(made.length, `${label} ${goal} ${choice}`).toBe(n);
          groups += 1;
        }
      }
    }
    expect(groups).toBeGreaterThan(40);
  });

  it("has no split on a share scenario, and a choice on every run of a choice scenario", () => {
    for (const { label, file } of realGrids) {
      if (file.kind === "share") {
        expect(file.descriptive.choice_splits, label).toEqual([]);
        expect(
          file.descriptive.per_run.every((r) => r.choice === null),
          label,
        ).toBe(true);
      } else {
        expect(
          file.descriptive.per_run.every((r) => r.choice !== null),
          label,
        ).toBe(true);
      }
    }
  });

  it("keeps every drawn value on its axis: outcomes 0 to 1, lever shares to their lever's scale, differences and intervals -1 to 1", () => {
    for (const { label, file } of realGrids) {
      for (const run of file.descriptive.per_run) {
        expect(run.primary, label).toBeGreaterThanOrEqual(0);
        expect(run.primary, label).toBeLessThanOrEqual(1);
      }
      // A lever's share can pass 1 on s4 (the share of the year's money), so its scale is the data's own highest
      // value for that lever over every goal, as the allocation panels draw it.
      for (const run of file.descriptive.per_run) {
        for (const [lever, share] of run.shares) {
          const top = axisExtent(
            goals.flatMap((goal) =>
              goalLines(file, goal)
                .filter((line) => line.key === lever)
                .map((line) => line.summary.maximum),
            ),
          );
          expect(share, `${label} ${lever}`).toBeGreaterThanOrEqual(0);
          expect(share, `${label} ${lever}`).toBeLessThanOrEqual(top);
        }
      }
      for (const c of file.comparisons) {
        for (const v of [c.difference, c.low, c.high]) {
          if (v === null) continue;
          expect(v, `${label} ${c.first}-${c.second}`).toBeGreaterThanOrEqual(-1);
          expect(v, `${label} ${c.first}-${c.second}`).toBeLessThanOrEqual(1);
        }
      }
    }
    for (const entry of realIndex.against_thesis.entries) {
      for (const v of [entry.difference!, entry.low!, entry.high!])
        expect(Math.abs(v)).toBeLessThanOrEqual(1);
    }
  });

  it("finds a lever's share in each run, for every lever of the goal's cell", () => {
    for (const { label, file } of realGrids) {
      for (const goal of goals) {
        const lines = goalLines(file, goal);
        for (const run of runsOfGoal(file, goal)) {
          for (const line of lines)
            expect(leverShare(run, line.key), `${label} ${goal} ${line.key}`).toBeDefined();
        }
      }
    }
  });

  it("lists the levers of a goal in one order across goals", () => {
    for (const { label, file } of realGrids) {
      const orders = goals.map((goal) =>
        goalLines(file, goal)
          .map((l) => l.key)
          .join(","),
      );
      expect(new Set(orders).size, label).toBe(1);
    }
  });
});

describe("the order of the sentences", () => {
  it("is C vs D, A vs C, B vs D, A vs B, then the secondary A vs D", () => {
    expect(SENTENCE_ORDER).toEqual([
      ["C", "D"],
      ["A", "C"],
      ["B", "D"],
      ["A", "B"],
      ["A", "D"],
    ]);
    for (const { label, file } of realGrids) {
      const ordered = orderedComparisons(file);
      expect(
        ordered.map((c) => `${c.first}${c.second}`),
        label,
      ).toEqual(["CD", "AC", "BD", "AB", "AD"]);
      expect(
        ordered.map((c) => c.role),
        label,
      ).toEqual(["primary", "primary", "primary", "primary", "secondary"]);
    }
  });

  it("gives a goal the class that carries its color, and finds a goal's cell", () => {
    expect(goalClass("A")).toBe("goal-a");
    expect(goalClass("E")).toBe("goal-e");
    const file = realGrids[0]!.file;
    expect(goalCell(file, "A")?.wording_id).toBeNull();
    expect(goalCell(file, "Z")).toBeUndefined();
    expect(goalRunCount(file, "Z")).toBe(0);
  });
});

describe("a wording's runs and counts (C5, the studies view)", () => {
  const grid = realGrids.find((g) => g.label === "grid haiku-5-5 s1")!.file;
  const sealed = realIndex.models.find((m) => m.model_key === "haiku-5-5")!.sealed_wording;

  it("takes a goal's count from the descriptive cell of that wording, and the rows from per_run", () => {
    for (const goal of realIndex.objectives.map((o) => o.id)) {
      const cell = grid.descriptive.cells.find(
        (c) => c.objective_id === goal && c.wording_id === sealed && c.choice === null,
      )!;
      expect(goalRunCount(grid, goal, sealed), goal).toBe(cell.runs);
      expect(goalCell(grid, goal, sealed)).toBe(cell);
      const rows = runsOfGoal(grid, goal, sealed);
      expect(rows.every((r) => r.wording_id === sealed && r.objective_id === goal)).toBe(true);
      expect(rows.length, goal).toBe(cell.runs); // the data agrees with its own count; the view uses the field
    }
  });

  it("leaves a call with no wording as it was: every wording kept", () => {
    expect(goalRunCount(grid, "A")).toBe(goalCell(grid, "A")!.runs);
    expect(runsOfGoal(grid, "A").length).toBeGreaterThan(runsOfGoal(grid, "A", sealed).length);
    expect(goalCell(grid, "A")!.wording_id).toBeNull();
    expect(goalRunCount(grid, "A", "w9")).toBe(0);
  });
});
