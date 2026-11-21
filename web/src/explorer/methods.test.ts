// The methods page (Phase 6.5 steps 4 and 5): its outline, the ledger placement that holds the page to the disclosure
// ledger (doc section 1), the trace of every figure in its words to a source, and the census of every place still a
// placeholder.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { isMethodsPlaceholder, METHODS_PLACEHOLDER } from "./copy";
import type { CellStatus } from "./data";
import { realCasesIndex, realGrids, WEB_ROOT } from "./fixtures";
import { formatCount } from "./format";
import hisJson from "./his.json";
import type { Block, CountSpec, Figure, OutlineSection } from "./Methods";
import outlineJson from "./methods.json";
import { SAFE_SEGMENT } from "./page-meta.mjs";

const REPO = resolve(WEB_ROOT, "..");
const DOC = resolve(REPO, "docs/phases/phase-6.5-methods-and-release-IMPLEMENTATION.md");
const doc = readFileSync(DOC, "utf8");

const sections = outlineJson.sections as unknown as OutlineSection[];
const allBlocks: Array<{ section: string; block: Block }> = sections.flatMap((s) =>
  s.blocks.map((block) => ({ section: s.id, block })),
);

/**
 * The disclosure ledger's ids, written once (doc section 1, "The disclosure ledger"): 1 to 40, plus 14a, 20a and 20b.
 * A test below holds this set equal to the doc's own table, so it cannot drift from the doc; another holds that every
 * id has a block that states it (the definition of done's row 1).
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

  it("has a block for every ledger id of every section, and no block claims an id its section does not carry", () => {
    for (const section of sections) {
      const carried = new Set(section.blocks.flatMap((b) => b.ledger));
      for (const id of carried) expect(section.ledger, `${section.id} block claims ${id}`).toContain(id);
      for (const id of section.ledger)
        expect(carried.has(id), `${section.id} has no block for ledger ${id}`).toBe(true);
    }
  });

  it("keeps the Delivers and definition-of-done references of the sections that carry no ledger id", () => {
    for (const section of sections) {
      if (section.ledger.length === 0)
        expect(section.also.length, `${section.id} has no ledger id`).toBeGreaterThan(0);
    }
  });
});

/**
 * Text from a repository file as prose reads it: markdown quote marks at a line's start, emphasis and code marks
 * dropped, white space collapsed.
 */
