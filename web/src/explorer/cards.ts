/**
 * The share cards (Phase 6 IMPLEMENTATION doc section 10, C7): one 1200 by 630 card per path, drawn as SVG from the same
 * data files the views read and rasterized by the build (web/scripts/write-cards.mjs, with resvg and the committed
 * TTFs). Nothing here runs in the browser: no view imports this file, and the placeholder entry cannot reach it.
 *
 * THE RULE THAT MAKES A CARD SAFE. A card is a binary file, which the name guard cannot read. So every string a card
 * draws is one of three kinds of run, each tagged with where it came from, and the SVG's text is exactly those runs
 * and nothing else (cards.test.ts reads the SVG back and compares):
 *
 *   his    a value of his.json, by its key (a page title carries the route's own id, as `pageMeta` writes it);
 *   label  an `explorerLabels` value, or its output for arguments that are data fields;
 *   data   a field of a data file, by file and path (a model's name goes through `modelName`).
 *
 * A card reads nothing of a real case that the cases page does not already show: the exploratory label, the
 * description or its status, and each model's label (rule zero, CLAUDE.md). No chart, no goal color, and no color that
 * carries a verdict. No number is computed from data: the numbers on a card are fields, `format.ts`'s `attemptedRuns`
 * (an integer sum of run counts) or the layout's own pixel positions (rule 3 of format.ts's header).
 */
import { everyReadingNoGoodMatch, labelUnderEveryReading } from "./caseData";
import { SENTENCE_ORDER } from "./chartData";
import { explorerCardLabels, explorerHis, explorerLabels, isPlaceholder } from "./copy";
import type { CaseFile, CasesIndex, DataIndex, GridFile, ObjectiveRate } from "./data";
import { attemptedRuns } from "./format";
import { modelName, orderedModels } from "./models";
import { CARD_HEIGHT, CARD_WIDTH, pageMeta } from "./page-meta.mjs";
import type { PageRoute } from "./page-meta.mjs";

// ---------------------------------------------------------------------------------------------------------------------
// The look: the site's light palette and its three families (styles.css), copied as constants. palette.test.ts and
// cards.test.ts tie each one to its CSS value.

export const PALETTE = {
  surface: "#f6f2e9",
  ink: "#141a26",
  ink2: "#4d4a43",
  grid: "#e2dbcb",
  accent: "#1c3a66",
  sun: "#e9a23b",
} as const;

/**
 * The families as the TTF files name them. Newsreader's static files are one per optical size: the 16pt one is the
 * text size, the same design as the site's WOFF2 (Google Fonts' default instance). The site says "Newsreader".
 */
export const FAMILIES = {
  display: "Big Shoulders Display",
  serif: "Newsreader 16pt",
  sans: "Source Sans 3",
} as const;

export type StyleName =
  "hero" | "name" | "title" | "headline" | "prose" | "note" | "cell" | "strong" | "flag" | "label";

export interface TextStyle {
  family: string;
  weight: number;
  size: number;
  lineHeight: number;
  fill: string;
}

/** Body text is never smaller than 22 px: a card is seen small (cards.test.ts). */
export const MIN_BODY_SIZE = 22;

export const STYLES: Readonly<Record<StyleName, TextStyle>> = {
  hero: { family: FAMILIES.display, weight: 800, size: 72, lineHeight: 1.0, fill: PALETTE.accent },
  name: { family: FAMILIES.display, weight: 800, size: 38, lineHeight: 1.1, fill: PALETTE.accent },
  title: { family: FAMILIES.sans, weight: 600, size: 40, lineHeight: 1.15, fill: PALETTE.ink },
  headline: { family: FAMILIES.serif, weight: 400, size: 32, lineHeight: 1.3, fill: PALETTE.ink },
  prose: { family: FAMILIES.serif, weight: 400, size: 24, lineHeight: 1.28, fill: PALETTE.ink },
  note: { family: FAMILIES.serif, weight: 400, size: 22, lineHeight: 1.28, fill: PALETTE.ink2 },
  cell: { family: FAMILIES.sans, weight: 400, size: 22, lineHeight: 1.28, fill: PALETTE.ink },
  strong: { family: FAMILIES.sans, weight: 600, size: 22, lineHeight: 1.28, fill: PALETTE.ink },
  flag: { family: FAMILIES.sans, weight: 600, size: 22, lineHeight: 1.28, fill: PALETTE.ink2 },
  label: { family: FAMILIES.sans, weight: 600, size: 22, lineHeight: 1.28, fill: PALETTE.ink },
};

