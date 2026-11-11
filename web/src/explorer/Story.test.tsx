import { cleanup, render, waitFor, within } from "@testing-library/react";
import type { RenderResult } from "@testing-library/react";
import axe from "axe-core";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { everyReadingNoGoodMatch } from "./caseData";
import { SENTENCE_ORDER, findComparison, orderedComparisons } from "./chartData";
import { explorerHis, explorerLabels as L } from "./copy";
import type { DataApi, GridFile } from "./data";
import { createDataApi } from "./data";
import { fileFetcher, realApi, realCaseFiles, realCasesIndex, realGrids, realIndex } from "./fixtures";
import { attemptedRuns, comparisonRuns, confidenceLevel } from "./format";
import { ROUNDTABLE_CLAIM_URL, ROUNDTABLE_OVERVIEW_URL, protocolUrl } from "./links";
import { modelName, orderedModels } from "./models";
import { PROTOCOL_READINGS, readingFor } from "./protocol";
import { resultSentence, TEMPLATE_IDS } from "./sentences";
import { Story } from "./Story";

const MODELS = orderedModels(realIndex.models).map((m) => m.model_key);
const MAIN = MODELS[0]!;
const gridOf = (model: string, scenario: string): GridFile =>
  realGrids.find((g) => g.label === `grid ${model} ${scenario}`)!.file;

const BEATS = [
  "beat-question",
  "beat-setup",
  "beat-s1",
  "beat-comparisons",
  "beat-second-model",
  "beat-other-scenarios",
  "against-the-thesis",
  "beat-cases",
  "beat-methods",
];

function renderStory(data: DataApi, onSettled?: () => void): RenderResult {
  return render(<Story index={realIndex} casesIndex={realCasesIndex} data={data} onSettled={onSettled} />);
}

async function loaded(rendered: RenderResult): Promise<void> {
  await waitFor(() => expect(rendered.container.querySelectorAll(".story-wait")).toHaveLength(0));
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2); the headless capture runs axe-core in a real browser, contrast included.
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

const beat = (container: HTMLElement, id: string) => container.querySelector<HTMLElement>(`section#${id}`)!;