function plain(text: string): string {
  return text
    .replace(/^[ \t]*>[ \t]?/gm, "")
    .replace(/[*`]/g, "")
    .replace(/\s+/g, " ");
}
const fileCache = new Map<string, string>();
function repoText(path: string): string {
  let text = fileCache.get(path);
  if (text === undefined) {
    text = plain(readFileSync(resolve(REPO, path), "utf8"));
    fileCache.set(path, text);
  }
  return text;
}

/** The words of a block a reader sees, written in methods.json (a block drawn from data or his.json has none). */
function wordsOf(block: Block): string[] {
  const lead = "lead" in block && block.lead !== undefined ? [block.lead] : [];
  if (block.kind === "p") return [...lead, block.text];
  if (block.kind === "quote") return [...lead, ...block.texts];
  if (block.kind === "list") return [...lead, ...block.items.map((i) => i.text)];
  return [];
}

/**
 * Names that hold digits and are not figures: the models', the tag's, the hash's and the cases' labels. Anything else
 * with a digit in the page's words must be a figure with a source.
 */
const NAMES = [
  "Haiku 5.5",
  "Sonnet 5.5",
  "gpt-oss-120b",
  "prereg-v1",
  "prereg-v2",
  "sha256",
  ...realCasesIndex.cases.map((c) => c.label),
].sort((a, b) => b.length - a.length);

function cellsOf(spec: CountSpec): CellStatus[] {
  const files = realGrids.filter(
    ({ label }) =>
      label.startsWith(`${spec.sweep} ${spec.model} `) &&
      (spec.scenario === undefined || label === `${spec.sweep} ${spec.model} ${spec.scenario}`),
  );
  expect(files.length, JSON.stringify(spec)).toBeGreaterThan(0);
  return files.flatMap(({ file }) => file.cells);
}

/** A count from the results files, as the page writes it. Unsuccessful means attempted minus valid (refusals included). */
function counted(spec: CountSpec): string {
  const cells = cellsOf(spec);
  const lost = (c: CellStatus) => c.attempted - c.valid;
  const attempted = cells.reduce((n, c) => n + c.attempted, 0);
  const unsuccessful = cells.reduce((n, c) => n + lost(c), 0);
  switch (spec.measure) {
    case "attempted":
      return formatCount(attempted);
    case "unsuccessful":
      return formatCount(unsuccessful);
    case "unsuccessful_percent":
      return `${((100 * unsuccessful) / attempted).toFixed(1)}%`;
    case "cells_over_limit":
      return formatCount(cells.filter((c) => lost(c) / c.attempted > 0.1).length);
    case "cells_with_unsuccessful":
      return formatCount(cells.filter((c) => lost(c) > 0).length);
    case "runs_per_cell": {
      const sizes = new Set(cells.map((c) => c.attempted));
      expect(sizes.size, `${JSON.stringify(spec)}: cells differ in size`).toBe(1);
      return formatCount([...sizes][0]!);
    }
  }
}

describe("the page's words", () => {
  it("cites only files that exist in the repository", () => {
    for (const { section, block } of allBlocks) {
      const paths = [...(block.sources ?? []), ...(block.kind === "quote" ? [block.source] : [])];
      for (const path of paths) expect(existsSync(resolve(REPO, path)), `${section}: ${path}`).toBe(true);
      for (const figure of block.figures ?? [])
        if (figure.source !== undefined)
          expect(existsSync(resolve(REPO, figure.source)), `${section}: ${figure.source}`).toBe(true);
    }
  });

  it("quotes word for word: every quoted text is in its source", () => {
    const quotes = allBlocks.filter(({ block }) => block.kind === "quote");
    expect(quotes.length).toBeGreaterThan(0);
    for (const { section, block } of quotes) {
      if (block.kind !== "quote") continue;
      for (const text of block.texts)
        expect(repoText(block.source), `${section}: ${text}`).toContain(plain(text));
    }
  });

  it("traces every figure: a quoted one is in its source as written, a counted one is the results files' count", () => {
    let quoted = 0;
    let countedFigures = 0;
    for (const { section, block } of allBlocks) {
      for (const figure of block.figures ?? []) {
        const where = `${section}: ${figure.text}`;
        expect((figure.source === undefined) !== (figure.count === undefined), `${where}: one source`).toBe(
          true,
        );
        if (figure.count !== undefined) {
          expect(counted(figure.count), where).toBe(figure.text);
          countedFigures += 1;
          continue;
        }
        const match = figure.match ?? figure.text;
        expect(repoText(figure.source!), where).toContain(plain(match));
        // Every run of digits in the figure is in the words it is matched to (a date's day and year, a count).
        for (const digits of figure.text.match(/\d+/g) ?? []) expect(match, where).toContain(digits);
        quoted += 1;
      }
    }
    expect(quoted).toBeGreaterThan(40);
    expect(countedFigures).toBeGreaterThan(10);
  });

  it("holds no digit in its words that is not a figure, a name or a protocol section", () => {
    // A quote's own words are traced whole by the test above (word for word in its source); its lead is not.
    for (const { section, block } of allBlocks) {
      const figures = [...(block.figures ?? [])]
        .map((f: Figure) => f.text)
        .sort((a, b) => b.length - a.length);
      const words = block.kind === "quote" ? (block.lead === undefined ? [] : [block.lead]) : wordsOf(block);
      for (const text of words) {
        let rest = text;
        for (const name of NAMES) rest = rest.split(name).join(" ");
        for (const figure of figures) rest = rest.split(figure).join(" ");
        rest = rest.replace(/§\d+(\.\d+)*/g, " ");
        expect(rest, `${section}: ${text}`).not.toMatch(/\d/);
      }
    }
  });

  it("declares no figure its block does not use", () => {
    for (const { section, block } of allBlocks) {
      const words = wordsOf(block).join(" ");
      for (const figure of block.figures ?? [])
        expect(words, `${section}: ${figure.text}`).toContain(figure.text);
    }
  });

  it("links a list item only to a section of this page", () => {
    const anchors = new Set(sections.map((s) => s.anchor));
    for (const { block } of allBlocks)
      if (block.kind === "list")
        for (const item of block.items) if (item.anchor !== undefined) expect(anchors).toContain(item.anchor);
  });
});

describe("the placeholder census", () => {
  // Every place a placeholder still stands: none. Step 7 wrote M7's (the prompt-reconstruction check, 2026-11-18); step 9
  // wrote the video and its link (M11 and M0, 2026-11-20); step 10 wrote M10's vocabulary recheck (2026-11-21). Go-live
  // (doc section 7) makes `check-dist` refuse any placeholder in dist-explorer/.
  const expected: string[] = [];

  function collect(value: unknown, path: string, found: string[], odd: string[]) {
    if (typeof value === "string") {
      if (isMethodsPlaceholder(value)) found.push(`his.json ${path}`);
      else if (/^\[.*\]$/.test(value)) odd.push(`his.json ${path}`); // a bracketed word that is neither placeholder
    } else if (value !== null && typeof value === "object") {
      for (const [key, inner] of Object.entries(value))
        collect(inner, path === "" ? key : `${path}.${key}`, found, odd);
    }
  }

  it("is the one part a later step writes, and nothing else: his titles and the page's title are written", () => {
    const found: string[] = [];
    const odd: string[] = [];
    collect(hisJson, "", found, odd);
    for (const section of sections) {
      if (section.blocks.length === 0) found.push(`methods.json ${section.id} body`);
      for (const block of section.blocks)
        if (block.kind === "pending") found.push(`methods.json ${section.id} pending`);
    }
    expect(odd).toEqual([]);
    expect(found.sort()).toEqual([...expected].sort());
  });

  it("says, for each part still to write, which step writes it", () => {
    for (const { section, block } of allBlocks)
      if (block.kind === "pending") expect(block.note, section).toMatch(/^step 10: /);
  });

  it("keeps the one exported constant for the placeholders", () => {
    expect(METHODS_PLACEHOLDER).toEqual({ title: "[his title]", body: "[to be written]" });
    expect(Object.values(hisJson.methods.sectionTitles).some(isMethodsPlaceholder)).toBe(false);
  });
});

describe("the video (step 9, doc section 6)", () => {
  const MEDIA = resolve(WEB_ROOT, "explorer-media");
  const videos = allBlocks.filter(({ block }) => block.kind === "video");

  it("is one block, in M11, after its label, and M0 links to it", () => {
    expect(videos.map(({ section }) => section)).toEqual(["M11"]);
    const m11 = sections.find((s) => s.id === "M11")!;
    expect(m11.anchor).toBe("video");
    expect(m11.blocks[0]!.kind).toBe("p");
    const m0 = sections.find((s) => s.id === "M0")!;
    const links = m0.blocks.flatMap((b) => (b.kind === "list" ? b.items.map((i) => i.anchor) : []));
    expect(links).toContain("video");
  });

  it("names every tool that made or checked it in its label and its record", () => {
    const words = sections
      .find((s) => s.id === "M11")!
      .blocks.flatMap((b) => (b.kind === "p" ? [b.text] : []))
      .join(" ");
    for (const tool of ["Gemini Notebook", "Claude", "faster-whisper", "ffmpeg"])
      expect(words, tool).toContain(tool);
    expect(words).toMatch(/AI tools/);
  });

  it("has its file, poster and captions in explorer-media/, the video under the media budget", () => {
    for (const { block } of videos) {
      if (block.kind !== "video") continue;
      for (const name of [block.file, block.poster, block.captions])
        expect(existsSync(resolve(MEDIA, name)), name).toBe(true);
      expect(block.file).toMatch(/\.mp4$/);
      expect(block.poster).toMatch(/\.jpg$/);
      expect(block.captions).toMatch(/\.vtt$/);
    }
  });

  it("shows below it the same words its captions carry, cue by cue, and the end card's words are the scope sentence", () => {
    for (const { block } of videos) {
      if (block.kind !== "video") continue;
      const vtt = readFileSync(resolve(MEDIA, block.captions), "utf8").replace(/\r/g, "");
      expect(vtt.startsWith("WEBVTT\n")).toBe(true);
      const cues = vtt
        .split("\n\n")
        .slice(1)
        .map((cue) => cue.trim().split("\n"))
        .filter((lines) => lines.length >= 3)
        .map((lines) => lines.slice(2).join(" "));
      expect(cues).toEqual(block.spoken);
      expect(block.onScreen).toBe(hisJson.scopeSentence);
    }
  });
});