/** Each family and weight a card uses, once: the build checks that every one resolves to a committed TTF. */
export const FONT_FACES: ReadonlyArray<{ family: string; weight: number }> = [
  ...new Map(
    Object.values(STYLES).map((s) => [`${s.family}|${s.weight}`, { family: s.family, weight: s.weight }]),
  ).values(),
];

// ---------------------------------------------------------------------------------------------------------------------
// Runs and where they came from.

export type Via = "attemptedRuns" | "modelName";

/** A field of a data file: the file by its path under explorer-data/, the field by a dotted path into it. */
export interface DataRef {
  file: string;
  path: string;
  /** `attemptedRuns`: `format.ts`'s integer sum of a file's `objective_rates`; `modelName`: the page's name of a model key. */
  via?: Via;
}

export interface LabelSpec {
  /** A dotted path into `explorerLabels`: a string, or a function taking `args`. */
  key: string;
  /** A data field whose value is appended to `key` (`verdictWords` + `split`): the data picks the word. */
  select?: DataRef;
  args?: Arg[];
}

export type Arg = { data: DataRef } | { label: LabelSpec };

export type Source =
  | { kind: "his"; key: string; id?: string }
  | { kind: "label"; spec: LabelSpec }
  | { kind: "data"; ref: DataRef };

export interface Run {
  text: string;
  source: Source;
}

export type CardFiles = Readonly<Record<string, unknown>>;

/** Every label a card may use: the explorer's own, and the cards' (a separate export, see copy.ts). */
const LABELS = { ...explorerLabels, ...explorerCardLabels };

