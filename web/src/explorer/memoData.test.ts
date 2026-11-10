import { describe, expect, it } from "vitest";
import { createDataApi, dataPath, memoPathCell } from "./data";
import type { MemoRow } from "./data";
import { fileFetcher, readAwareness, readMemoRows, realApi, realIndex, realMemoIndex } from "./fixtures";
import { memoCells, resolveMemoQuery, scenariosOf } from "./memoData";
import type { Cell } from "./memoData";
import type { MemoQuery } from "./route";

const SCENARIOS = realIndex.scenarios.map((s) => s.scenario_id);
const GOALS = realIndex.objectives.map((o) => o.id);
const cells = memoCells(realMemoIndex);
const none: MemoQuery = { kind: null, scenario: null, objective: null, run: null };

describe("the cells of the memo index", () => {
  it("are read from the index's own list: every grid cell of both models, and the sub-study on Haiku 5.5 only", () => {
    expect(cells.length).toBeGreaterThan(0);
    for (const model of realIndex.models.map((m) => m.model_key)) {
      for (const scenario of SCENARIOS) {
        for (const objective of GOALS) {
          expect(
            cells.some(
              (c) =>
                c.kind === "grid" &&
                c.model === model &&
                c.scenario === scenario &&
                c.objective === objective,
            ),
            `${model} ${scenario} ${objective}`,
          ).toBe(true);
        }
      }
    }
    const thinking = cells.filter((c) => c.kind === "thinking");
    expect(new Set(thinking.map((c) => c.model))).toEqual(new Set(["haiku-5-5"]));
    expect(new Set(thinking.map((c) => c.scenario))).toEqual(new Set(["s1"]));
  });

  it("count a cell split by wording once, and ignore a path of any other shape", () => {
    const found = memoCells({
      files: [
        "grid/m/s1/A-w1.jsonl",
        "grid/m/s1/A-w2.jsonl",
        "grid/m/s1/B.jsonl",
        "grid/m/s1/index.json",
        "notes.jsonl",
        "grid/m/s1/a.jsonl",
        "grid/m/s1/extra/B.jsonl",
      ],
    });
    expect(found).toEqual([
      { kind: "grid", model: "m", scenario: "s1", objective: "A" },
      { kind: "grid", model: "m", scenario: "s1", objective: "B" },
    ]);
    expect(memoPathCell("grid/m/s1/A-w1.jsonl")).toEqual({
      kind: "grid",
      model: "m",
      scenario: "s1",
      objective: "A",
    });
    expect(memoPathCell("grid/m/s1/A.json")).toBeNull();
  });

  it("list a kind's scenarios in the index's order", () => {
    expect(scenariosOf(cells, "grid", "haiku-5-5")).toEqual(SCENARIOS);
    expect(scenariosOf(cells, "thinking", "haiku-5-5")).toEqual(["s1"]);
    expect(scenariosOf(cells, "thinking", "gpt-oss-openrouter")).toEqual([]);
  });
});

describe("what a query asks for", () => {
  const resolve = (query: Partial<MemoQuery>, model = "haiku-5-5", from: readonly Cell[] = cells) =>
    resolveMemoQuery({ ...none, ...query }, model, SCENARIOS, GOALS, from);

  it("with nothing chosen is the grid, the first scenario and the first goal: s1 and A", () => {
    expect(resolve({})).toEqual({ ok: true, kind: "grid", scenario: "s1", objective: "A", run: null });
    expect(resolve({}, "gpt-oss-openrouter")).toMatchObject({
      ok: true,
      kind: "grid",
      scenario: "s1",
      objective: "A",
    });
  });

  it("passes the thinking kind and a run through", () => {
    expect(resolve({ kind: "thinking", run: "r-x" })).toEqual({
      ok: true,
      kind: "thinking",
      scenario: "s1",
      objective: "A",
      run: "r-x",
    });
  });

  it("refuses an unknown kind, scenario or goal, naming which", () => {
    expect(resolve({ kind: "other" })).toEqual({ ok: false, why: "kind" });
    expect(resolve({ scenario: "s9" })).toEqual({ ok: false, why: "scenario" });
    expect(resolve({ objective: "Z" })).toEqual({ ok: false, why: "objective" });
    expect(resolve({ objective: "a" })).toEqual({ ok: false, why: "objective" });
  });

  it("refuses the thinking kind on a model the sub-study did not run on, before anything else", () => {
    expect(resolve({ kind: "thinking" }, "gpt-oss-openrouter")).toEqual({ ok: false, why: "thinking_model" });
    expect(resolve({ kind: "thinking", scenario: "s9" }, "gpt-oss-openrouter")).toEqual({
      ok: false,
      why: "thinking_model",
    });
  });

  it("refuses a cell the index does not list, as in the sub-study on a scenario it did not run", () => {
    expect(resolve({ kind: "thinking", scenario: "s2" })).toEqual({ ok: false, why: "cell" });
  });
});

