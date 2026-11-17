// The methods page's frame (Phase 6.5 step 4): its outline, the ledger placement that holds step 5 to the disclosure
// ledger (doc section 1), and the census of every place his words are still a placeholder.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { isMethodsPlaceholder, METHODS_PLACEHOLDER } from "./copy";
import { WEB_ROOT } from "./fixtures";
import hisJson from "./his.json";
import outlineJson from "./methods.json";
import { SAFE_SEGMENT } from "./page-meta.mjs";

const DOC = resolve(WEB_ROOT, "..", "docs/phases/phase-6.5-methods-and-release-IMPLEMENTATION.md");
const doc = readFileSync(DOC, "utf8");

const sections = outlineJson.sections as Array<{
  id: string;
  anchor: string;
  ledger: string[];
  also: string[];
  blocks: unknown[];
}>;

/**
 * The disclosure ledger's ids, written once (doc section 1, "The disclosure ledger"): 1 to 40, plus 14a, 20a and 20b.
 * A test below holds this set equal to the doc's own table, so it cannot drift from the doc. Step 5 extends the check
 * below to "every ledger id has a block that carries it" (the definition of done's row 1).
 */
const LEDGER_IDS: readonly string[] = [
  ...Array.from({ length: 40 }, (_, i) => String(i + 1)),
  "14a",
  "20a",
  "20b",
];
/** Ledger 17 is split: its counts sit in M3, its consequence in M5 (doc section 3's table). Every other id has one section. */
const IN_TWO = new Map<string, string[]>([["17", ["M3", "M5"]]]);

describe("the outline", () => {
  it("is exactly the thirteen sections M0 to M12, in order, each with a unique, safe anchor", () => {
    expect(sections.map((s) => s.id)).toEqual(Array.from({ length: 13 }, (_, i) => `M${i}`));
    const anchors = sections.map((s) => s.anchor);
    expect(new Set(anchors).size).toBe(13);
    for (const anchor of anchors) expect(anchor, anchor).toMatch(SAFE_SEGMENT);
  });

  it("has a title in his.json for every section, and no title for a section the outline lacks", () => {
    expect(Object.keys(hisJson.methods.sectionTitles)).toEqual(sections.map((s) => s.id));
  });
});

describe("the ledger placement (doc section 1, held to doc section 3)", () => {
  it("is the doc's own list of ledger ids: 1 to 40, plus 14a, 20a and 20b, forty-three in all", () => {
    const section1 = doc.slice(doc.indexOf("## 1. The disclosure ledger"), doc.indexOf("## 2. Decisions"));
    const documented = [...section1.matchAll(/^\| (\d+[ab]?) \|/gm)].map((m) => m[1]!);
    expect([...documented].sort()).toEqual([...LEDGER_IDS].sort());
    expect(LEDGER_IDS).toHaveLength(43);
  });

  it("places every ledger id, and nothing else, with 17 in exactly M3 and M5 and every other id in exactly one section", () => {
    const where = new Map<string, string[]>();
    for (const section of sections) {
      expect(new Set(section.ledger).size, `${section.id} lists an id twice`).toBe(section.ledger.length);
      for (const id of section.ledger) where.set(id, [...(where.get(id) ?? []), section.id]);
    }
    expect([...where.keys()].sort()).toEqual([...LEDGER_IDS].sort());
    for (const id of LEDGER_IDS) {
      expect(where.get(id), `ledger ${id}`).toEqual(IN_TWO.get(id) ?? [expect.stringMatching(/^M\d+$/)]);
    }
  });

  it("matches the Ledger column of the doc's section 3 table, section by section", () => {
    const section3 = doc.slice(doc.indexOf("## 3. The methods page"), doc.indexOf("## 4. Facts"));
    const expand = (cell: string): string[] => {
      const bare = cell.replace(/\([^)]*\)/g, ""); // "(counts)", "(scope Delivers 7)": notes, not ids
      return bare
        .split(",")
        .map((token) => token.trim())
        .filter((token) => token !== "")
        .flatMap((token) => {
          const range = /^(\d+)-(\d+)$/.exec(token);
          if (range === null) return [token];
          const [from, to] = [Number(range[1]), Number(range[2])];
          return Array.from({ length: to - from + 1 }, (_, i) => String(from + i));
        });
    };
    const rows = section3
      .split("\n")
      .filter((line) => /^\| M\d+ \|/.test(line))
      .map((line) =>
        line
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((c) => c.trim()),
      );
    expect(rows.map((cells) => cells[0])).toEqual(sections.map((s) => s.id));
    for (const cells of rows) {
      const section = sections.find((s) => s.id === cells[0])!;
      expect(section.ledger, section.id).toEqual(expand(cells[3]!));
    }
  });

  it("keeps the Delivers and definition-of-done references of the sections that carry no ledger id", () => {
    for (const section of sections) {
      if (section.ledger.length === 0)
        expect(section.also.length, `${section.id} has no ledger id`).toBeGreaterThan(0);
    }
  });
});

describe("the placeholder census", () => {
  // Every place a placeholder stands in for his words or the words of step 5. Step 5 shrinks this list: each title he
  // writes and each body Claude drafts and he approves leaves it. Go-live (doc section 7) must make `check-dist` refuse
  // any placeholder in dist-explorer/; that refusal is NOT added in step 4, because it would fail `make check`.
  const expected = [
    "his.json pages.methods.title",
    "his.json pages.methods.description",
    ...sections.map((s) => `his.json methods.sectionTitles.${s.id}`),
    ...sections.map((s) => `methods.json ${s.id} body`),
  ];

  function collect(value: unknown, path: string, found: string[], odd: string[]) {
    if (typeof value === "string") {
      if (isMethodsPlaceholder(value)) found.push(`his.json ${path}`);
      else if (/^\[.*\]$/.test(value)) odd.push(`his.json ${path}`); // a bracketed word that is neither placeholder
    } else if (value !== null && typeof value === "object") {
      for (const [key, inner] of Object.entries(value))
        collect(inner, path === "" ? key : `${path}.${key}`, found, odd);
    }
  }

  it("is the page's title, its description, thirteen section titles and thirteen bodies, and nothing else", () => {
    const found: string[] = [];
    const odd: string[] = [];
    collect(hisJson, "", found, odd);
    // A section whose blocks are empty shows the body placeholder.
    for (const section of sections)
      if (section.blocks.length === 0) found.push(`methods.json ${section.id} body`);
    expect(odd).toEqual([]);
    expect(found.sort()).toEqual([...expected].sort());
    expect(found).toHaveLength(2 + 13 + 13);
  });

  it("holds his.json's titles and description equal to the one exported constant, never a retyped string", () => {
    expect(hisJson.pages.methods.title).toBe(METHODS_PLACEHOLDER.title);
    expect(hisJson.pages.methods.description).toBe(METHODS_PLACEHOLDER.body);
    for (const title of Object.values(hisJson.methods.sectionTitles))
      expect(title).toBe(METHODS_PLACEHOLDER.title);
    expect(METHODS_PLACEHOLDER).toEqual({ title: "[his title]", body: "[to be written]" });
  });
});