function getPath(value: unknown, path: string): unknown {
  let current = value;
  for (const part of path.split(".")) {
    if (current === null || typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

function resolveRef(files: CardFiles, ref: DataRef): string | number {
  const value = getPath(files[ref.file], ref.path);
  if (ref.via === "attemptedRuns") {
    if (!Array.isArray(value)) throw new Error(`cards: ${ref.file} ${ref.path} is not a list of rates`);
    return attemptedRuns(value as ObjectiveRate[]);
  }
  if (typeof value !== "string" && typeof value !== "number") {
    throw new Error(`cards: ${ref.file} has no text or number at ${ref.path}`);
  }
  return ref.via === "modelName" ? modelName(String(value)) : value;
}

function evalLabel(files: CardFiles, spec: LabelSpec): string {
  const key = spec.select === undefined ? spec.key : `${spec.key}.${String(resolveRef(files, spec.select))}`;
  const found = getPath(LABELS, key);
  if (typeof found === "string") return found;
  if (typeof found === "function") {
    const args = (spec.args ?? []).map((arg) =>
      "data" in arg ? resolveRef(files, arg.data) : evalLabel(files, arg.label),
    );
    return (found as (...values: unknown[]) => string)(...args);
  }
  throw new Error(`cards: no label at ${key}`);
}

/** Refuses words he has not written: a placeholder must never be drawn onto an image. */
function written(text: string, where: string): string {
  if (isPlaceholder(text)) throw new Error(`cards: ${where} is still a placeholder`);
  return text;
}

function hisRun(key: string): Run {
  const value = getPath(explorerHis, key);
  if (typeof value !== "string") throw new Error(`cards: his.json has no text at ${key}`);
  return { text: written(value, `his.json ${key}`), source: { kind: "his", key } };
}

/** A page's title as `pageMeta` writes it, with the route's id after it for a scenario and a case. */
function titleRun(route: PageRoute): Run {
  const key = `pages.${route.kind}.title`;
  const id = route.kind === "scenario" ? route.id : route.kind === "case" ? route.label : undefined;
  const text = written(pageMeta(route, explorerHis.pages).title, `his.json ${key}`);
  return { text, source: id === undefined ? { kind: "his", key } : { kind: "his", key, id } };
}

const labelRun = (files: CardFiles, spec: LabelSpec): Run => ({
  text: evalLabel(files, spec),
  source: { kind: "label", spec },
});

const dataRun = (files: CardFiles, ref: DataRef): Run => ({
  text: String(resolveRef(files, ref)),
  source: { kind: "data", ref },
});

// ---------------------------------------------------------------------------------------------------------------------
// The card: blocks in reading order, each a row of cells, each cell a stack of paragraphs.

export interface Paragraph {
  style: StyleName;
  runs: Run[];
  /** What goes between runs: a space unless the paragraph says ": " (a model's name, then what is said of it). */
  joiner?: " " | ": ";
  /** A bar beside the paragraph: the exploratory label's mark (the CSS gives it a left border). */
  rule?: boolean;
}

export interface Cell {
  x: number;
  width: number;
  align?: "start" | "end";
  paragraphs: Paragraph[];
}

export interface Block {
  cells: Cell[];
  /** Space above the block, in pixels. */
  gap: number;
  /** A thin line under the block (a table row). */
  divider?: boolean;
  /** Placed so its last line ends at the card's lower margin, with a thin line above it: the scope sentence. Last block only. */
  pin?: "bottom";
}

export interface Card {
  route: PageRoute;
  blocks: Block[];
}

export const LEFT = 56;
export const RIGHT = CARD_WIDTH - 56;
const WIDTH = RIGHT - LEFT;
const TOP = 34;
/** The lowest a line of text may end. */
export const BOTTOM_LIMIT = CARD_HEIGHT - 34;
/** The least space between the content and the pinned scope sentence's line above it. */
const PIN_CLEARANCE = 22;
const RULE_INDENT = 20;

const paragraph = (
  style: StyleName,
  runs: Run[],
  extra: { joiner?: " " | ": "; rule?: boolean } = {},
): Paragraph => {
  const made: Paragraph = { style, runs };
  if (extra.joiner !== undefined) made.joiner = extra.joiner;
  if (extra.rule === true) made.rule = true;
  return made;
};

const cell = (x: number, width: number, paragraphs: Paragraph[], align?: "end"): Cell =>
  align === undefined ? { x, width, paragraphs } : { x, width, align, paragraphs };

const full = (gap: number, ...paragraphs: Paragraph[]): Block => ({
  cells: [cell(LEFT, WIDTH, paragraphs)],
  gap,
});

/** The name, and the page's title beside it (right-aligned): for the cards with a table or a long label to fit. */
function headerRow(files: CardFiles, route: PageRoute): Block {
  return {
    gap: 0,
    cells: [
      cell(LEFT, 420, [paragraph("name", [labelRun(files, { key: "cardName" })])]),
      cell(LEFT + 440, WIDTH - 440, [paragraph("title", [titleRun(route)])], "end"),
    ],
  };
}

/** The name, large, above the page's title, each on its own line: for the cards with room. */
function headerStack(files: CardFiles, route: PageRoute): Block[] {
  return [
    full(0, paragraph("hero", [labelRun(files, { key: "cardName" })])),
    full(6, paragraph("title", [titleRun(route)])),
  ];
}

/** The scope sentence, pinned to the card's foot on every card. */
const scope = (): Block => ({
  ...full(0, paragraph("note", [hisRun("scopeSentence")])),
  pin: "bottom",
});

function dataOf(files: CardFiles): { index: DataIndex; casesIndex: CasesIndex } {
  const index = files["index.json"] as DataIndex | undefined;
  if (index === undefined) throw new Error("cards: index.json is not among the files");
  const casesIndex = files[index.files.cases] as CasesIndex | undefined;
  if (casesIndex === undefined) throw new Error(`cards: ${index.files.cases} is not among the files`);
  return { index, casesIndex };
}

/** The models in the order the page shows them, each with its place in the data's own list (for a field's path). */
function modelsInOrder(index: DataIndex): Array<{ key: string; at: number }> {
  return orderedModels(index.models).map((entry) => ({
    key: entry.model_key,
    at: index.models.findIndex((m) => m.model_key === entry.model_key),
  }));
}

const modelNameRun = (files: CardFiles, at: number): Run =>
  dataRun(files, { file: "index.json", path: `models.${at}.model_key`, via: "modelName" });

// ---------------------------------------------------------------------------------------------------------------------
// One card per kind of path.

function storyCard(files: CardFiles, route: PageRoute): Card {
  const { index } = dataOf(files);
  const [first, second] = modelsInOrder(index);
  if (first === undefined || second === undefined) throw new Error("cards: the story card names two models");
  const twoModels = labelRun(files, {
    key: "cardTwoModels",
    args: [
      // The full names (`cardModelNames`), picked by the data's model keys: this card is the one seen away from the site.
      {
        label: {
          key: "cardModelNames",
          select: { file: "index.json", path: `models.${first.at}.model_key` },
        },
      },
      {
        label: {
          key: "cardModelNames",
          select: { file: "index.json", path: `models.${second.at}.model_key` },
        },
      },
    ],
  });
  return {
    route,
    blocks: [
      // The name only, not the page title: the story's title begins with the name, so the card printed it twice, and a
      // link preview shows og:title as text beside the image anyway (Opus review, section 29a).
      full(0, paragraph("hero", [labelRun(files, { key: "cardName" })])),
      full(34, paragraph("headline", [hisRun("landingQuestion")])),
      full(30, paragraph("strong", [twoModels])),
      scope(),
    ],
  };
}

const COL_LABEL = { x: LEFT, width: 740 };
const COL_ONE = { x: LEFT + 750, width: 160 };
const COL_TWO = { x: LEFT + 928, width: 160 };

function scenarioCard(files: CardFiles, route: PageRoute & { kind: "scenario" }): Card {
  const { index } = dataOf(files);
  const id = route.id;
  const models = modelsInOrder(index).map((m) => {
    const path = index.files.grid[m.key]?.[id];
    if (path === undefined) throw new Error(`cards: the index lists no file for ${m.key} on ${id}`);
    const file = files[path] as GridFile | undefined;
    if (file === undefined) throw new Error(`cards: ${path} is not among the files`);
    return { ...m, path, file };
  });
  if (models.length !== 2) throw new Error("cards: the scenario card shows two models side by side");
  const [one, two] = models as [(typeof models)[number], (typeof models)[number]];

  // Both models side by side, never pooled (planning/07 section 1), the main model first: its name, then its valid
  // runs of attempted.
  const modelCell = (m: typeof one, x: number, width: number): Cell =>
    cell(x, width, [
      paragraph(
        "strong",
        [
          modelNameRun(files, m.at),
          labelRun(files, {
            key: "capValidOfAttempted",
            args: [
              { data: { file: m.path, path: "descriptive.runs" } },
              { data: { file: m.path, path: "objective_rates", via: "attemptedRuns" } },
            ],
          }),
        ],
        { joiner: ": " },
      ),
    ]);

  const verdictCell = (m: typeof one, first: string, second: string, slot: typeof COL_ONE): Cell => {
    const at = m.file.comparisons.findIndex((c) => c.first === first && c.second === second);
    if (at === -1) throw new Error(`cards: ${m.path} has no ${first} vs ${second}`);
    return cell(slot.x, slot.width, [
      paragraph("strong", [
        labelRun(files, {
          key: "verdictWords",
          select: { file: m.path, path: `comparisons.${at}.final_verdict` },
        }),
      ]),
    ]);
  };

  const rows: Block[] = SENTENCE_ORDER.map(([first, second], i) => {
    const at = one.file.comparisons.findIndex((c) => c.first === first && c.second === second);
    if (at === -1) throw new Error(`cards: ${one.path} has no ${first} vs ${second}`);
    const pair = (path: string) => ({ data: { file: one.path, path: `comparisons.${at}.${path}` } });
    const name = (path: string): Arg => ({
      label: { key: "objectiveNames", select: { file: one.path, path: `comparisons.${at}.${path}` } },
    });
    const labelParagraphs = [
      paragraph("cell", [
        labelRun(files, {
          key: "storyPairHeading",
          args: [name("first"), pair("first"), name("second"), pair("second")],
        }),
      ]),
    ];
    // C vs D carries the flag for the pair the Roundtable's claim is about, and no other row does.
    if (first === "C" && second === "D") {
      labelParagraphs.push(paragraph("flag", [labelRun(files, { key: "roundtableFlag" })]));
    }
    return {
      gap: i === 0 ? 8 : 7,
      divider: true,
      cells: [
        cell(COL_LABEL.x, COL_LABEL.width, labelParagraphs),
        verdictCell(one, first, second, COL_ONE),
        verdictCell(two, first, second, COL_TWO),
      ],
    };
  });

  return {
    route,
    blocks: [
      headerRow(files, route),
      full(16, paragraph("prose", [hisRun(`scenarioBriefs.${id}`)])),
      { gap: 20, cells: [modelCell(one, LEFT, 540), modelCell(two, LEFT + 564, 524)] },
      {
        gap: 16,
        divider: true,
        cells: [
          cell(COL_ONE.x, COL_ONE.width, [paragraph("flag", [modelNameRun(files, one.at)])]),
          cell(COL_TWO.x, COL_TWO.width, [paragraph("flag", [modelNameRun(files, two.at)])]),
        ],
      },
      ...rows,
      scope(),
    ],
  };
}

/** The label of every reading of a case file, as the cases page and the story's last beat show it for a model. */
function readingParagraph(files: CardFiles, path: string): Paragraph {
  const file = files[path] as CaseFile | undefined;
  if (file === undefined) throw new Error(`cards: ${path} is not among the files`);
  const same = labelUnderEveryReading(file);
  if (same === null) return paragraph("cell", [labelRun(files, { key: "storyLabelVaries" })]);
  // The label itself, after the model's name and ": " (no "Label:" of its own: section 29b).
  return paragraph("cell", [
    labelRun(files, { key: "readingLabels", select: { file: path, path: "readings.0.label" } }),
  ]);
}

function casePaths(index: DataIndex, label: string): Array<{ key: string; at: number; path: string }> {
  return modelsInOrder(index).map((m) => {
    const path = index.files.case_results[label]?.[m.key];
    if (path === undefined) throw new Error(`cards: the index lists no file for ${label} on ${m.key}`);
    return { ...m, path };
  });
}

function casesCard(files: CardFiles, route: PageRoute): Card {
  const { index, casesIndex } = dataOf(files);
  const casesFile = index.files.cases;
  // The exploratory label first, each distinct one verbatim, as the cases page and the story's last beat show it.
  const seen = new Set<string>();
  const labels: Block[] = [];
  casesIndex.cases.forEach((entry, at) => {
    if (seen.has(entry.exploratory_label)) return;
    seen.add(entry.exploratory_label);
    labels.push(
      full(
        labels.length === 0 ? 14 : 8,
        paragraph("label", [dataRun(files, { file: casesFile, path: `cases.${at}.exploratory_label` })], {
          rule: true,
        }),
      ),
    );
  });

  const everyFile = casesIndex.cases.flatMap((entry) =>
    casePaths(index, entry.label).map((m) => files[m.path] as CaseFile),
  );
  const body: Block[] = [];
  if (everyReadingNoGoodMatch(everyFile)) {
    body.push(full(14, paragraph("strong", [labelRun(files, { key: "allNoGoodMatch" })])));
    const each = WIDTH / casesIndex.cases.length;
    body.push({
      gap: 10,
      cells: casesIndex.cases.map((_, at) =>
        cell(LEFT + each * at, each, [
          paragraph("cell", [dataRun(files, { file: casesFile, path: `cases.${at}.label` })]),
        ]),
      ),
    });
  } else {
    casesIndex.cases.forEach((entry, at) => {
      const found = casePaths(index, entry.label);
      body.push({
        gap: 8,
        divider: true,
        cells: [
          cell(LEFT, 170, [
            paragraph("strong", [dataRun(files, { file: casesFile, path: `cases.${at}.label` })]),
          ]),
          ...found.map((m, i) =>
            cell(LEFT + 190 + i * 450, 440, [
              paragraph("cell", [modelNameRun(files, m.at), ...readingParagraph(files, m.path).runs], {
                joiner: ": ",
              }),
            ]),
          ),
        ],
      });
    });
  }
  return { route, blocks: [headerRow(files, route), ...labels, ...body, scope()] };
}

function caseCard(files: CardFiles, route: PageRoute & { kind: "case" }): Card {
  const { index, casesIndex } = dataOf(files);
  const casesFile = index.files.cases;
  const at = casesIndex.cases.findIndex((c) => c.label === route.label);
  const entry = casesIndex.cases[at];
  if (entry === undefined) throw new Error(`cards: ${casesFile} has no case ${route.label}`);
  // The description exactly as `Description` shows it: its text when published, otherwise its status.
  const description =
    entry.description.status === "published" && entry.description.text !== undefined
      ? dataRun(files, { file: casesFile, path: `cases.${at}.description.text` })
      : labelRun(files, {
          key: "caseDescriptionStatus",
          args: [{ data: { file: casesFile, path: `cases.${at}.description.status` } }],
        });
  const readings = casePaths(index, route.label).map((m) => ({
    gap: 8,
    divider: true,
    cells: [
      cell(LEFT, WIDTH, [
        paragraph("cell", [modelNameRun(files, m.at), ...readingParagraph(files, m.path).runs], {
          joiner: ": ",
        }),
      ]),
    ],
  }));
  return {
    route,
    blocks: [
      headerRow(files, route),
      full(
        16,
        paragraph("label", [dataRun(files, { file: casesFile, path: `cases.${at}.exploratory_label` })], {
          rule: true,
        }),
      ),
      full(18, paragraph("prose", [description])),
      ...readings.map((block, i) => (i === 0 ? { ...block, gap: 26 } : block)),
      scope(),
    ],
  };
}

function studiesCard(files: CardFiles, route: PageRoute): Card {
  return {
    route,
    blocks: [
      ...headerStack(files, route),
      full(34, paragraph("headline", [hisRun("pages.studies.description")])),
      scope(),
    ],
  };
}

function memosCard(files: CardFiles, route: PageRoute): Card {
  return {
    route,
    blocks: [
      ...headerStack(files, route),
      full(34, paragraph("headline", [hisRun("pages.memos.description")])),
      full(30, paragraph("strong", [labelRun(files, { key: "cardMemoLabel" })])),
      scope(),
    ],
  };
}

/** The card of one route, as runs. Throws when anything it reads is missing, so a build never draws a half card. */
export function buildCard(route: PageRoute, files: CardFiles): Card {
  switch (route.kind) {
    case "story":
      return storyCard(files, route);
    case "scenario":
      return scenarioCard(files, route);
    case "cases":
      return casesCard(files, route);
    case "case":
      return caseCard(files, route);
    case "studies":
      return studiesCard(files, route);
    case "memos":
      return memosCard(files, route);
  }
}

/** Every run of a card, in reading order: block by block, cell by cell, paragraph by paragraph. */
export function cardRuns(card: Card): Run[] {
  return card.blocks.flatMap((b) => b.cells.flatMap((c) => c.paragraphs.flatMap((p) => p.runs)));
}

/** The text of a paragraph: its runs between its joiner. */
export function paragraphText(p: Paragraph): string {
  return p.runs.map((r) => r.text).join(p.joiner ?? " ");
}

/** Every data file the cards read, by its path under explorer-data/: the index, the cases index, and the files they list. */
export function collectCardFiles(readJson: (relative: string) => unknown): Record<string, unknown> {
  const files: Record<string, unknown> = {};
  const take = (relative: string) => {
    files[relative] = readJson(relative);
  };
  take("index.json");
  const index = files["index.json"] as DataIndex;
  take(index.files.cases);
  for (const byScenario of Object.values(index.files.grid))
    for (const path of Object.values(byScenario)) take(path);
  for (const byModel of Object.values(index.files.case_results))
    for (const path of Object.values(byModel)) take(path);
  return files;
}

// ---------------------------------------------------------------------------------------------------------------------
// Layout: wrap by measurement, then place. `measure` is resvg's (write-cards.mjs): the width of one line of text.

export type Measure = (text: string, style: StyleName) => number;

export interface PlacedLine {
  block: number;
  cell: number;
  paragraph: number;
  text: string;
  style: StyleName;
  x: number;
  /** The baseline. */
  y: number;
  anchor: "start" | "end";
  /** The measured width of this line, and the width of the box it had to fit. */
  width: number;
  maxWidth: number;
}

export interface Bar {
  x: number;
  y: number;
  width: number;
  height: number;
  kind: "rule" | "divider";
}

export interface Layout {
  lines: PlacedLine[];
  bars: Bar[];
  /** The lowest edge of any text, including its descent. */
  bottom: number;
}

const DESCENT = 0.26;
const ASCENT = 0.8;

/**
 * Greedy word wrap: each line takes as many words as fit, found by measuring candidate lines (a binary search over how
 * many words), never by counting characters. A word wider than the box stands alone on its line.
 */
export function wrap(text: string, style: StyleName, maxWidth: number, measure: Measure): string[] {
  const words = text.split(" ").filter((w) => w !== "");
  const lines: string[] = [];
  let start = 0;
  while (start < words.length) {
    // The most words, from `start`, whose line fits; at least one.
    let low = 1;
    let high = words.length - start;
    while (low < high) {
      const middle = low + ((high - low + 1) >> 1); // the upper middle, in whole words
      if (measure(words.slice(start, start + middle).join(" "), style) <= maxWidth) low = middle;
      else high = middle - 1;
    }
    lines.push(words.slice(start, start + low).join(" "));
    start = start + low;
  }
  return lines;
}

/** How tall a block is: its tallest cell, each paragraph its wrapped lines at the style's line height. */
function blockHeight(block: Block, measure: Measure): number {
  let tallest = 0;
  for (const c of block.cells) {
    let height = 0;
    for (const p of c.paragraphs) {
      const style = STYLES[p.style];
      const indent = p.rule === true ? RULE_INDENT : 0;
      const count = wrap(paragraphText(p), p.style, c.width - indent, measure).length;
      height = height + count * style.size * style.lineHeight;
    }
    if (height > tallest) tallest = height;
  }
  return tallest;
}

export function layoutCard(card: Card, measure: Measure): Layout {
  const lines: PlacedLine[] = [];
  const bars: Bar[] = [];
  let bottom = 0;
  let top = TOP;
  card.blocks.forEach((block, b) => {
    let blockTop = top + block.gap;
    if (block.pin === "bottom") {
      if (b !== card.blocks.length - 1)
        throw new Error("cards: only the last block can be pinned to the foot");
      const pinned = BOTTOM_LIMIT - blockHeight(block, measure);
      if (pinned < top + PIN_CLEARANCE) blockTop = top + PIN_CLEARANCE;
      else blockTop = pinned;
      // The line above the scope sentence replaces the last table row's own line, so there are not two.
      if (bars[bars.length - 1]?.kind === "divider") bars.pop();
      bars.push({ x: LEFT, y: blockTop - 14, width: WIDTH, height: 1, kind: "divider" });
    }
    let blockBottom = blockTop;
    block.cells.forEach((c, ci) => {
      let y = blockTop;
      c.paragraphs.forEach((p, pi) => {
        const style = STYLES[p.style];
        const indent = p.rule === true ? RULE_INDENT : 0;
        const maxWidth = c.width - indent;
        const height = style.size * style.lineHeight;
        const paragraphTop = y;
        for (const text of wrap(paragraphText(p), p.style, maxWidth, measure)) {
          const baseline = y + (height - style.size) / 2 + style.size * ASCENT;
          const end = c.align === "end";
          lines.push({
            block: b,
            cell: ci,
            paragraph: pi,
            text,
            style: p.style,
            x: end ? c.x + c.width : c.x + indent,
            y: baseline,
            anchor: end ? "end" : "start",
            width: measure(text, p.style),
            maxWidth,
          });
          const descent = baseline + style.size * DESCENT;
          if (descent > bottom) bottom = descent;
          y = y + height;
        }
        if (p.rule === true) {
          bars.push({ x: c.x, y: paragraphTop + 2, width: 4, height: y - paragraphTop - 4, kind: "rule" });
        }
      });
      if (y > blockBottom) blockBottom = y;
    });
    if (block.divider === true) {
      bars.push({ x: LEFT, y: blockBottom + 2, width: WIDTH, height: 1, kind: "divider" });
    }
    top = blockBottom;
  });
  return { lines, bars, bottom };
}

/** Throws unless every line fits its box and nothing runs past the card's lower edge. */
export function assertFits(card: Card, layout: Layout): void {
  const where = `the card of ${card.route.kind}`;
  for (const line of layout.lines) {
    if (line.width > line.maxWidth + 0.01) {
      throw new Error(`cards: ${where}: "${line.text}" is ${line.width}px wide in a ${line.maxWidth}px box`);
    }
  }
  if (layout.bottom > BOTTOM_LIMIT) {
    throw new Error(`cards: ${where} runs to ${layout.bottom}px, past ${BOTTOM_LIMIT}px`);
  }
}

// ---------------------------------------------------------------------------------------------------------------------
// The SVG.

export function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

const px = (n: number): string => String(Number(n.toFixed(2)));

function textAttributes(style: TextStyle): string {
  return `font-family="'${style.family}'" font-weight="${style.weight}" font-size="${style.size}" fill="${style.fill}"`;
}

/** One line of text on its own, for measuring it: resvg's bounding box of this is the line's width. */
export function measureSvg(text: string, style: StyleName): string {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${CARD_WIDTH * 2}" height="${CARD_HEIGHT}">` +
    `<text x="0" y="${CARD_HEIGHT / 2}" ${textAttributes(STYLES[style])}>${escapeXml(text)}</text></svg>`
  );
}

/** The card as SVG. Its text is the layout's lines and nothing else; `data-block` ties a line to its block. */
export function cardSvg(layout: Layout): string {
  const parts: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" width="${CARD_WIDTH}" height="${CARD_HEIGHT}" viewBox="0 0 ${CARD_WIDTH} ${CARD_HEIGHT}">`,
    `<rect width="${CARD_WIDTH}" height="${CARD_HEIGHT}" fill="${PALETTE.surface}"/>`,
    `<rect width="14" height="${CARD_HEIGHT}" fill="${PALETTE.sun}"/>`,
  ];
  for (const bar of layout.bars) {
    const fill = bar.kind === "rule" ? PALETTE.ink : PALETTE.grid;
    parts.push(
      `<rect x="${px(bar.x)}" y="${px(bar.y)}" width="${px(bar.width)}" height="${px(bar.height)}" fill="${fill}"/>`,
    );
  }
  for (const line of layout.lines) {
    const anchor = line.anchor === "end" ? ' text-anchor="end"' : "";
    parts.push(
      `<text data-block="${line.block}" x="${px(line.x)}" y="${px(line.y)}"${anchor} ${textAttributes(STYLES[line.style])}>${escapeXml(line.text)}</text>`,
    );
  }
  parts.push("</svg>");
  return parts.join("\n");
}
