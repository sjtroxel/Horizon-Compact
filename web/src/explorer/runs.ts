import type { DataIndex, RunSpan } from "./data";

/**
 * The run dates a results surface states, read from the index's `runs` block and from nowhere else (Phase 7 step 2).
 * These return the data's own values, untouched: no date is typed in the page's code, and none is worked out here.
 * `undefined` means the data holds no run of that kind for that model, and the surface then states nothing, so a
 * missing date can never be filled by a guess.
 */

export type RunKind = "grid" | "thinking" | "awareness";

/** The dates of a model's official grid, its thinking sub-study or its awareness probe. */
export function runSpan(index: DataIndex, kind: RunKind, model: string): RunSpan | undefined {
  return index.runs[kind][model];
}

/** The dates of a model's runs on one real case (session start dates; see `RunSpan`). */
export function caseRunSpan(index: DataIndex, label: string, model: string): RunSpan | undefined {
  return index.runs.cases[label]?.[model];
}

/**
 * The date a model was retired, or `null` while the data says it is still served (every model, in v1). A model the
 * data does not list is also `null`: the retirement line appears only when the data names a date.
 */
export function retiredOn(index: DataIndex, model: string): string | null {
  return index.runs.retired_on[model] ?? null;
}
