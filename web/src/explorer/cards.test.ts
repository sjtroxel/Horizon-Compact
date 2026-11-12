import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { Resvg } from "@resvg/resvg-js";
import { cleanup, render } from "@testing-library/react";
import { createElement } from "react";
import { afterAll, afterEach, describe, expect, it } from "vitest";
import { assertFonts, fontFiles, makeMeasure, rasterize } from "../../scripts/card-render.mjs";
import { writeCards } from "../../scripts/write-cards.mjs";
import {
  BOTTOM_LIMIT,
  FAMILIES,
  FONT_FACES,
  MIN_BODY_SIZE,
  PALETTE,
  STYLES,
  buildCard,
  cardRuns,
  cardSvg,
  collectCardFiles,
  escapeXml,
  layoutCard,
  measureSvg,
  paragraphText,
  wrap,
} from "./cards";
import type { Card, DataRef, LabelSpec, Run } from "./cards";
import { Description } from "./caseParts";
import { SENTENCE_ORDER } from "./chartData";
import { explorerCardLabels, explorerHis, explorerLabels as L } from "./copy";
import type { CaseFile, CasesIndex, DataIndex, GridFile } from "./data";
import { WEB_ROOT, readMemoRows, realMemoIndex } from "./fixtures";
import { CARD_HEIGHT, CARD_WIDTH, allRoutes, cardSlug } from "./page-meta.mjs";
import type { PageRoute } from "./page-meta.mjs";

afterEach(cleanup);

// ---------------------------------------------------------------------------------------------------------------------
// What the tests read: the committed files off disk, with code of their own, so that a card is checked against the data
// and not against the card module's own reading of it.

const his = JSON.parse(readFileSync(resolve(WEB_ROOT, "src/explorer/his.json"), "utf8")) as Record<
  string,
  unknown
>;
const disk = (relative: string): unknown =>
  JSON.parse(readFileSync(resolve(WEB_ROOT, "explorer-data", relative), "utf8"));
const at = (value: unknown, path: string): unknown =>
  path.split(".").reduce<unknown>((v, key) => (v as Record<string, unknown> | undefined)?.[key], value);
const ALL = { ...L, ...explorerCardLabels } as Record<string, unknown>;

const files = collectCardFiles(disk);
const index = disk("index.json") as DataIndex;
const casesIndex = disk(index.files.cases) as CasesIndex;
const scenarioIds = index.scenarios.map((s) => s.scenario_id);
const caseLabels = casesIndex.cases.map((c) => c.label);
const routes = allRoutes(scenarioIds, caseLabels);
const MODELS = L.models.map((m) => m.key); // the page's order: the main model first

const measure = makeMeasure(measureSvg);
const built = routes.map((route) => {
  const card = buildCard(route, files);
  const layout = layoutCard(card, measure);
  return { route, name: cardSlug(route), card, layout, svg: cardSvg(layout) };
});
const cardOf = (slug: string) => built.find((b) => b.name === slug)!;

function dataValue(ref: DataRef): string {
  const raw = at(disk(ref.file), ref.path);
  if (ref.via === "attemptedRuns") {
    return String((raw as Array<{ attempted: number }>).reduce((sum, rate) => sum + rate.attempted, 0));
  }
  if (ref.via === "modelName") return L.models.find((m) => m.key === raw)!.name;
  return String(raw);
}

/** A label's output for its arguments, the arguments' own text, and the label with every argument blank. */
function labelText(spec: LabelSpec): { text: string; args: string[]; fixed: string } {
  const key = spec.select === undefined ? spec.key : `${spec.key}.${dataValue(spec.select)}`;
  const found = at(ALL, key);
  if (typeof found === "string") return { text: found, args: [], fixed: found };
  const args = (spec.args ?? []).map((arg) =>
    "data" in arg ? dataValue(arg.data) : labelText(arg.label).text,
  );
  const call = found as (...values: string[]) => string;
  return { text: call(...args), args, fixed: call(...args.map(() => "")) };
}

/** What a run's text must be, from its source, read independently of the card module. */
function expectedText(run: Run): string {
  const { source } = run;
  if (source.kind === "his") {
    const value = at(his, source.key) as string;
    if (source.id === undefined) return value;
    expect([...scenarioIds, ...caseLabels]).toContain(source.id);
    return `${value} (${source.id})`;
  }
  return source.kind === "label" ? labelText(source.spec).text : dataValue(source.ref);
}

const sourceProblems = (card: Card): string[] =>
  cardRuns(card)
    .filter((run) => run.text !== expectedText(run))
    .map((run) => `"${run.text}" is not what its source says`);

