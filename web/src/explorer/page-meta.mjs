// The one place that says what path a route has and what its title and description are. Plain ES module with a
// .d.mts beside it, so the explorer's route code (bundled by Vite) and the build's write-paths script (plain Node)
// read the same rule and cannot drift apart.

export const SITE_ORIGIN = "https://horizon-compact.vercel.app";

/** The share cards' size in pixels (Phase 6 IMPLEMENTATION doc section 10): the one place it is written. */
export const CARD_WIDTH = 1200;
export const CARD_HEIGHT = 630;

/** A path segment that is safe to make a folder or a file name from: ids come from data, and a file is written for each. */
export const SAFE_SEGMENT = /^[a-z0-9][a-z0-9-]*$/;

/** The path of a route, with its trailing slash. `not_found` has none: no page is written for it. */
export function pathOf(route) {
  switch (route.kind) {
    case "story":
      return "/";
    case "scenario":
      return `/scenario/${route.id}/`;
    case "cases":
      return "/cases/";
    case "case":
      return `/cases/${route.label}/`;
    case "studies":
      return "/studies/";
    case "memos":
      return "/memos/";
    default:
      throw new Error(`pathOf: no path for a ${route.kind} route`);
  }
}

/** The route a path belongs to, the inverse of `pathOf`; null for a path no page is written for. */
export function routeOfPath(path) {
  const segments = path.split("/").filter(Boolean);
  const [first, second, third] = segments;
  if (path !== `/${segments.join("/")}${segments.length > 0 ? "/" : ""}`) return null;
  if (first === undefined) return { kind: "story" };
  if (first === "scenario" && second !== undefined && third === undefined)
    return { kind: "scenario", id: second };
  if (first === "cases" && second === undefined) return { kind: "cases" };
  if (first === "cases" && third === undefined) return { kind: "case", label: second };
  if (first === "studies" && second === undefined) return { kind: "studies" };
  if (first === "memos" && second === undefined) return { kind: "memos" };
  return null;
}

/** The name of a route's share card, without its extension: the file is `cards/<slug>.png`. */
export function cardSlug(route) {
  switch (route.kind) {
    case "story":
      return "story";
    case "scenario":
      return `scenario-${route.id}`;
    case "cases":
      return "cases";
    case "case":
      return `case-${route.label}`;
    case "studies":
      return "studies";
    case "memos":
      return "memos";
    default:
      throw new Error(`cardSlug: no card for a ${route.kind} route`);
  }
}

/** Title and description of a route, from his words. A scenario's or a case's own id follows the title. */
export function pageMeta(route, pages) {
  const page = pages[route.kind];
  if (!page) throw new Error(`pageMeta: no words for a ${route.kind} route`);
  const suffix =
    route.kind === "scenario" ? ` (${route.id})` : route.kind === "case" ? ` (${route.label})` : "";
  return { title: `${page.title}${suffix}`, description: page.description };
}

/** Every route that gets a page, in the order the paths are written. */
export function allRoutes(scenarioIds, caseLabels) {
  return [
    { kind: "story" },
    ...scenarioIds.map((id) => ({ kind: "scenario", id })),
    { kind: "cases" },
    ...caseLabels.map((label) => ({ kind: "case", label })),
    { kind: "studies" },
    { kind: "memos" },
  ];
}