describe("the story, from the real files", () => {
  const requested: string[] = [];
  const settled = vi.fn();
  let rendered: RenderResult;
  let container: HTMLElement;
  let errors: ReturnType<typeof vi.spyOn>;
  let warnings: ReturnType<typeof vi.spyOn>;

  beforeAll(async () => {
    errors = vi.spyOn(console, "error").mockImplementation(() => {});
    warnings = vi.spyOn(console, "warn").mockImplementation(() => {});
    rendered = renderStory(realApi(requested), settled);
    container = rendered.container;
    await loaded(rendered);
  });
  afterAll(() => {
    cleanup();
    errors.mockRestore();
    warnings.mockRestore();
  });

  it("renders without a console error or warning, and reports once that every beat has its data", async () => {
    await waitFor(() => expect(settled).toHaveBeenCalledTimes(1));
    expect(errors).not.toHaveBeenCalled();
    expect(warnings).not.toHaveBeenCalled();
  });

  it("has the nine sections, with exactly these ids, in this order", () => {
    expect([...container.querySelectorAll("section[id]")].map((s) => s.id)).toEqual(BEATS);
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    // Beat 1's heading is the page's h1; every other beat has an h2 that names it.
    for (const id of BEATS.slice(1)) {
      const section = beat(container, id);
      const heading = section.querySelector(":scope > h2")!;
      expect(section.getAttribute("aria-labelledby"), id).toBe(heading.id);
    }
    expect(beat(container, "beat-question").getAttribute("aria-labelledby")).toBe(
      container.querySelector("h1")!.id,
    );
  });

  it("walks s1 on the main model, which is Haiku 5.5, with the second model the other one", () => {
    expect(MAIN).toBe("haiku-5-5");
    expect(MODELS).toHaveLength(2);
    expect(realIndex.scenarios[0]!.scenario_id).toBe("s1");
    const figure = beat(container, "beat-s1").querySelector("figure")!;
    expect(figure.querySelector("[role=img]")!.getAttribute("aria-label")).toContain("scenario s1");
    expect(figure.textContent).toContain(modelName(MAIN));
  });

  it("opens with the question and the name line, and the setup with the five goals and the scope sentence", () => {
    const first = beat(container, "beat-question");
    expect(first.textContent).toContain(explorerHis.landingQuestion);
    expect(first.textContent).toContain(explorerHis.storyName);
    const setup = beat(container, "beat-setup");
    expect(setup.querySelectorAll(".x-goals li")).toHaveLength(5);
    for (const o of realIndex.objectives) {
      expect(setup.textContent).toContain(L.objectiveNames[o.id]!);
      expect(setup.textContent).toContain(o.who === null ? L.goalUnstated : L.goalTold(o.who, o.when));
    }
    expect(setup.textContent).toContain(explorerHis.scopeSentence);
  });

  it("states no result in beats 1 and 2: no verdict word, no result sentence, no template", () => {
    for (const id of ["beat-question", "beat-setup"]) {
      const section = beat(container, id);
      expect(section.querySelectorAll("[data-template]"), id).toHaveLength(0);
      expect(section.querySelectorAll("svg"), id).toHaveLength(0);
      for (const word of Object.values(L.verdictWords)) expect(section.textContent, id).not.toContain(word);
    }
  });

  it("beat 3: the brief, the link to the full text, the chart card with every goal, and a link to the scenario", () => {
    const section = beat(container, "beat-s1");
    expect(section.textContent).toContain(explorerHis.scenarioBriefs["s1"]!);
    expect(section.querySelector(`a[href$="experiment/company/scenarios/s1.toml"]`)).not.toBeNull();
    expect(section.querySelectorAll("figure.card")).toHaveLength(1);
    expect(section.querySelectorAll(".goal-row[data-goal]")).toHaveLength(5);
    expect(section.querySelectorAll(".goal-row[data-off=true]")).toHaveLength(0); // no toggles in the story
    expect(section.querySelectorAll("button")).toHaveLength(0);
    expect(section.querySelector('a[href="/scenario/s1/"]')).not.toBeNull();
  });

  it("every figure keeps the model, the valid runs of those attempted and the scope sentence, so a crop keeps them", () => {
    const figures = [...container.querySelectorAll("figure.card")];
    // beat 3: 1; beat 4: 5; beat 5: 2.
    expect(figures).toHaveLength(1 + 5 + 2);
    for (const figure of figures) {
      const model = MODELS.find((m) => figure.textContent!.includes(modelName(m)));
      expect(model, figure.textContent!.slice(0, 60)).toBeDefined();
      const file = gridOf(model!, "s1");
      expect(figure.textContent).toContain(
        L.capValidOfAttempted(file.descriptive.runs, attemptedRuns(file.objective_rates)),
      );
      expect(figure.textContent).toContain(explorerHis.scopeSentence);
      expect(figure.querySelector("figcaption")).not.toBeNull();
    }
  });

  describe("beat 4, the comparisons", () => {
    const file = gridOf(MAIN, "s1");
    const blocks = () => [
      ...beat(container, "beat-comparisons").querySelectorAll<HTMLElement>("li.story-comparison"),
    ];

    it("has one block per comparison in the sentence column's order, C vs D first", () => {
      expect(blocks().map((b) => b.dataset["pair"])).toEqual(SENTENCE_ORDER.map(([a, b]) => `${a}-${b}`));
    });

    it("gives each block its goals by plain name and letter, its template sentence, a one-row chart, its runs, its verdict and its headline verbatim", () => {
      for (const block of blocks()) {
        const [first, second] = block.dataset["pair"]!.split("-") as [string, string];
        const c = findComparison(file, first, second)!;
        expect(block.querySelector("h3")!.textContent).toBe(
          L.storyPairHeading(L.objectiveNames[first]!, first, L.objectiveNames[second]!, second),
        );
        const sentence = block.querySelector<HTMLElement>(".result-sentence")!;
        const expected = resultSentence(c, L.objectiveNames, L.outcomePhrases["s1"]!);
        expect(sentence.dataset["template"]).toBe(expected.id);
        expect(sentence.textContent).toBe(expected.text);
        expect(block.querySelectorAll(".interval-row:not(.interval-axis)")).toHaveLength(1);
        const fine = block.querySelector(".fine")!.textContent!;
        if (c.final_verdict === "not_assessable") expect(fine).toContain(L.noRunsCompared);
        else {
          const runs = comparisonRuns(c);
          expect(fine).toContain(L.runsPair(runs.first, runs.second));
        }
        expect(fine).toContain(`${L.officialVerdict} ${L.verdictWords[c.final_verdict]}`);
        expect(block.textContent).toContain(c.headline);
      }
    });

    it("names C vs D as the test of the Roundtable's claim, and no other pair", () => {
      const labelled = blocks().filter((b) => b.textContent!.includes(L.roundtableFlag));
      expect(labelled.map((b) => b.dataset["pair"])).toEqual(["C-D"]);
    });

    it("links to the two outside pages on the Roundtable, in a new tab, before the first comparison", () => {
      const section = beat(container, "beat-comparisons");
      const list = section.querySelector<HTMLElement>('[data-sources="roundtable"]')!;
      const links = [...list.querySelectorAll("a")];
      expect(links.map((a) => [a.getAttribute("href"), a.textContent])).toEqual([
        [ROUNDTABLE_OVERVIEW_URL, L.storyRoundtableOverview],
        [ROUNDTABLE_CLAIM_URL, L.storyRoundtableClaim],
      ]);
      for (const a of links) {
        expect(a.getAttribute("target")).toBe("_blank");
        expect(a.getAttribute("rel")).toBe("noopener noreferrer");
      }
      const first = blocks()[0]!;
      expect(list.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    });

    it("quotes the protocol's reading wherever readingFor gives one, as written, and writes none of its own", () => {
      const cd = findComparison(file, "C", "D")!.final_verdict;
      for (const block of blocks()) {
        const [first, second] = block.dataset["pair"]!.split("-") as [string, string];
        const c = findComparison(file, first, second)!;
        const key = readingFor(first, second, c.final_verdict, cd);
        const quoted = block.querySelector<HTMLElement>("blockquote.reading");
        if (key === null) expect(quoted, block.dataset["pair"]).toBeNull();
        else {
          expect(quoted!.dataset["reading"]).toBe(key);
          expect(quoted!.textContent).toContain(PROTOCOL_READINGS[key].reading);
        }
      }
      const section = beat(container, "beat-comparisons");
      expect(section.textContent).toContain(L.readingsNote);
      expect(section.querySelectorAll(".protocol-none").length).toBeLessThanOrEqual(1);
    });

    it("says the interval level from the file's alpha and the verdict note once, before the first block", () => {
      const section = beat(container, "beat-comparisons");
      const level = confidenceLevel(realIndex.models.find((m) => m.model_key === MAIN)!.alpha);
      const text = section.textContent!;
      expect(text).toContain(L.verdictNote(level));
      expect(text).toContain(L.intervalKey(level));
      expect(text.split(L.verdictNote(level))).toHaveLength(2);
      expect(text.indexOf(L.verdictNote(level))).toBeLessThan(text.indexOf(blocks()[0]!.textContent!));
    });
  });

  describe("beat 5, the second model", () => {
    const section = () => beat(container, "beat-second-model");

    it("shows both models' s1 comparisons, the main model first, each five rows and five template sentences", () => {
      const columns = [...section().querySelectorAll<HTMLElement>(".story-model")];
      expect(columns.map((c) => c.dataset["model"])).toEqual(MODELS);
      for (const column of columns) {
        const file = gridOf(column.dataset["model"]!, "s1");
        expect(column.querySelectorAll(".interval-row:not(.interval-axis)")).toHaveLength(5);
        const sentences = [...column.querySelectorAll<HTMLElement>("li.sent")];
        expect(sentences.map((li) => li.dataset["pair"])).toEqual(
          SENTENCE_ORDER.map(([a, b]) => `${a}-${b}`),
        );
        for (const li of sentences) {
          const [first, second] = li.dataset["pair"]!.split("-") as [string, string];
          const expected = resultSentence(
            findComparison(file, first, second)!,
            L.objectiveNames,
            L.outcomePhrases["s1"]!,
          );
          const element = li.querySelector<HTMLElement>(".result-sentence")!;
          expect(element.dataset["template"]).toBe(expected.id);
          expect(element.textContent).toBe(expected.text);
        }
      }
    });

    it("draws the two models' charts at the same size", () => {
      const widths = [...section().querySelectorAll(".story-model")].map((column) =>
        [...column.querySelectorAll(".chart.intervals svg.x-plot")].map((svg) => [
          svg.getAttribute("width"),
          svg.getAttribute("height"),
        ]),
      );
      expect(widths).toHaveLength(2);
      expect(widths[0]!.length).toBeGreaterThan(0);
      expect(widths[1]).toEqual(widths[0]);
    });
  });

  describe("beat 6, the other three scenarios", () => {
    it("has a cell for every comparison of every model in s2 to s4, and its verdict word is the file's final verdict", () => {
      let cells = 0;
      const seen = new Set<string>();
      for (const id of ["s2", "s3", "s4"]) {
        const table = beat(container, "beat-other-scenarios").querySelector<HTMLElement>(
          `table[data-scenario=${id}]`,
        )!;
        expect([...table.querySelectorAll("thead th")].slice(1).map((th) => th.textContent)).toEqual(
          MODELS.map(modelName),
        );
        expect(
          [...table.querySelectorAll("tbody tr")].map((tr) => (tr as HTMLElement).dataset["pair"]),
        ).toEqual(SENTENCE_ORDER.map(([a, b]) => `${a}-${b}`));
        for (const model of MODELS) {
          for (const c of orderedComparisons(gridOf(model, id))) {
            const cell = table.querySelector<HTMLElement>(
              `tr[data-pair=${c.first}-${c.second}] td[data-model="${model}"]`,
            )!;
            expect(cell.querySelector(".verdict-word")!.textContent, `${model} ${id}`).toBe(
              L.verdictWords[c.final_verdict],
            );
            expect(cell.dataset["verdict"]).toBe(c.final_verdict);
            const runs = comparisonRuns(c);
            expect(cell.textContent).toContain(
              c.final_verdict === "not_assessable" ? L.noRunsCompared : L.runsPair(runs.first, runs.second),
            );
            seen.add(c.final_verdict);
            cells += 1;
          }
        }
      }
      expect(cells).toBe(3 * 2 * 5);
      // Shown in place, never hidden: the real files have inconclusive and not-assessable verdicts, and they are here.
      expect(seen.has("inconclusive")).toBe(true);
      expect(seen.has("not_assessable")).toBe(true);
    });

    it("captions each table with the scope sentence, carries no color and no style, and links to each model's view", () => {
      for (const id of ["s2", "s3", "s4"]) {
        const table = beat(container, "beat-other-scenarios").querySelector<HTMLElement>(
          `table[data-scenario=${id}]`,
        )!;
        expect(table.querySelector("caption")!.textContent).toContain(explorerHis.scopeSentence);
        expect(table.querySelectorAll("[style], [class*=goal-]")).toHaveLength(0);
        const links = [...table.closest(".story-scenario")!.querySelectorAll("a")].map((a) =>
          a.getAttribute("href"),
        );
        expect(links).toEqual([`/scenario/${id}/`, `/scenario/${id}/?model=gpt-oss-openrouter`]);
      }
    });
  });

  it("beat 7 is the section for results against the thesis, with its id, listing the index's entries", () => {
    const section = beat(container, "against-the-thesis");
    expect(section.querySelectorAll("li.x-entry")).toHaveLength(realIndex.against_thesis.entries.length);
  });

  describe("beat 8, the real cases", () => {
    const section = () => beat(container, "beat-cases");

    it("puts the exploratory label before any reading, in document order", () => {
      const html = section();
      const first = html.querySelector("[data-exploratory-label]")!;
      const everyReading = [...html.querySelectorAll("[data-model], [data-sentence]")];
      expect(everyReading.length).toBeGreaterThan(0);
      for (const element of everyReading) {
        expect(
          first.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING,
          element.outerHTML,
        ).toBeTruthy();
      }
      const labels = [...html.querySelectorAll("[data-exploratory-label]")].map((e) => e.textContent);
      for (const entry of realCasesIndex.cases) expect(labels).toContain(entry.exploratory_label);
    });

    it("says every reading is no good match if and only if every reading of every file is", () => {
      const sentence = section().querySelector('[data-sentence="every-reading-no-good-match"]');
      expect(everyReadingNoGoodMatch(realCaseFiles.map((c) => c.file))).toBe(sentence !== null);
      if (sentence !== null) expect(sentence.textContent).toBe(L.allNoGoodMatch);
    });

    it("has one row per case in the index's order, each with the label, both models' labels and a link to the case", () => {
      const rows = [...section().querySelectorAll<HTMLElement>("li.case-card")];
      expect(rows.map((r) => r.dataset["case"])).toEqual(realCasesIndex.cases.map((c) => c.label));
      for (const row of rows) {
        const entry = realCasesIndex.cases.find((c) => c.label === row.dataset["case"])!;
        expect(row.querySelector("h3")!.textContent).toBe(entry.label);
        expect(row.querySelector("[data-exploratory-label]")!.textContent).toBe(entry.exploratory_label);
        expect(
          [...row.querySelectorAll("li[data-model]")].map((li) => (li as HTMLElement).dataset["model"]),
        ).toEqual(MODELS);
        expect(row.querySelector(`a[href="/cases/${entry.label}/"]`)).not.toBeNull();
      }
      const first = realCasesIndex.cases[0]!;
      const file = realCaseFiles.find((c) => c.label === first.label && c.model === MAIN)!.file;
      expect(
        within(rows[0]!).getAllByText(L.readingLabelIs(L.readingLabels[file.readings[0]!.label]!), {
          exact: false,
        }),
      ).not.toHaveLength(0);
    });

    it("shows the shortfall from the cases index, and a link to /cases/", () => {
      const facts = section().querySelector(".story-shortfall")!;
      for (const type of Object.keys(realCasesIndex.shortfall.cases_by_type)) {
        const row = facts.querySelector(`[data-type=${type}]`)!;
        expect(row.textContent).toContain(L.caseTypes[type]!);
        expect(row.textContent).toContain(
          `${L.shortfallFound}: ${realCasesIndex.shortfall.cases_by_type[type]}; ${L.shortfallShort}: ${realCasesIndex.shortfall.short_by_type[type]}`,
        );
      }
      expect(section().querySelector('a[href="/cases/"]')).not.toBeNull();
    });

    it("shows nothing of a case beyond its files' fields: no memo link, no run id, no case memo text", () => {
      expect(section().querySelectorAll('a[href*="/memos/"]')).toHaveLength(0);
      expect(section().querySelectorAll(".memo-card, .memo-text")).toHaveLength(0);
      expect(section().querySelectorAll("a")).toHaveLength(realCasesIndex.cases.length + 1); // a case link each, and /cases/
    });
  });

  it("beat 9 links to the protocol at the pre-registered tag, the studies and the memo reader", () => {
    const section = beat(container, "beat-methods");
    expect(section.querySelector(`a[href="${protocolUrl()}"]`)).not.toBeNull();
    expect(section.querySelector('a[href="/studies/"]')).not.toBeNull();
    expect(section.querySelector('a[href="/memos/"]')).not.toBeNull();
  });

  it("every result sentence in the story is a template's output, and its text is nowhere else as a bare string", () => {
    const sentences = [...container.querySelectorAll<HTMLElement>(".result-sentence")];
    // Beat 4: 5; beat 5: 2 x 5; beat 7 has none (it shows the analysis's own headline).
    expect(sentences).toHaveLength(5 + 10);
    for (const element of sentences) {
      expect(TEMPLATE_IDS as readonly string[]).toContain(element.dataset["template"]);
    }
    const texts = sentences.map((e) => e.textContent!);
    const clone = container.cloneNode(true) as HTMLElement;
    clone.querySelectorAll(".result-sentence").forEach((e) => e.remove());
    for (const text of texts) expect(clone.textContent).not.toContain(text);
  });

  it("uses no style attribute and no script, and puts no verdict in a color", () => {
    expect(container.querySelectorAll("[style]")).toHaveLength(0);
    expect(container.querySelectorAll("script")).toHaveLength(0);
  });

  it("fetches only from /data/, and nothing it does not show", () => {
    expect(requested.length).toBeGreaterThan(0);
    for (const path of requested) expect(path.startsWith("/data/"), path).toBe(true);
    expect(requested.filter((p) => p.includes("/memos/"))).toEqual([]);
    expect(requested.filter((p) => p.includes("/thinking/") || p.includes("awareness"))).toEqual([]);
  });

  it("carries a placeholder or his word for every story key, and none states a result", () => {
    expect(explorerHis.storyName).toBeTruthy();
    const keys = [
      "setupTitle",
      "setupIntro",
      "s1Title",
      "s1Intro",
      "comparisonsTitle",
      "comparisonsIntro",
      "secondTitle",
      "secondIntro",
      "othersTitle",
      "othersIntro",
      "casesTitle",
      "casesIntro",
      "methodsTitle",
      "methodsText",
    ] as const;
    expect(Object.keys(explorerHis.story).sort()).toEqual([...keys].sort());
    for (const key of keys) {
      const text = explorerHis.story[key];
      expect(text.trim(), key).not.toBe("");
      // Placeholder or written, no story line states a result (planning/06 section 6.1).
      expect(text, key).not.toMatch(/\b(split|no split|inconclusive|found that|showed that)\b/i);
    }
    expect(explorerHis.storyName).not.toMatch(/\b(split|no split|inconclusive|found that|showed that)\b/i);
  });

  it("has no axe violations with every beat's data loaded, at 1280 wide", async () => {
    window.innerWidth = 1280;
    expect(await violations(container)).toEqual([]);
  });

  it("has no axe violations with every beat's data loaded, at 390 wide", async () => {
    window.innerWidth = 390;
    expect(await violations(container)).toEqual([]);
  });
});

describe("the story's loading", () => {
  afterEach(cleanup);

  it("renders the first two beats at once, shows the loading line where data is on its way, then fills in", async () => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => (release = resolve));
    const base = fileFetcher();
    const data = createDataApi(async (path) => {
      if (path.includes("/grid/") || path.includes("/cases/")) await gate;
      return base(path);
    });
    const settled = vi.fn();
    const view = renderStory(data, settled);
    expect(view.container.querySelector("h1")).not.toBeNull(); // beats 1 and 2 are there on the first render
    expect(beat(view.container, "beat-setup").querySelectorAll(".x-goals li")).toHaveLength(5);
    expect(view.container.querySelectorAll('section#beat-s1 [role="status"]')).toHaveLength(1);
    expect(view.container.querySelector("section#against-the-thesis")).not.toBeNull(); // needs only the index
    expect(settled).not.toHaveBeenCalled();
    release();
    await loaded(view);
    await waitFor(() => expect(settled).toHaveBeenCalledTimes(1));
    expect(view.container.querySelector("section#beat-s1 figure")).not.toBeNull();
  });

  it("shows the failure line in the beat whose file did not load, not in the others, and still reports settled", async () => {
    const base = fileFetcher();
    const data = createDataApi(async (path) =>
      path.endsWith("/grid/gpt-oss-openrouter/s3.json")
        ? ({ ok: false, status: 500 } as Response)
        : base(path),
    );
    const settled = vi.fn();
    const view = renderStory(data, settled);
    await waitFor(() => expect(settled).toHaveBeenCalledTimes(1));
    expect(view.container.querySelectorAll('[role="alert"]')).toHaveLength(1);
    expect(beat(view.container, "beat-other-scenarios").querySelector('[role="alert"]')).not.toBeNull();
    expect(beat(view.container, "beat-s1").querySelector("figure")).not.toBeNull();
    expect(beat(view.container, "beat-second-model").querySelectorAll(".story-model")).toHaveLength(2);
    expect(beat(view.container, "beat-cases").querySelector("li.case-card")).not.toBeNull();
  });
});

