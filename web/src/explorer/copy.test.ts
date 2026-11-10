import { describe, expect, it } from "vitest";
import { isPlaceholder, PLACEHOLDER_MARK } from "../copy";
import { explorerHis, explorerLabels } from "./copy";
import { allRoutes } from "./page-meta.mjs";
import { MEMO_KINDS } from "./route";
import {
  readAwareness,
  readMemoRows,
  realCaseFiles,
  realCasesIndex,
  realGrids,
  realIndex,
  realMemoIndex,
} from "./fixtures";

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

// Keyed maps are tested against the data, never the other way round: a key the data has and the labels lack fails
// here, so no bare key reaches the page.
describe("the labels keyed by the data", () => {
  const scenarios = realIndex.scenarios.map((s) => s.scenario_id);

  it("name every model in the index, in an order of their own, and no model the index lacks", () => {
    const labelled = explorerLabels.models.map((m) => m.key);
    expect(new Set(labelled)).toEqual(new Set(realIndex.models.map((m) => m.model_key)));
    expect(labelled).toHaveLength(new Set(labelled).size);
    expect(labelled[0]).toBe("haiku-5-5"); // the default comes first
    for (const model of explorerLabels.models) expect(model.name.trim()).not.toBe("");
  });

  it("name every goal in the index", () => {
    for (const objective of realIndex.objectives) {
      expect(explorerLabels.objectiveNames[objective.id], objective.id).toBeTruthy();
    }
  });

  it("hold an outcome phrase for every scenario", () => {
    for (const id of scenarios) expect(explorerLabels.outcomePhrases[id], id).toBeTruthy();
  });

  it("hold axis words and a key for every share scenario", () => {
    for (const s of realIndex.scenarios.filter((x) => x.kind === "share")) {
      const ends = explorerLabels.axisEnds[s.scenario_id];
      expect(ends, s.scenario_id).toBeDefined();
      for (const word of [ends!.title, ends!.low, ends!.mid, ends!.high]) expect(word.trim()).not.toBe("");
      expect(explorerLabels.shareKey[s.scenario_id], s.scenario_id).toBeTruthy();
    }
  });

  it("hold a label for every choice and every lever in every real file", () => {
    const choices = new Set<string>();
    const levers = new Set<string>();
    const leversOfS4 = new Set<string>();
    for (const { file } of realGrids) {
      for (const split of file.descriptive.choice_splits)
        for (const [choice] of split.counts) choices.add(choice);
      for (const run of file.descriptive.per_run) {
        if (run.choice !== null) choices.add(run.choice);
        for (const [lever] of run.shares) levers.add(lever);
      }
      for (const cell of file.descriptive.cells) {
        if (cell.choice !== null) choices.add(cell.choice);
        for (const line of cell.lines) {
          levers.add(line.key);
          if (file.scenario_id === "s4") leversOfS4.add(line.key);
        }
      }
    }
    expect(leversOfS4.size).toBe(15); // s4 is the scenario with the long menu
    for (const choice of choices) expect(explorerLabels.choices[choice], `choice ${choice}`).toBeTruthy();
    for (const lever of levers) expect(explorerLabels.levers[lever], `lever ${lever}`).toBeTruthy();
  });

  it("hold the four verdict words", () => {
    for (const verdict of ["split", "no_split", "inconclusive", "not_assessable"]) {
      expect(explorerLabels.verdictWords[verdict], verdict).toBeTruthy();
    }
  });

  it("carry a written brief or a placeholder for every scenario, and the section's title and introduction", () => {
    for (const id of scenarios) expect(explorerHis.scenarioBriefs[id], id).toBeTruthy();
    expect(explorerHis.againstTitle).toBeTruthy();
    expect(explorerHis.againstIntro).toBeTruthy();
  });
});

describe("the labels keyed by the C5 data", () => {
  it("hold a word for every label the matcher can write, and every one in the real case files", () => {
    // matcher.py: Label = match | tie | no_good_match | not_enough_disclosed.
    for (const label of ["match", "tie", "no_good_match", "not_enough_disclosed"]) {
      expect(explorerLabels.readingLabels[label], label).toBeTruthy();
    }
    const found = new Set(realCaseFiles.flatMap((c) => c.file.readings.map((r) => r.label)));
    expect(found.size).toBeGreaterThan(0);
    for (const label of found) expect(explorerLabels.readingLabels[label], label).toBeTruthy();
    expect(Object.keys(explorerLabels.readingLabels).sort()).toEqual([
      "match",
      "no_good_match",
      "not_enough_disclosed",
      "tie",
    ]);
  });

  it("name the primary reading, and every case type and every kind of memo set", () => {
    expect(explorerLabels.readingNames["primary"]).toBeTruthy();
    expect(explorerLabels.readingAlternative("u1")).toContain("u1");
    const types = new Set([
      ...Object.keys(realCasesIndex.shortfall.cases_by_type),
      ...Object.keys(realCasesIndex.shortfall.short_by_type),
      ...realCasesIndex.cases.map((c) => c.type),
    ]);
    for (const type of types) expect(explorerLabels.caseTypes[type], type).toBeTruthy();
    for (const kind of MEMO_KINDS) expect(explorerLabels.memoKinds[kind], kind).toBeTruthy();
  });

  it("label every choice, lever and dimension in the real case files", () => {
    for (const { file } of realCaseFiles) {
      expect(explorerLabels.choices[file.company.choice]).toBeTruthy();
      for (const reading of [file.company, ...file.company_alternatives]) {
        for (const lever of Object.keys(reading.shares))
          expect(explorerLabels.levers[lever], lever).toBeTruthy();
      }
      for (const key of [
        ...file.dimensions.observable,
        ...file.dimensions.excluded,
        ...file.readings.flatMap((r) => r.observable_lines),
      ]) {
        expect(key === "choice" || explorerLabels.levers[key], key).toBeTruthy();
      }
    }
  });

  it("word every reason a memo is held, and every count the cases page shows", () => {
    for (const { file } of realCaseFiles) {
      for (const reason of Object.keys(file.memo_counts.held_by_reason)) {
        expect(explorerLabels.heldReasons[reason], reason).toBeTruthy();
      }
    }
    expect(Object.keys(explorerLabels.memoCountLabels)).toEqual([
      "runs",
      "with_text",
      "without_text",
      "published",
      "held",
    ]);
  });

  it("word every source a memo can have, and every reason the reader can refuse a choice", () => {
    const sources = new Set<string>();
    for (const file of realMemoIndex.files.slice(0, 8))
      for (const row of readMemoRows(file)) if (row.source !== null) sources.add(row.source);
    expect(sources.size).toBeGreaterThan(0);
    for (const source of [...sources, "memo", "reply_text"])
      expect(explorerLabels.memoSources[source], source).toBeTruthy();
    for (const why of ["kind", "scenario", "objective", "cell", "run"])
      expect(explorerLabels.memoMessages[why], why).toBeTruthy();
  });

  it("hold a title for each part of the studies page, and the introductions, as placeholders that name what goes there", () => {
    for (const key of [
      "memosIntro",
      "casesIntro",
      "caseMemosHeld",
      "studiesIntro",
      "studiesThinkingTitle",
      "studiesAwarenessTitle",
    ] as const) {
      expect(isPlaceholder(explorerHis[key]), key).toBe(true);
    }
  });

  it("have an awareness file for every model in the index, with fifteen calls each", () => {
    for (const model of realIndex.models.map((m) => m.model_key)) {
      const file = readAwareness(model);
      expect(file.model_key).toBe(model);
      expect(file.calls).toHaveLength(15);
    }
  });
});
