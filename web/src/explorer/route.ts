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
