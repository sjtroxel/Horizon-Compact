import { describe, expect, it } from "vitest";
import { allRoutes } from "./page-meta.mjs";
import { DEFAULT_MODEL, modelFromSearch, parseRoute, pathOf, searchWithModel, withModel } from "./route";
import { realCasesIndex, realIndex } from "./fixtures";

const known = {
  scenarioIds: realIndex.scenarios.map((s) => s.scenario_id),
  caseLabels: realCasesIndex.cases.map((c) => c.label),
};
const modelKeys = realIndex.models.map((m) => m.model_key);

describe("parseRoute", () => {
  const routes = allRoutes(known.scenarioIds, known.caseLabels);

  it("has a page for the story, every scenario, the cases, each case, the studies and the memos", () => {
    expect(routes).toHaveLength(1 + known.scenarioIds.length + 1 + known.caseLabels.length + 1 + 1);
    expect(known.scenarioIds).toEqual(["s1", "s2", "s3", "s4"]);
  });

  it("parses every path to its route, with and without the trailing slash", () => {
    for (const route of routes) {
      const path = pathOf(route);
      expect(parseRoute(path, known), path).toEqual(route);
      if (path !== "/") expect(parseRoute(path.slice(0, -1), known), path.slice(0, -1)).toEqual(route);
    }
  });

  it("reads the paths the plan names", () => {
    expect(parseRoute("/", known)).toEqual({ kind: "story" });
    expect(parseRoute("/scenario/s3/", known)).toEqual({ kind: "scenario", id: "s3" });
    expect(parseRoute("/cases/", known)).toEqual({ kind: "cases" });
    expect(parseRoute("/studies/", known)).toEqual({ kind: "studies" });
    expect(parseRoute("/memos/", known)).toEqual({ kind: "memos" });
  });

  it("gives not_found for an unknown scenario id, case label or top path", () => {
    const missing = { kind: "not_found" };
    expect(parseRoute("/scenario/s9/", known)).toEqual(missing);
    expect(parseRoute("/scenario/", known)).toEqual(missing);
    expect(parseRoute("/cases/not-a-case/", known)).toEqual(missing);
    expect(parseRoute("/nowhere/", known)).toEqual(missing);
    expect(parseRoute("/scenario/s1/extra/", known)).toEqual(missing);
    expect(parseRoute("/studies/extra/", known)).toEqual(missing);
    expect(parseRoute("/memos/extra", known)).toEqual(missing);
    expect(parseRoute("/Scenario/S1/", known)).toEqual(missing);
    expect(parseRoute("/scenario/%E0%A4%A/", known)).toEqual(missing); // a malformed percent escape
  });

  it("checks only the shape of a path while the data has not loaded", () => {
    expect(parseRoute("/scenario/anything/")).toEqual({ kind: "scenario", id: "anything" });
    expect(parseRoute("/nowhere/")).toEqual({ kind: "not_found" });
  });
});

describe("the model in the query string", () => {
  it("reads the model the query names", () => {
    for (const key of modelKeys) expect(modelFromSearch(`?model=${key}`, modelKeys)).toBe(key);
  });

  it("falls back to Haiku 5.5 when the model is absent or not one the data has", () => {
    expect(DEFAULT_MODEL).toBe("haiku-5-5");
    expect(modelFromSearch("", modelKeys)).toBe("haiku-5-5");
    expect(modelFromSearch("?model=", modelKeys)).toBe("haiku-5-5");
    expect(modelFromSearch("?model=nonsense", modelKeys)).toBe("haiku-5-5");
    expect(modelFromSearch("?model=both", modelKeys)).toBe("haiku-5-5");
    expect(modelFromSearch("?other=1", modelKeys)).toBe("haiku-5-5");
  });

  it("writes the model into a query string, keeps other parameters, and leaves the default out", () => {
    expect(searchWithModel("", "gpt-oss-openrouter")).toBe("?model=gpt-oss-openrouter");
    expect(searchWithModel("?scenario=s1", "gpt-oss-openrouter")).toBe(
      "?scenario=s1&model=gpt-oss-openrouter",
    );
    expect(searchWithModel("?model=gpt-oss-openrouter&scenario=s1", "haiku-5-5")).toBe("?scenario=s1");
    expect(searchWithModel("?model=gpt-oss-openrouter", "haiku-5-5")).toBe("");
  });

  it("carries the model on a link", () => {
    expect(withModel("/cases/", "gpt-oss-openrouter")).toBe("/cases/?model=gpt-oss-openrouter");
    expect(withModel("/cases/", "haiku-5-5")).toBe("/cases/");
  });
});
