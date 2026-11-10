import { describe, expect, it } from "vitest";
import { createDataApi, dataPath } from "./data";
import type { DataIndex } from "./data";
import { fileFetcher, readData, realApi, realIndex } from "./fixtures";

/** A small index of the same shape, with payloads that say which file they came from. */
const FIXTURE_FILES = {
  grid: { m1: { s1: "grid/m1/s1.json" } },
  thinking: { m1: { s1: "thinking/m1/s1.json" } },
  cases: "cases/index.json",
  case_results: { c1: { m1: "cases/c1/m1.json" } },
};

function fixtureFetcher(files: unknown, requested: string[]) {
  const payloads: Record<string, unknown> = {
    "/data/index.json": { models: [], files },
    "/data/grid/m1/s1.json": { from: "grid", nested: { list: [1, 2, { a: null }], n: 0.30000000000000004 } },
    "/data/thinking/m1/s1.json": { from: "thinking" },
    "/data/cases/index.json": { from: "cases index" },
    "/data/cases/c1/m1.json": { from: "case" },
  };
  return async (path: string) => {
    requested.push(path);
    const body = payloads[path];
    if (body === undefined) return { ok: false, status: 404 } as Response;
    return { ok: true, status: 200, json: async () => structuredClone(body) } as Response;
  };
}

describe("the loaders", () => {
  it("build every path from the index's files block, under /data/", async () => {
    const requested: string[] = [];
    const api = createDataApi(fixtureFetcher(FIXTURE_FILES, requested));
    await api.loadGrid("m1", "s1");
    await api.loadThinking();
    await api.loadCasesIndex();
    await api.loadCase("c1", "m1");
    expect(requested).toEqual([
      "/data/index.json",
      "/data/grid/m1/s1.json",
      "/data/thinking/m1/s1.json",
      "/data/cases/index.json",
      "/data/cases/c1/m1.json",
    ]);
  });

  it("fetch the index once, however many files are loaded", async () => {
    const requested: string[] = [];
    const api = createDataApi(fixtureFetcher(FIXTURE_FILES, requested));
    await Promise.all([api.loadIndex(), api.loadGrid("m1", "s1"), api.loadCasesIndex()]);
    expect(requested.filter((p) => p === "/data/index.json")).toHaveLength(1);
  });

  it("keep each file in memory by its path, so switching back does not fetch it again", async () => {
    const requested: string[] = [];
    const api = createDataApi(fixtureFetcher(FIXTURE_FILES, requested));
    const first = await api.loadGrid("m1", "s1");
    await api.loadThinking();
    expect(await api.loadGrid("m1", "s1")).toBe(first); // the same object, not a second fetch
    await api.loadThinking();
    await api.loadCase("c1", "m1");
    await api.loadCase("c1", "m1");
    expect(requested.filter((p) => p === "/data/grid/m1/s1.json")).toHaveLength(1);
    expect(requested.filter((p) => p === "/data/thinking/m1/s1.json")).toHaveLength(1);
    expect(requested.filter((p) => p === "/data/cases/c1/m1.json")).toHaveLength(1);
  });

  it("forgets a failed fetch, so the next ask tries again", async () => {
    let calls = 0;
    const api = createDataApi(async (path) => {
      calls += 1;
      if (calls === 1) return { ok: false, status: 503 } as Response;
      return { ok: true, status: 200, json: async () => ({ path }) } as Response;
    });
    await expect(api.loadIndex()).rejects.toThrow(/503/);
    expect(await api.loadIndex()).toEqual({ path: "/data/index.json" });
    expect(calls).toBe(2);
  });

  it("change nothing between the parsed JSON and the returned object", async () => {
    const api = createDataApi(fixtureFetcher(FIXTURE_FILES, []));
    expect(await api.loadGrid("m1", "s1")).toEqual({
      from: "grid",
      nested: { list: [1, 2, { a: null }], n: 0.30000000000000004 },
    });
    expect(await api.loadCase("c1", "m1")).toEqual({ from: "case" });
    expect(await api.loadThinking()).toEqual([{ from: "thinking" }]);
  });

  it("return the real files exactly as committed", async () => {
    const api = realApi();
    expect(await api.loadIndex()).toEqual(realIndex);
    expect(await api.loadGrid("haiku-5-5", "s1")).toEqual(readData("grid/haiku-5-5/s1.json"));
    expect(await api.loadCase("pre-25", "haiku-5-5")).toEqual(readData("cases/pre-25/haiku-5-5.json"));
    expect(await api.loadCasesIndex()).toEqual(readData("cases/index.json"));
    const thinking = await api.loadThinking();
    expect(thinking).toEqual([readData("thinking/haiku-5-5/s1.json")]);
  });

  it("read every file the real index lists, and only those", async () => {
    const requested: string[] = [];
    const api = realApi(requested);
    const index: DataIndex = await api.loadIndex();
    for (const [model, byScenario] of Object.entries(index.files.grid)) {
      for (const scenario of Object.keys(byScenario)) await api.loadGrid(model, scenario);
    }
    for (const [label, byModel] of Object.entries(index.files.case_results)) {
      for (const model of Object.keys(byModel)) await api.loadCase(label, model);
    }
    expect(requested.every((p) => p.startsWith("/data/"))).toBe(true);
    expect(new Set(requested).size).toBe(1 + 8 + 10); // the index, 2 models x 4 scenarios, 5 cases x 2 models
  });

  it("refuse a path outside /data/", async () => {
    for (const bad of [
      "../secret.json",
      "grid/../../secret.json",
      "/etc/passwd",
      "https://example.com/x.json",
      "//example.com/x.json",
      "grid\\m1.json",
      "grid//s1.json",
      "",
    ]) {
      const requested: string[] = [];
      const files = { ...FIXTURE_FILES, grid: { m1: { s1: bad } } };
      const api = createDataApi(fixtureFetcher(files, requested));
      await expect(api.loadGrid("m1", "s1"), bad).rejects.toThrow(/refusing the path/);
      expect(requested, bad).toEqual(["/data/index.json"]);
    }
  });

  it("say so when the index lists no such file, or the server fails", async () => {
    const api = createDataApi(fixtureFetcher(FIXTURE_FILES, []));
    await expect(api.loadGrid("nope", "s1")).rejects.toThrow(/lists no file/);
    await expect(api.loadCase("c1", "nope")).rejects.toThrow(/lists no file/);
    const missing = createDataApi(fileFetcher());
    await expect(missing.loadGrid("haiku-5-5", "s9")).rejects.toThrow(/lists no file/);
    const down = createDataApi(async () => ({ ok: false, status: 503 }) as Response);
    await expect(down.loadIndex()).rejects.toThrow(/503/);
  });
});

describe("dataPath", () => {
  it("puts a relative path under /data/", () => {
    expect(dataPath("grid/haiku-5-5/s1.json")).toBe("/data/grid/haiku-5-5/s1.json");
  });
});