const unescapeXml = (text: string) =>
  text
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&gt;/g, ">")
    .replace(/&lt;/g, "<")
    .replace(/&amp;/g, "&");

/** What is wrong with the SVG's text: anything that is not exactly the runs, in order, block by block. */
function textProblems(card: Card, svg: string): string[] {
  const problems: string[] = [];
  const elements = [...svg.matchAll(/<text data-block="(\d+)"[^>]*>([^<]*)<\/text>/g)];
  if ((svg.match(/<text\b/g) ?? []).length !== elements.length)
    problems.push("a <text> element of another shape");
  for (const forbidden of ["<tspan", "<title", "<desc", "<image", "<style", "<script", "<foreignObject"]) {
    if (svg.includes(forbidden)) problems.push(`the SVG has ${forbidden}`);
  }
  const byBlock = new Map<number, string[]>();
  for (const [, block, text] of elements) {
    byBlock.set(Number(block), [...(byBlock.get(Number(block)) ?? []), unescapeXml(text!)]);
  }
  card.blocks.forEach((block, b) => {
    const expected = block.cells.flatMap((c) => c.paragraphs.map(paragraphText)).join(" ");
    const drawn = (byBlock.get(b) ?? []).join(" ");
    if (drawn !== expected) problems.push(`block ${b} draws "${drawn}", the runs say "${expected}"`);
  });
  for (const block of byBlock.keys())
    if (block >= card.blocks.length) problems.push(`text in block ${block}`);
  return problems;
}

const textOf = (card: Card) =>
  card.blocks.flatMap((b) => b.cells.flatMap((c) => c.paragraphs.map(paragraphText)));
const digits = (text: string): string[] => text.match(/\d+/g) ?? [];

// ---------------------------------------------------------------------------------------------------------------------

