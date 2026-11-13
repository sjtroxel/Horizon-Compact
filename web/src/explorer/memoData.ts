/**
 * Which memos the reader's query string asks for, and whether the memo extract holds them (Phase 6 IMPLEMENTATION
 * doc section 8, C5 B3). Pure functions: they look at the index's file list and the data's lists of goals and
 * scenarios and decide; they never read a memo.
 */
import { memoPathCell } from "./data";
import type { MemoIndex } from "./data";
import { MEMO_KINDS } from "./route";
import type { MemoKind, MemoQuery } from "./route";

export interface Cell {
  kind: string;
  model: string;
  scenario: string;
  objective: string;
}

/** The cells the memo index lists, once each, in its order. A file whose path is of another shape is ignored. */
export function memoCells(index: Pick<MemoIndex, "files">): Cell[] {
  const seen = new Set<string>();
  const cells: Cell[] = [];
  for (const path of index.files) {
    const cell = memoPathCell(path);
    if (cell === null) continue;
    const key = `${cell.kind}/${cell.model}/${cell.scenario}/${cell.objective}`;
    if (seen.has(key)) continue;
    seen.add(key);
    cells.push(cell);
  }
  return cells;
}

/** Why a query cannot be shown. */
export type Refusal = "kind" | "scenario" | "objective" | "thinking_model" | "cell";

export type Resolved =
  | { ok: true; kind: MemoKind; scenario: string; objective: string; run: string | null }
  | { ok: false; why: Refusal };

const isKind = (value: string): value is MemoKind => (MEMO_KINDS as readonly string[]).includes(value);

/**
 * The reader's choice from its query. With nothing chosen: the grid, the first scenario, the first goal (s1 and A in
 * the data) and the first run, which the view picks from the cell's file. A parameter the data does not have is a
 * refusal that names it; so is a thinking choice on a model the sub-study did not run on, and a cell the index
 * does not list. A `run` is passed through: whether it is in the cell is for the view, which has the rows.
 */
export function resolveMemoQuery(
  query: MemoQuery,
  model: string,
  scenarioIds: readonly string[],
  goalIds: readonly string[],
  cells: readonly Cell[],
): Resolved {
  const kind = query.kind ?? "grid";
  if (!isKind(kind)) return { ok: false, why: "kind" };
  const ofKind = cells.filter((cell) => cell.kind === kind && cell.model === model);
  if (kind === "thinking" && ofKind.length === 0) return { ok: false, why: "thinking_model" };
  const scenario = query.scenario ?? (kind === "grid" ? scenarioIds[0] : ofKind[0]?.scenario);
  if (scenario === undefined || !scenarioIds.includes(scenario)) return { ok: false, why: "scenario" };
  const objective = query.objective ?? goalIds[0];
  if (objective === undefined || !goalIds.includes(objective)) return { ok: false, why: "objective" };
  const listed = ofKind.some((cell) => cell.scenario === scenario && cell.objective === objective);
  if (!listed) return { ok: false, why: "cell" };
  return { ok: true, kind, scenario, objective, run: query.run };
}

/**
 * A cell's runs grouped by wording, for the reader's list of runs: one group a wording in the order each first appears,
 * the runs of a group in the file's order. It regroups and counts nothing.
 */
export function groupRunsByWording<T extends { wording_id: string }>(
  rows: readonly T[],
): Array<{ wording: string; runs: T[] }> {
  const groups: Array<{ wording: string; runs: T[] }> = [];
  for (const row of rows) {
    const group = groups.find((g) => g.wording === row.wording_id);
    if (group === undefined) groups.push({ wording: row.wording_id, runs: [row] });
    else group.runs.push(row);
  }
  return groups;
}

/** The scenarios the index lists for a kind and model, in its order. */
export function scenariosOf(cells: readonly Cell[], kind: string, model: string): string[] {
  const found: string[] = [];
  for (const cell of cells) {
    if (cell.kind === kind && cell.model === model && !found.includes(cell.scenario))
      found.push(cell.scenario);
  }
  return found;
}
