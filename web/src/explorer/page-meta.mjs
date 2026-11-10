// The one place that says what path a route has and what its title and description are. Plain ES module with a
// .d.mts beside it, so the explorer's route code (bundled by Vite) and the build's write-paths script (plain Node)
// read the same rule and cannot drift apart.

export const SITE_ORIGIN = "https://horizon-compact.vercel.app";

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
