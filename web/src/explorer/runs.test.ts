import { describe, expect, it } from "vitest";
import type { DataIndex } from "./data";
import { realIndex } from "./fixtures";
import { caseRunSpan, retiredOn, runSpan } from "./runs";

const MODELS = realIndex.models.map((m) => m.model_key);
const CASES = Object.keys(realIndex.runs.cases);

describe("the run dates are the index's own values", () => {
  it("returns, for every model, exactly what the index holds for a grid, a probe and a case", () => {
    expect(MODELS.length).toBe(2);
    for (const model of MODELS) {
      expect(runSpan(realIndex, "grid", model)).toBe(realIndex.runs.grid[model]);
      expect(runSpan(realIndex, "awareness", model)).toBe(realIndex.runs.awareness[model]);
      expect(runSpan(realIndex, "grid", model)).toBeDefined();
      expect(runSpan(realIndex, "awareness", model)).toBeDefined();
      for (const label of CASES) {
        expect(caseRunSpan(realIndex, label, model)).toBe(realIndex.runs.cases[label]?.[model]);
        expect(caseRunSpan(realIndex, label, model)).toBeDefined();
      }
    }
    expect(CASES.length).toBe(5);
  });

  it("has the thinking sub-study for one model only, and says nothing for the other", () => {
    expect(runSpan(realIndex, "thinking", "haiku-5-5")).toBe(realIndex.runs.thinking["haiku-5-5"]);
    expect(runSpan(realIndex, "thinking", "haiku-5-5")).toBeDefined();
    expect(runSpan(realIndex, "thinking", "gpt-oss-openrouter")).toBeUndefined();
  });

  it("returns undefined for a model, a case or a kind the data does not hold, never a guess", () => {
    expect(runSpan(realIndex, "grid", "no-such-model")).toBeUndefined();
    expect(caseRunSpan(realIndex, "no-such-case", "haiku-5-5")).toBeUndefined();
    expect(caseRunSpan(realIndex, CASES[0] ?? "", "no-such-model")).toBeUndefined();
  });

  it("holds only YYYY-MM-DD dates, from not after to, each with a known basis", () => {
    const spans = [
      ...Object.values(realIndex.runs.grid),
      ...Object.values(realIndex.runs.thinking),
      ...Object.values(realIndex.runs.awareness),
      ...Object.values(realIndex.runs.cases).flatMap((byModel) => Object.values(byModel)),
    ];
    expect(spans.length).toBe(2 + 1 + 2 + 10);
    for (const span of spans) {
      expect(span.from).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(span.to).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(span.from <= span.to).toBe(true);
      expect(["sessions", "calls", "run_log"]).toContain(span.basis);
    }
  });
});

describe("the retirement field", () => {
  it("is null for every model in v1", () => {
    for (const model of MODELS) expect(retiredOn(realIndex, model)).toBeNull();
    expect(Object.values(realIndex.runs.retired_on).every((v) => v === null)).toBe(true);
  });

  it("is null for a model the data does not list", () => {
    expect(retiredOn(realIndex, "no-such-model")).toBeNull();
  });

  it("returns the date once the data holds one, for that model only", () => {
    const filled = {
      ...realIndex,
      runs: { ...realIndex.runs, retired_on: { ...realIndex.runs.retired_on, "haiku-5-5": "2027-10-07" } },
    } as DataIndex;
    expect(retiredOn(filled, "haiku-5-5")).toBe("2027-10-07");
    expect(retiredOn(filled, "gpt-oss-openrouter")).toBeNull();
  });
});
