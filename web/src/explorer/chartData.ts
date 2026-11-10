/**
 * Lookups over a grid file for the scenario view: which runs belong to a goal, the goal's count in the chart, the
 * choices in their order, the levers in their canonical order. They group and find; they compute nothing (Phase 6
 * IMPLEMENTATION doc section 5). Every count comes from a field of the file.
 */
import type { ChoiceSplit, DescriptiveCell, GridComparison, GridFile, LineSummary, PerRun } from "./data";

/** The valid runs of one goal, in the file's order; of one wording only when `wording` is given. */
export function runsOfGoal(file: GridFile, goal: string, wording?: string): PerRun[] {
  return file.descriptive.per_run.filter(
    (run) => run.objective_id === goal && (wording === undefined || run.wording_id === wording),
  );
}

/** A goal over every wording kept: the descriptive cell with no wording and no choice. With `wording`, the cell of
 * that wording alone (and no choice). */
export function goalCell(file: GridFile, goal: string, wording?: string): DescriptiveCell | undefined {
  return file.descriptive.cells.find(
    (cell) => cell.objective_id === goal && cell.wording_id === (wording ?? null) && cell.choice === null,
  );
}

/** The number of runs of a goal the chart shows: `descriptive.cells[]` (the wording, or none; no choice) `.runs`. */
export function goalRunCount(file: GridFile, goal: string, wording?: string): number {
  return goalCell(file, goal, wording)?.runs ?? 0;
}

/** A goal's choice split over every wording kept (a choice scenario only). */
export function goalSplit(file: GridFile, goal: string): ChoiceSplit | undefined {
  return file.descriptive.choice_splits.find(
    (split) => split.objective_id === goal && split.wording_id === null,
  );
}

/** The choices of a choice scenario, in the order of the first all-wordings split's `counts`. */
export function choiceOrder(file: GridFile): string[] {
  const split = file.descriptive.choice_splits.find((s) => s.wording_id === null);
  return split === undefined ? [] : split.counts.map(([choice]) => choice);
}

/** A goal's lever summaries in canonical order: the `lines` of its all-wordings cell. */
export function goalLines(file: GridFile, goal: string): LineSummary[] {
  return goalCell(file, goal)?.lines ?? [];
}

/** One run's share on one lever, or undefined when the run's `shares` has no such lever. */
export function leverShare(run: PerRun, lever: string): number | undefined {
  return run.shares.find(([key]) => key === lever)?.[1];
}

/** The comparison of a pair, first then second, if the file has it. */
export function findComparison(
  file: Pick<GridFile, "comparisons">,
  first: string,
  second: string,
): GridComparison | undefined {
  return file.comparisons.find((c) => c.first === first && c.second === second);
}

/**
 * The comparisons in the order the sentence column shows them: C vs D first, as the lead, then A vs C, B vs D,
 * A vs B, then A vs D, the secondary one.
 */
export const SENTENCE_ORDER: ReadonlyArray<readonly [string, string]> = [
  ["C", "D"],
  ["A", "C"],
  ["B", "D"],
  ["A", "B"],
  ["A", "D"],
];

export function orderedComparisons(file: Pick<GridFile, "comparisons">): GridComparison[] {
  const found: GridComparison[] = [];
  for (const [first, second] of SENTENCE_ORDER) {
    const comparison = findComparison(file, first, second);
    if (comparison !== undefined) found.push(comparison);
  }
  return found;
}

/** The CSS class that carries a goal's color (`--o-a` to `--o-e`). */
export function goalClass(goal: string): string {
  return `goal-${goal.toLowerCase()}`;
}