describe("the memo loaders", () => {
  it("read the cell's file from the index's list and return its rows in the file's order, equal to the file's", async () => {
    const requested: string[] = [];
    const api = realApi(requested);
    const cell = await api.loadMemos("grid", "haiku-5-5", "s1", "A");
    expect(cell.found).toBe(true);
    if (!cell.found) return;
    expect(cell.paths).toEqual(["grid/haiku-5-5/s1/A.jsonl"]);
    expect(cell.rows).toEqual(readMemoRows("grid/haiku-5-5/s1/A.jsonl"));
    expect(requested).toEqual(["/data/memos/index.json", "/data/memos/grid/haiku-5-5/s1/A.jsonl"]);
  });

  it("return a not-found result, not an exception, for a cell the index does not list, and fetch no memo file", async () => {
    const requested: string[] = [];
    const api = realApi(requested);
    expect(await api.loadMemos("thinking", "gpt-oss-openrouter", "s1", "A")).toEqual({ found: false });
    expect(await api.loadMemos("grid", "haiku-5-5", "s9", "A")).toEqual({ found: false });
    expect(requested).toEqual(["/data/memos/index.json"]);
  });

  it("fetch every file of a cell split by wording, in the index's order, and join their rows", async () => {
    const row = (id: string, wording: string): MemoRow => ({
      run_id: id,
      wording_id: wording,
      repeat: 0,
      status: "valid",
      source: "memo",
      memo: id,
      final: { key: "k", sha256: "s" },
      attempt: { key: "k", sha256: "s" },
    });
    const lines = (rows: MemoRow[]) => rows.map((r) => JSON.stringify(r)).join("\n") + "\n\n";
    const bodies: Record<string, string> = {
      "/data/memos/grid/m/s1/A-w1.jsonl": lines([row("r-1", "w1"), row("r-2", "w1")]),
      "/data/memos/grid/m/s1/A-w2.jsonl": lines([row("r-3", "w2")]),
    };
    const requested: string[] = [];
    const api = createDataApi(async (path) => {
      requested.push(path);
      if (path === "/data/memos/index.json") {
        const body = { files: ["grid/m/s1/A-w1.jsonl", "grid/m/s1/A-w2.jsonl", "grid/m/s1/B.jsonl"] };
        return { ok: true, status: 200, json: async () => body } as Response;
      }
      const text = bodies[path];
      return text === undefined
        ? ({ ok: false, status: 404 } as Response)
        : ({ ok: true, status: 200, text: async () => text } as Response);
    });
    const cell = await api.loadMemos("grid", "m", "s1", "A");
    expect(cell).toMatchObject({ found: true, paths: ["grid/m/s1/A-w1.jsonl", "grid/m/s1/A-w2.jsonl"] });
    if (cell.found) expect(cell.rows.map((r) => r.run_id)).toEqual(["r-1", "r-2", "r-3"]);
    expect(requested).toEqual([
      "/data/memos/index.json",
      "/data/memos/grid/m/s1/A-w1.jsonl",
      "/data/memos/grid/m/s1/A-w2.jsonl",
    ]);
  });

  it("keep a memo file by its path, so a second ask does not fetch it, and forget a failed fetch", async () => {
    const requested: string[] = [];
    const api = realApi(requested);
    await api.loadMemos("grid", "haiku-5-5", "s1", "B");
    await api.loadMemos("grid", "haiku-5-5", "s1", "B");
    expect(requested.filter((p) => p.endsWith("B.jsonl"))).toHaveLength(1);

    let failing = true;
    const base = fileFetcher();
    const flaky = createDataApi(async (path) =>
      path.endsWith("C.jsonl") && failing ? ({ ok: false, status: 500 } as Response) : base(path),
    );
    await expect(flaky.loadMemos("grid", "haiku-5-5", "s1", "C")).rejects.toThrow(/500/);
    failing = false;
    await expect(flaky.loadMemos("grid", "haiku-5-5", "s1", "C")).resolves.toMatchObject({ found: true });
  });

  it("load the memo index once and an awareness file from the index's files block", async () => {
    const requested: string[] = [];
    const api = realApi(requested);
    await Promise.all([api.loadMemoIndex(), api.loadMemos("grid", "haiku-5-5", "s2", "A")]);
    expect(requested.filter((p) => p === "/data/memos/index.json")).toHaveLength(1);
    const awareness = await api.loadAwareness("haiku-5-5");
    expect(awareness).toEqual(readAwareness("haiku-5-5"));
    expect(requested).toContain("/data/awareness/haiku-5-5.json");
    await expect(api.loadAwareness("nobody")).rejects.toThrow(/lists no file/);
  });

  it("refuse a path that climbs out of /data/", () => {
    expect(() => dataPath("memos/../../index.json")).toThrow(/refusing/);
  });
});