describe("the entrance (motion)", () => {
  class FakeObserver {
    static all: FakeObserver[] = [];
    observed = new Set<Element>();
    constructor(readonly callback: IntersectionObserverCallback) {
      FakeObserver.all.push(this);
    }
    observe(target: Element) {
      this.observed.add(target);
    }
    unobserve(target: Element) {
      this.observed.delete(target);
    }
    disconnect() {
      this.observed.clear();
    }
    takeRecords() {
      return [];
    }
    emit(target: Element, isIntersecting: boolean, top: number) {
      this.callback(
        [
          {
            target,
            isIntersecting,
            boundingClientRect: { top } as DOMRectReadOnly,
          } as IntersectionObserverEntry,
        ],
        this as unknown as IntersectionObserver,
      );
    }
  }
  const withClass = (container: HTMLElement) => [...container.querySelectorAll(".beat-enter")];

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    FakeObserver.all = [];
  });

  it("gives no beat the class when there is no IntersectionObserver", async () => {
    vi.stubGlobal("IntersectionObserver", undefined);
    const view = renderStory(realApi());
    await loaded(view);
    expect(withClass(view.container)).toHaveLength(0);
  });

  it("gives no beat the class when the reader prefers reduced motion, and does not even observe", async () => {
    vi.stubGlobal("IntersectionObserver", FakeObserver);
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: query.includes("reduce"), media: query }));
    const view = renderStory(realApi());
    await loaded(view);
    expect(FakeObserver.all).toHaveLength(0);
    expect(withClass(view.container)).toHaveLength(0);
  });

  it("gives a beat below the first screen the class until it comes into view, and beat 1 never", async () => {
    vi.stubGlobal("IntersectionObserver", FakeObserver);
    vi.stubGlobal("matchMedia", (query: string) => ({ matches: false, media: query }));
    const view = renderStory(realApi());
    await loaded(view);
    const observer = FakeObserver.all[0]!;
    const observed = [...observer.observed].map((e) => e.id);
    expect(observed).toEqual(BEATS.slice(1)); // beat 1 is not observed at all
    const setup = beat(view.container, "beat-setup");
    const below = beat(view.container, "beat-second-model");
    observer.emit(setup, true, 300); // on the first screen: never gets the class
    observer.emit(below, false, 2400);
    expect(setup.classList.contains("beat-enter")).toBe(false);
    expect(below.classList.contains("beat-enter")).toBe(true);
    expect(withClass(view.container)).toEqual([below]);
    observer.emit(below, true, 600);
    expect(below.classList.contains("beat-enter")).toBe(false);
    expect(observer.observed.has(below)).toBe(false);
    // A beat already scrolled past (above the screen) is left alone.
    const past = beat(view.container, "beat-s1");
    observer.emit(past, false, -900);
    expect(past.classList.contains("beat-enter")).toBe(false);
    // A beat whose top is on the first screen, in the root margin's bottom band (not intersecting yet), is left alone:
    // it is already seen, and the class would fade it out (review of part B, section 28b).
    const edge = beat(view.container, "beat-comparisons");
    observer.emit(edge, false, window.innerHeight - 20);
    expect(edge.classList.contains("beat-enter")).toBe(false);
    // Every beat is in the document all along: nothing was added or removed.
    expect(view.container.querySelectorAll("section[id]")).toHaveLength(9);
  });
});
