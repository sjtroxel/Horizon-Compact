import { describe, expect, it } from "vitest";
import { isPlaceholder, PLACEHOLDER_MARK } from "../copy";
import { explorerHis, explorerLabels } from "./copy";
import { allRoutes } from "./page-meta.mjs";
import { realCasesIndex, realIndex } from "./fixtures";

/** Every string in a nested object; a function is called with a sample argument and its text is read. */
function strings(value: unknown, path = ""): Array<[string, string]> {
  if (typeof value === "string") return [[path, value]];
  if (typeof value === "function") return strings((value as (x: string) => unknown)("x"), `${path}()`);
  if (value !== null && typeof value === "object") {
    return Object.entries(value).flatMap(([key, inner]) =>
      strings(inner, path === "" ? key : `${path}.${key}`),
    );
  }
  return [];
}

describe("the explorer's words", () => {
  // The placeholder page's test `his words are written` (src/copy.test.ts) is not widened to these: the explorer's
  // words are unwritten on purpose until Phase 6 doc section 14 step 8. The gate that fails on an unwritten
  // explorer word is Phase 6.5's go-live.
  it("every one of his values is written text or a placeholder that names what goes there", () => {
    const values = strings(explorerHis);
    expect(values.length).toBeGreaterThan(0);
    for (const [path, text] of values) {
      expect(text.trim(), path).not.toBe("");
      if (isPlaceholder(text)) {
        expect(text.endsWith("]"), `${path} closes its placeholder`).toBe(true);
        const named = text.slice(PLACEHOLDER_MARK.length, -1).trim();
        expect(named, `${path} names what goes there`).not.toBe("");
      }
    }
  });

  it("holds a title and a description for every kind of page", () => {
    const kinds = new Set(
      allRoutes(
        realIndex.scenarios.map((s) => s.scenario_id),
        realCasesIndex.cases.map((c) => c.label),
      ).map((route) => route.kind),
    );
    expect([...kinds].sort()).toEqual(Object.keys(explorerHis.pages).sort());
    for (const [kind, page] of Object.entries(explorerHis.pages)) {
      expect(page.title, kind).not.toBe("");
      expect(page.description, kind).not.toBe("");
    }
  });

  it("holds no `[his:` value among the Claude-drafted labels", () => {
    const values = strings(explorerLabels);
    expect(values.length).toBeGreaterThan(0);
    expect(values.filter(([, text]) => isPlaceholder(text) || text.includes(PLACEHOLDER_MARK))).toEqual([]);
    for (const [path, text] of values) expect(text.trim(), path).not.toBe("");
  });

  it("keeps the labels free of the words the page must not carry", () => {
    const text = JSON.stringify(strings(explorerLabels)).toLowerCase();
    for (const word of ["insight", "powered by", "unlock", "seamless", "delve", "leverage", "robust"]) {
      expect(text).not.toContain(word);
    }
  });
});
