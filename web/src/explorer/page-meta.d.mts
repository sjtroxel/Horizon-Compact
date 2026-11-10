export type Route =
  | { kind: "story" }
  | { kind: "scenario"; id: string }
  | { kind: "cases" }
  | { kind: "case"; label: string }
  | { kind: "studies" }
  | { kind: "memos" }
  | { kind: "not_found" };

/** A route that has a page of its own. */
export type PageRoute = Exclude<Route, { kind: "not_found" }>;

export interface PageWords {
  title: string;
  description: string;
}

export type Pages = Record<PageRoute["kind"], PageWords>;

export const SITE_ORIGIN: string;
export function pathOf(route: Route): string;
export function pageMeta(route: Route, pages: Pages): PageWords;
export function allRoutes(scenarioIds: readonly string[], caseLabels: readonly string[]): PageRoute[];