describe("the cards: where every string comes from", () => {
  it("has a card for every path the pages are written for, with a safe, unique file name", () => {
    expect(built.map((b) => b.name)).toEqual([
      "story",
      ...scenarioIds.map((id) => `scenario-${id}`),
      "cases",
      ...caseLabels.map((label) => `case-${label}`),
      "studies",
      "memos",
    ]);
    expect(new Set(built.map((b) => b.name)).size).toBe(built.length);
    for (const { name } of built) expect(name).toMatch(/^[a-z0-9][a-z0-9-]*$/);
  });

  it.each(built.map((b) => [b.name, b] as const))(
    "%s: every run equals its source and the SVG's text is exactly the runs, in order",
    (_name, { card, svg }) => {
      expect(sourceProblems(card)).toEqual([]);
      expect(textProblems(card, svg)).toEqual([]);
      expect(cardRuns(card).length).toBeGreaterThan(2);
    },
  );

  it("fails a card drawn with one extra hard-coded string, or a run that is not its source (mutation checks)", () => {
    const { card, svg } = cardOf("scenario-s1");
    expect(textProblems(card, svg)).toEqual([]);
    const extra = svg.replace(
      "</svg>",
      '<text data-block="0" x="60" y="600" font-size="22">Extra words</text></svg>',
    );
    expect(textProblems(card, extra).join(" ")).toContain("Extra words");
    const unlabelled = svg.replace("</svg>", '<text x="60" y="600" font-size="22">No block</text></svg>');
    expect(textProblems(card, unlabelled)).not.toEqual([]);
    const tspan = svg.replace("</svg>", "<tspan>Hidden</tspan></svg>");
    expect(textProblems(card, tspan)).not.toEqual([]);
    const changed = svg.replace("Scenario (s1)", "Scenario (s9)");
    expect(textProblems(card, changed)).not.toEqual([]);

    const mutated = structuredClone(card);
    const run = cardRuns(mutated).find((r) => r.source.kind === "his")!;
    run.text = `${run.text} and more`;
    expect(sourceProblems(mutated)).not.toEqual([]);
    const relabelled = structuredClone(card);
    const label = cardRuns(relabelled).find((r) => r.source.kind === "label")!;
    label.text = "something else";
    expect(sourceProblems(relabelled)).not.toEqual([]);
  });

  it("escapes every string for XML and reads back the same (a quote and an ampersand in a string)", () => {
    expect(escapeXml(`a & b < c > "d" 'e'`)).toBe("a &amp; b &lt; c &gt; &quot;d&quot; &apos;e&apos;");
    expect(unescapeXml(escapeXml(`a & b < c > "d" 'e'`))).toBe(`a & b < c > "d" 'e'`);
    const withApostrophe = built.find((b) => cardRuns(b.card).some((r) => r.text.includes("'")))!;
    expect(withApostrophe.svg).toContain("&apos;");
    expect(withApostrophe.svg).not.toMatch(/>[^<]*'[^<]*<\/text>/);
  });

  it("traces every number to a field of a data file, his words or a model's name (section 10)", () => {
    const modelDigits = new Set(L.models.flatMap((m) => digits(m.name)));
    for (const { name, card } of built) {
      for (const run of cardRuns(card)) {
        const { source } = run;
        if (source.kind === "data" && source.ref.via === undefined) {
          const field = dataValue(source.ref);
          for (const number of digits(run.text)) expect(field, `${name}: ${number}`).toContain(number);
        } else if (source.kind === "data") {
          // A model's name (its digits are the model's) or `attemptedRuns`' sum of the file's counts.
          for (const number of digits(run.text)) {
            if (source.ref.via === "modelName") expect(modelDigits, `${name}: ${number}`).toContain(number);
            else expect(dataValue(source.ref), `${name}: ${number}`).toBe(number);
          }
        } else if (source.kind === "his") {
          const value = at(his, source.key) as string;
          for (const number of digits(run.text)) {
            expect(`${value} (${source.id ?? ""})`, `${name}: ${number}`).toContain(number);
          }
        } else {
          // A label: each number is an argument's, or sits in the label's own fixed words, which hold a model's name
          // and nothing else (a number a label wrote itself would be a result).
          const { text, args, fixed } = labelText(source.spec);
          for (const number of digits(fixed))
            expect(modelDigits, `${name}: label "${fixed}"`).toContain(number);
          for (const number of digits(text)) {
            expect(
              args.some((a) => a.includes(number)) || digits(fixed).includes(number),
              `${name}: ${number} in "${text}"`,
            ).toBe(true);
          }
        }
      }
    }
  });

  it("draws the model's runs from the file the index lists, on every scenario and case card", () => {
    for (const { route, card } of built) {
      for (const run of cardRuns(card)) {
        if (run.source.kind !== "data") continue;
        const { file } = run.source.ref;
        const listed = [
          "index.json",
          index.files.cases,
          ...Object.values(index.files.grid).flatMap((byScenario) => Object.values(byScenario)),
          ...Object.values(index.files.case_results).flatMap((byModel) => Object.values(byModel)),
        ];
        expect(listed, route.kind).toContain(file);
      }
    }
  });
});

describe("the story card", () => {
  const { card } = cardOf("story");
  const text = textOf(card).join(" ");

  it("holds the name, the question, the two models in order, and the scope sentence, and nothing else", () => {
    expect(textOf(card)).toEqual([
      "Horizon Compact",
      explorerHis.landingQuestion,
      `Two models: ${MODELS.map((key) => explorerCardLabels.cardModelNames[key]!).join(" and ")}`,
      explorerHis.scopeSentence,
    ]);
  });

  it("states no result: no verdict word, no template sentence, and no digit outside the models' names", () => {
    for (const word of Object.values(L.verdictWords)) {
      expect(text.toLowerCase(), word).not.toMatch(new RegExp(`\\b${word}\\b`));
    }
    expect(text).not.toMatch(/percentage points|runs?\b|attempted|valid/i);
    const modelDigits = new Set(L.models.flatMap((m) => digits(m.name)));
    for (const number of digits(text)) expect(modelDigits).toContain(number);
  });
});

describe("the scenario cards", () => {
  it.each(scenarioIds)(
    "%s: both models side by side, the main model first, every verdict in its cell",
    (id) => {
      const { card } = cardOf(`scenario-${id}`);
      const grids = MODELS.map((key) => disk(index.files.grid[key]![id]!) as GridFile);

      // The run line of each model, main model first.
      const runLines = card.blocks.flatMap((b) =>
        b.cells.flatMap((c) => c.paragraphs.map(paragraphText)).filter((t) => t.includes(" valid runs of ")),
      );
      expect(runLines).toEqual(
        grids.map((file, i) => {
          const attempted = file.objective_rates.reduce((sum, rate) => sum + rate.attempted, 0);
          return `${L.models[i]!.name}: ${L.capValidOfAttempted(file.descriptive.runs, attempted)}`;
        }),
      );

      // One row per comparison, in SENTENCE_ORDER, with each model's verdict word in its cell.
      const rows = card.blocks.filter((b) => b.cells.length === 3);
      expect(rows).toHaveLength(SENTENCE_ORDER.length);
      SENTENCE_ORDER.forEach(([first, second], i) => {
        const heading = L.storyPairHeading(
          L.objectiveNames[first]!,
          first,
          L.objectiveNames[second]!,
          second,
        );
        const row = rows[i]!;
        expect(paragraphText(row.cells[0]!.paragraphs[0]!)).toBe(heading);
        grids.forEach((file, m) => {
          const comparison = file.comparisons.find((c) => c.first === first && c.second === second)!;
          expect(paragraphText(row.cells[1 + m]!.paragraphs[0]!)).toBe(
            L.verdictWords[comparison.final_verdict],
          );
        });
        // The Roundtable's flag is on C vs D and on no other row.
        const flagged = row.cells[0]!.paragraphs.some((p) => paragraphText(p) === L.roundtableFlag);
        expect(flagged).toBe(first === "C" && second === "D");
      });

      // The scope sentence, last; the title with the scenario's id; the brief.
      const lastBlock = card.blocks[card.blocks.length - 1]!;
      expect(paragraphText(lastBlock.cells[0]!.paragraphs[0]!)).toBe(explorerHis.scopeSentence);
      expect(textOf(card)).toContain(`${explorerHis.pages.scenario.title} (${id})`);
      expect(textOf(card)).toContain((explorerHis.scenarioBriefs as Record<string, string>)[id]);
    },
  );

  it("shows inconclusive and not assessable in place, as the data has them", () => {
    const drawn = new Set(
      scenarioIds.flatMap((id) =>
        cardOf(`scenario-${id}`).card.blocks.flatMap((b) =>
          b.cells.flatMap((c) => c.paragraphs.map(paragraphText)),
        ),
      ),
    );
    expect(drawn).toContain(L.verdictWords.inconclusive);
    expect(drawn).toContain(L.verdictWords.not_assessable);
    expect(drawn).toContain(L.verdictWords.split);
    expect(drawn).toContain(L.verdictWords.no_split);
  });
});

describe("the cases card and the case cards (rule zero)", () => {
  const caseFile = (label: string, model: string) =>
    disk(index.files.case_results[label]![model]!) as CaseFile;
  const sameLabel = (file: CaseFile) =>
    new Set(file.readings.map((r) => r.label)).size === 1 ? file.readings[0]!.label : null;
  const lineY = (name: string, test: (text: string) => boolean) =>
    cardOf(name)
      .layout.lines.filter((l) => test(l.text))
      .map((l) => l.y);

  it("the cases card: the exploratory label first, verbatim, then the one line and the five labels", () => {
    const { card } = cardOf("cases");
    const distinct = [...new Set(casesIndex.cases.map((c) => c.exploratory_label))];
    const everyLabel = caseLabels.flatMap((label) =>
      MODELS.flatMap((model) => caseFile(label, model).readings.map((r) => r.label)),
    );
    expect(everyLabel.every((label) => label === "no_good_match")).toBe(true); // the real data's own case
    expect(textOf(card)).toEqual([
      "Horizon Compact",
      explorerHis.pages.cases.title,
      ...distinct,
      L.allNoGoodMatch,
      ...caseLabels,
      explorerHis.scopeSentence,
    ]);
    // Above every reading line, by y.
    const labelYs = lineY("cases", (t) => t.startsWith("exploratory:"));
    const readingY = lineY("cases", (t) => t === L.allNoGoodMatch)[0]!;
    expect(labelYs.length).toBeGreaterThan(0);
    for (const y of labelYs) expect(y).toBeLessThan(readingY);
  });

  it("the cases card: rows with each model's label when the readings are not all no good match", () => {
    const path = index.files.case_results["pre-11"]!["haiku-5-5"]!;
    // Every reading of one file labelled `match`: that model's label is shown, and the other model's is not changed.
    const allMatch = structuredClone(files) as Record<string, unknown>;
    for (const reading of (allMatch[path] as CaseFile).readings) reading.label = "match";
    // The readings of one file differ: the card says so, as the story does.
    const differing = structuredClone(files) as Record<string, unknown>;
    (differing[path] as CaseFile).readings[0]!.label = "tie";
    expect((differing[path] as CaseFile).readings.length).toBeGreaterThan(1);
    for (const [edited, expected] of [
      [allMatch, L.readingLabels.match!],
      [differing, L.storyLabelVaries],
    ] as const) {
      const card = buildCard({ kind: "cases" }, edited);
      const text = textOf(card);
      expect(text).not.toContain(L.allNoGoodMatch);
      expect(text).toContain(`${L.models[0]!.name}: ${expected}`);
      expect(text).toContain(`${L.models[1]!.name}: ${L.readingLabels.no_good_match!}`);
      // The SVG is still exactly the runs (the runs read the edited files here, so the disk-reading source check is not
      // asked of them).
      expect(textProblems(card, cardSvg(layoutCard(card, measure)))).toEqual([]);
    }
  });

  it.each(caseLabels)(
    "%s: the exploratory label first and verbatim, the description as it is shown, each model's label, nothing else",
    (label) => {
      const { card, layout } = cardOf(`case-${label}`);
      const entry = casesIndex.cases.find((c) => c.label === label)!;
      const shown = render(createElement(Description, { entry })).container.textContent;
      const lines = textOf(card);
      expect(lines).toEqual([
        "Horizon Compact",
        `${explorerHis.pages.case.title} (${label})`,
        entry.exploratory_label,
        shown,
        ...MODELS.map((model) => {
          const same = sameLabel(caseFile(label, model));
          const word = same === null ? L.storyLabelVaries : L.readingLabels[same]!;
          return `${L.models.find((m) => m.key === model)!.name}: ${word}`;
        }),
        explorerHis.scopeSentence,
      ]);
      // The label is above every reading label, by y.
      const labelY = layout.lines.find((l) => l.text.startsWith("exploratory:"))!.y;
      const readingYs = layout.lines
        .filter((l) => L.models.some((m) => l.text.startsWith(`${m.name}: `)))
        .map((l) => l.y);
      // A model's name, then its label: no "Label:" of the card's own (section 29b).
      expect(lines.join(" ")).not.toContain("Label:");
      expect(readingYs).toHaveLength(MODELS.length);
      for (const y of readingYs) expect(labelY).toBeLessThan(y);

      // Nothing the case page keeps below the label: no nearest goal, distance, dossier field, matcher reason or memo.
      const text = lines.join(" ");
      for (const model of MODELS) {
        const file = caseFile(label, model);
        for (const reading of file.readings) {
          expect(text).not.toContain(reading.reason);
          for (const d of reading.distances) {
            for (const value of [d.distance, d.low, d.high]) expect(text).not.toContain(value.toFixed(3));
          }
          for (const line of reading.observable_lines)
            expect(text.toLowerCase()).not.toContain(line.toLowerCase());
        }
        expect(text).not.toContain(
          file.company.choice === "close" ? "closed the plant" : file.company.choice,
        );
        expect(text).not.toContain(file.sweep_id);
        expect(text).not.toContain(String(file.memo_counts.runs));
      }
      // The words of the case's own label and description are the cases page's, verbatim; take them out and nothing
      // about a nearest goal, a distance, the dossier, a memo, the probes or the sources is left.
      const rest = text.replace(entry.exploratory_label, "").replace(shown ?? "", "");
      expect(rest).not.toMatch(/nearest|distance|dossier|memo|interval|threshold|probe|reidentif|source/i);
      expect(text).not.toContain(entry.dossier.reason);
      expect(text).not.toContain(entry.reidentification.reason);
    },
  );

  it("shows the withheld case by its status, as the page does, and a published one by its text", () => {
    const withheld = casesIndex.cases.filter((c) => c.description.status !== "published");
    const published = casesIndex.cases.filter((c) => c.description.status === "published");
    expect(withheld.length).toBeGreaterThan(0);
    expect(published.length).toBeGreaterThan(0);
    for (const entry of withheld) {
      expect(textOf(cardOf(`case-${entry.label}`).card)).toContain(
        L.caseDescriptionStatus(entry.description.status),
      );
    }
    for (const entry of published)
      expect(textOf(cardOf(`case-${entry.label}`).card)).toContain(entry.description.text!);
  });
});

describe("the studies and memos cards", () => {
  it("the studies card: his description and the scope sentence, and no study result", () => {
    const { card } = cardOf("studies");
    expect(textOf(card)).toEqual([
      "Horizon Compact",
      explorerHis.pages.studies.title,
      explorerHis.pages.studies.description,
      explorerHis.scopeSentence,
    ]);
    const text = textOf(card).join(" ").toLowerCase();
    for (const word of Object.values(L.verdictWords)) expect(text).not.toMatch(new RegExp(`\\b${word}\\b`));
    expect(digits(text)).toEqual([]);
  });

  it("the memos card: the memo label's fixed part, and no memo text", () => {
    const { card } = cardOf("memos");
    expect(textOf(card)).toEqual([
      "Horizon Compact",
      explorerHis.pages.memos.title,
      explorerHis.pages.memos.description,
      explorerCardLabels.cardMemoLabel,
      explorerHis.scopeSentence,
    ]);
    const text = textOf(card).join(" ");
    let checked = 0;
    for (const file of realMemoIndex.files) {
      for (const row of readMemoRows(file)) {
        if (row.memo === null) continue;
        checked = checked + 1;
        expect(text).not.toContain(row.memo.slice(0, 60));
      }
    }
    expect(checked).toBeGreaterThan(1000);
    expect(text).not.toContain(textOf(cardOf("story").card)[2]!);
  });

  it("the memo label's fixed part says what the memo card's label says of every memo (it is tied to it)", () => {
    const real = L.memoCardLabel("MODEL", "A", "GOAL", false);
    const fixed = explorerCardLabels.cardMemoLabel;
    expect(real).toContain(fixed.slice(fixed.indexOf("for a fictional company")));
    expect(fixed).toMatch(/^Written by a model under one goal, /);
  });
});

describe("the labels written for the cards", () => {
  // The labels with the models' names left blank: what is the label's own and not a data field's.
  const strings = [
    explorerCardLabels.cardName,
    explorerCardLabels.cardTwoModels("", ""),
    explorerCardLabels.cardMemoLabel,
    ...Object.values(explorerCardLabels.cardAlt),
  ];

  it("has alternative text for every kind of page, and states no result, no ratio and no number", () => {
    for (const kind of ["story", "scenario", "cases", "case", "studies", "memos"]) {
      expect(explorerCardLabels.cardAlt[kind], kind).toBeTruthy();
    }
    expect(Object.keys(explorerCardLabels.cardAlt).sort()).toEqual([
      "case",
      "cases",
      "memos",
      "scenario",
      "story",
      "studies",
    ]);
    for (const text of strings) {
      expect(text).not.toMatch(/\d/);
      expect(text.toLowerCase()).not.toMatch(
        /\b(half|twice|double|triple|times|ratio|percent|more than|fewer|less than|same|different|differ|no split|inconclusive|not assessable)\b|%/,
      );
      for (const word of Object.values(L.verdictWords)) {
        expect(text.toLowerCase(), word).not.toMatch(new RegExp(`\\b${word}\\b`));
      }
    }
  });

  it("gives a full name for every model the page names, and each full name holds the page's short name", () => {
    expect(Object.keys(explorerCardLabels.cardModelNames).sort()).toEqual([...MODELS].sort());
    for (const model of L.models) {
      expect(explorerCardLabels.cardModelNames[model.key], model.key).toContain(model.name);
    }
  });

  it("names no company and no goal color, and the cards use no goal color", () => {
    for (const { svg } of built) {
      for (const token of [
        "--o-a",
        "--o-b",
        "--o-c",
        "--o-d",
        "--o-e",
        "#daa668",
        "#5fa1f3",
        "#81520a",
        "#07519d",
      ]) {
        expect(svg).not.toContain(token);
      }
    }
  });
});

describe("the layout", () => {
  it("measures a line by drawing it: a wider string is wider, and a line with nothing in it is 0", () => {
    expect(measure("Horizon", "cell")).toBeGreaterThan(0);
    expect(measure("Horizon Compact", "cell")).toBeGreaterThan(measure("Horizon", "cell"));
    // The style is part of the measure. ("note" and "cell" are the same face, weight and size now that the serif is gone,
    // so a style that differs in size or weight is compared instead.)
    expect(measure("Horizon Compact", "cell")).not.toBe(measure("Horizon Compact", "title"));
    expect(measure("Horizon Compact", "cell")).not.toBe(measure("Horizon Compact", "strong"));
  });

  it("wraps at words, by measurement: no line wider than its box, and the words come back in order", () => {
    const text = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen";
    for (const box of [140, 260, 480]) {
      const lines = wrap(text, "cell", box, measure);
      expect(lines.join(" ")).toBe(text);
      expect(lines.length).toBeGreaterThan(1);
      for (const line of lines) expect(measure(line, "cell")).toBeLessThanOrEqual(box);
      // Greedy: the first word of the next line would not have fitted on this one.
      lines.slice(0, -1).forEach((line, i) => {
        const next = lines[i + 1]!.split(" ")[0]!;
        expect(measure(`${line} ${next}`, "cell")).toBeGreaterThan(box);
      });
    }
    expect(wrap("Supercalifragilisticexpialidocious", "cell", 30, measure)).toEqual([
      "Supercalifragilisticexpialidocious",
    ]);
  });

  it.each(built.map((b) => [b.name, b] as const))(
    "%s: no line wider than its box, nothing below the lower margin, body text 22 px or more",
    (_name, { layout, svg }) => {
      for (const line of layout.lines) {
        expect(line.width, line.text).toBeLessThanOrEqual(line.maxWidth);
        expect(STYLES[line.style].size, line.text).toBeGreaterThanOrEqual(MIN_BODY_SIZE);
        // The width again, from resvg's own bounding box of that one line.
        expect(measure(line.text, line.style)).toBe(line.width);
      }
      expect(layout.bottom).toBeLessThanOrEqual(BOTTOM_LIMIT);
      expect(BOTTOM_LIMIT).toBeLessThan(CARD_HEIGHT);

      // The whole card's text, drawn on its own: inside the card on every side.
      const textOnly = svg.replace(/<rect[^>]*\/>/g, "");
      const box = new Resvg(textOnly, {
        font: { loadSystemFonts: false, fontFiles: fontFiles() },
      }).getBBox()!;
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(CARD_WIDTH);
      expect(box.y).toBeGreaterThanOrEqual(0);
      expect(box.y + box.height).toBeLessThanOrEqual(CARD_HEIGHT);
    },
  );

  it("stops the build for a card that does not fit, instead of drawing it cut off", () => {
    const { card } = cardOf("scenario-s1");
    const tooTall = structuredClone(card);
    tooTall.blocks.splice(
      2,
      0,
      ...structuredClone(card.blocks.slice(1, 2)),
      ...structuredClone(card.blocks.slice(1, 2)),
    );
    const layout = layoutCard(tooTall, measure);
    expect(layout.bottom).toBeGreaterThan(BOTTOM_LIMIT);
  });

  it("every style is one of the two families at a weight the committed fonts have, and no style is a serif (step 11)", () => {
    const families = new Set(Object.values(STYLES).map((s) => s.family));
    expect([...families].sort()).toEqual(Object.values(FAMILIES).sort());
    expect(FONT_FACES.map((f) => `${f.family} ${f.weight}`).sort()).toEqual([
      "Big Shoulders Display 800",
      "Source Sans 3 400",
      "Source Sans 3 600",
    ]);
    // The three styles that were Newsreader in C7 are Source Sans 3 400 now, at their sizes.
    for (const name of ["headline", "prose", "note"] as const) {
      expect(STYLES[name].family, name).toBe(FAMILIES.sans);
      expect(STYLES[name].weight, name).toBe(400);
    }
    expect(Object.values(STYLES).filter((s) => s.family === FAMILIES.display)).toHaveLength(2); // hero and name only
    expect(FAMILIES).not.toHaveProperty("serif");
  });
});

describe("the fonts and the palette", () => {
  it("each family at each weight is one of the committed TTFs, with system fonts off", () => {
    const widths = assertFonts(FONT_FACES);
    expect(widths.size).toBe(FONT_FACES.length);
    for (const width of widths.values()) expect(width).toBeGreaterThan(0);
    // Three different faces draw three different widths: none is standing in for another.
    expect(new Set(widths.values()).size).toBe(FONT_FACES.length);
    // One word in each style has a bounding box.
    for (const style of Object.keys(STYLES) as Array<keyof typeof STYLES>) {
      expect(measure("Horizon", style), style).toBeGreaterThan(0);
    }
  });

  it("stops, and does not draw with another face, for a family it does not have", () => {
    expect(() => assertFonts([{ family: "Not A Family", weight: 400 }])).toThrow(/not among the TTFs/);
    expect(() => assertFonts([{ family: "Newsreader", weight: 400 }])).toThrow(/not among the TTFs/);
    expect(() => assertFonts(FONT_FACES, fontFiles().slice(0, 1))).toThrow();
  });

  it("with no font files, a card renders no text: the fonts are what draws it", () => {
    const { svg } = cardOf("story");
    const noFonts = makeMeasure(measureSvg, []);
    expect(noFonts("Horizon Compact", "cell")).toBe(0);
    const withFonts = rasterize(svg, CARD_WIDTH);
    const without = rasterize(svg, CARD_WIDTH, []);
    const textless = rasterize(svg.replace(/<text[^>]*>[^<]*<\/text>/g, ""), CARD_WIDTH, []);
    expect(Buffer.compare(withFonts, without)).not.toBe(0);
    expect(Buffer.compare(without, textless)).toBe(0);
  });

  it("copies the palette from styles.css: each constant is its token's light value", () => {
    const css = readFileSync(resolve(WEB_ROOT, "src/styles.css"), "utf8");
    const open = css.indexOf(":root {");
    const block = css.slice(open, css.indexOf("}", open));
    const tokens: Record<string, string> = {};
    for (const match of block.matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)) tokens[match[1]!] = match[2]!.trim();
    expect(PALETTE).toEqual({
      surface: tokens["--surface"],
      ink: tokens["--ink"],
      ink2: tokens["--ink2"],
      grid: tokens["--grid"],
      accent: tokens["--accent"],
      sun: tokens["--sun"],
    });
    for (const value of Object.values(PALETTE)) expect(value).toMatch(/^#[0-9a-f]{6}$/);
    // Every color the SVG uses is one of the six.
    const used = new Set(built.flatMap((b) => [...b.svg.matchAll(/#[0-9a-fA-F]{3,8}\b/g)].map((m) => m[0])));
    for (const color of used) expect(Object.values(PALETTE)).toContain(color);
  });

  it("names its families as the site's CSS does, and ships no serif: the Newsreader TTF and its licence are not in fonts-ttf/", () => {
    const css = readFileSync(resolve(WEB_ROOT, "src/styles.css"), "utf8");
    expect(css).toContain(`font-family: "${FAMILIES.display}"`);
    expect(css).toContain(`font-family: "${FAMILIES.sans}"`);
    const files = readdirSync(resolve(WEB_ROOT, "fonts-ttf"));
    expect(files.filter((name) => /newsreader/i.test(name))).toEqual([]);
    expect(files.sort()).toEqual([
      "BigShouldersDisplay-ExtraBold.ttf",
      "OFL-BigShouldersDisplay.txt",
      "OFL-SourceSans3.txt",
      "SourceSans3-Regular.ttf",
      "SourceSans3-Semibold.ttf",
    ]);
  });
});

describe("the PNG files", () => {
  const dirs: string[] = [];
  const temp = () => {
    const dir = mkdtempSync(join(tmpdir(), "cards-"));
    dirs.push(dir);
    return dir;
  };
  afterAll(() => {
    for (const dir of dirs) rmSync(dir, { recursive: true, force: true });
  });
  const size = (png: Buffer) => [png.readUInt32BE(16), png.readUInt32BE(20)];

  it("rasterizes each card at 1200 by 630", () => {
    for (const { svg, name } of built) {
      const png = rasterize(svg, CARD_WIDTH);
      expect(png.subarray(1, 4).toString("latin1"), name).toBe("PNG");
      expect(png.subarray(12, 16).toString("latin1")).toBe("IHDR");
      expect(size(png), name).toEqual([CARD_WIDTH, CARD_HEIGHT]);
    }
  });

  it("gives the same bytes for the same SVG twice", () => {
    for (const name of ["story", "scenario-s1", "case-pre-11"]) {
      const { svg } = cardOf(name);
      expect(Buffer.compare(rasterize(svg, CARD_WIDTH), rasterize(svg, CARD_WIDTH)), name).toBe(0);
    }
  });

  // Two whole builds, each its own test so each stays well under the time limit.
  let first: Awaited<ReturnType<typeof writeCards>>;
  let firstDir = "";
  it("the build writes one card per path, and each file is what the module draws", async () => {
    firstDir = temp();
    first = await writeCards(WEB_ROOT, firstDir);
    expect(first.map((c) => `${c.slug}.png`).sort()).toEqual(readdirSync(firstDir).sort());
    expect(first.map((c) => c.slug)).toEqual(built.map((x) => x.name));
    for (const name of readdirSync(firstDir)) {
      expect(size(readFileSync(join(firstDir, name))), name).toEqual([CARD_WIDTH, CARD_HEIGHT]);
    }
    const story = readFileSync(join(firstDir, "story.png"));
    expect(Buffer.compare(story, rasterize(cardOf("story").svg, CARD_WIDTH))).toBe(0);
  });

  it("the same build twice gives the same bytes in every file (the cards are reproducible)", async () => {
    const secondDir = temp();
    const second = await writeCards(WEB_ROOT, secondDir);
    expect(second.map((c) => c.bytes)).toEqual(first.map((c) => c.bytes));
    for (const name of readdirSync(firstDir)) {
      expect(
        Buffer.compare(readFileSync(join(firstDir, name)), readFileSync(join(secondDir, name))),
        name,
      ).toBe(0);
    }
  });

  it("a route's card is named by its path: slug, folder and file", () => {
    const route: PageRoute = { kind: "scenario", id: "s1" };
    expect(cardSlug(route)).toBe("scenario-s1");
  });
});
