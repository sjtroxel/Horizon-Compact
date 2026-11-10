import { pathOf } from "./page-meta.mjs";
import type { Route } from "./page-meta.mjs";

export type { Route } from "./page-meta.mjs";
export { pathOf } from "./page-meta.mjs";

/** The model shown when the URL names none, or names one the data does not have (Phase 6 doc, decision 7). */
export const DEFAULT_MODEL = "haiku-5-5";

/** What the loaded data says exists. A path naming anything else is not found. */
export interface Known {
  scenarioIds: readonly string[];
  caseLabels: readonly string[];
}

const NOT_FOUND: Route = { kind: "not_found" };

/**
 * Parses a pathname into a route. With `known`, a scenario id or case label the data does not have is not found;
 * without it, only the path's shape is checked. A trailing slash is optional.
 */
export function parseRoute(pathname: string, known?: Known): Route {
  let segments: string[];
  try {
    segments = pathname
      .split("/")
      .filter((s) => s !== "")
      .map(decodeURIComponent);
  } catch {
    return NOT_FOUND; // a malformed percent escape
  }
  const [first, second, ...rest] = segments;
  if (first === undefined) return { kind: "story" };
  if (rest.length > 0) return NOT_FOUND;
  switch (first) {
    case "scenario":
      if (second === undefined) return NOT_FOUND;
      return !known || known.scenarioIds.includes(second) ? { kind: "scenario", id: second } : NOT_FOUND;
    case "cases":
      if (second === undefined) return { kind: "cases" };
      return !known || known.caseLabels.includes(second) ? { kind: "case", label: second } : NOT_FOUND;
    case "studies":
      return second === undefined ? { kind: "studies" } : NOT_FOUND;
    case "memos":
      return second === undefined ? { kind: "memos" } : NOT_FOUND;
    default:
      return NOT_FOUND;
  }
}

/** The model the query string names, or the default when it is absent or not one of `modelKeys`. */
export function modelFromSearch(search: string, modelKeys: readonly string[]): string {
  const asked = new URLSearchParams(search).get("model");
  if (asked !== null && modelKeys.includes(asked)) return asked;
  return modelKeys.includes(DEFAULT_MODEL) ? DEFAULT_MODEL : (modelKeys[0] ?? DEFAULT_MODEL);
}

/** The query string with `?model=` set to `model` (dropped for the default, so the plain URL stays plain). Other
 * parameters stay as they were. Returns "" or a string starting with "?". */
export function searchWithModel(search: string, model: string): string {
  const params = new URLSearchParams(search);
  if (model === DEFAULT_MODEL) params.delete("model");
  else params.set("model", model);
  const text = params.toString();
  return text === "" ? "" : `?${text}`;
}

/** A path with the current model carried in its query string, for a link. */
export function withModel(path: string, model: string): string {
  return `${path}${searchWithModel("", model)}`;
}

/** The path (and query) of a route, for a link. */
export function hrefOf(route: Route, model: string): string {
  return withModel(pathOf(route), model);
}

/** The two sets of memos the reader holds: the main grid's, and the thinking sub-study's. */
export const MEMO_KINDS = ["grid", "thinking"] as const;
export type MemoKind = (typeof MEMO_KINDS)[number];

/** What the memo reader's query string asks for, each parameter as the URL has it (null when absent). The model is
 * the explorer's one `?model=`, read by `modelFromSearch`. */
export interface MemoQuery {
  kind: string | null;
  scenario: string | null;
  objective: string | null;
  run: string | null;
}

export function readMemoQuery(search: string): MemoQuery {
  const params = new URLSearchParams(search);
  return {
    kind: params.get("kind"),
    scenario: params.get("scenario"),
    objective: params.get("objective"),
    run: params.get("run"),
  };
}

/**
 * The query string after the model switch on the page at `pathname`. Every parameter is kept except the memo
 * reader's `run`: a run id belongs to one model's set, so it is dropped, and the reader opens the same set's first
 * run for the new model (Opus review of C5, section 27a).
 */
export function searchAfterModelSwitch(pathname: string, search: string, model: string): string {
  const params = new URLSearchParams(search);
  if (pathname === pathOf({ kind: "memos" })) params.delete("run");
  return searchWithModel(params.toString(), model);
}

/** A choice of memos: a set, a scenario and a goal, and one run in it when there is one. */
export interface MemoSelection {
  kind: string;
  scenario: string;
  objective: string;
  run?: string | null;
}

/**
 * The address of a memo (or of a set of them) in the reader. It keeps every parameter: the kind, the scenario, the
 * goal, the run when there is one, and the model (dropped for the default, like every link).
 */
export function memoHref(selection: MemoSelection, model: string): string {
  const params = new URLSearchParams();
  params.set("kind", selection.kind);
  params.set("scenario", selection.scenario);
  params.set("objective", selection.objective);
  if (selection.run !== undefined && selection.run !== null) params.set("run", selection.run);
  if (model !== DEFAULT_MODEL) params.set("model", model);
  return `${pathOf({ kind: "memos" })}?${params.toString()}`;
}
