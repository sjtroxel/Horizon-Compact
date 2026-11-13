import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { findComparison, goalRunCount, orderedComparisons, runsOfGoal } from "./chartData";
import { explorerHis, explorerLabels as L } from "./copy";
import type { AwarenessFile, DataApi } from "./data";
import { editedApi, readAwareness, realApi, realGrids, realIndex } from "./fixtures";
import { comparisonRuns, confidenceLevel, wordingRuns } from "./format";
import { AWARENESS_ANCHOR, THINKING_ANCHOR, protocolUrl } from "./links";
import { modelName } from "./models";
import { AWARENESS_INSTRUCTION, PROTOCOL_READINGS } from "./protocol";
import { memoHref } from "./route";
import { resultSentence } from "./sentences";
import { StudiesView } from "./Studies";

afterEach(cleanup);

const HAIKU = "haiku-5-5";
const GPT = "gpt-oss-openrouter";
const MODELS = L.models.map((m) => m.key);
const thinking = realGrids.find((g) => g.label === `thinking ${HAIKU} s1`)!.file;
const grid = realGrids.find((g) => g.label === `grid ${HAIKU} s1`)!.file;
const SEALED = realIndex.models.find((m) => m.model_key === HAIKU)!.sealed_wording;
const GOALS = realIndex.objectives.map((o) => o.id);
const verdictWord = (v: string) => L.verdictWords[v]!;

async function studies(data: DataApi = realApi(), model = HAIKU) {
  const rendered = render(<StudiesView index={realIndex} model={model} data={data} />);
  await waitFor(() => expect(rendered.container.querySelector(".awareness-model")).not.toBeNull());
  return rendered;
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

const before = (a: Element, b: Element) =>
  Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
const part = (container: HTMLElement, id: string) => container.querySelector<HTMLElement>(`#${id}`)!;

describe("the studies page", () => {
  it("holds his introduction and the titles of its two parts, as headings, each part findable by id", async () => {
    const { container } = await studies();
    expect(container.querySelector("h1")).not.toBeNull();
    expect(container.textContent).toContain(explorerHis.studiesIntro);
    const sub = part(container, "thinking-sub-study");
    const probes = part(container, "awareness-probes");
    expect(sub.querySelector("h2")!.textContent).toBe(explorerHis.studiesThinkingTitle);
    expect(probes.querySelector("h2")!.textContent).toBe(explorerHis.studiesAwarenessTitle);
    expect(sub.getAttribute("tabindex")).toBe("-1");
    expect(before(sub, probes)).toBe(true);
  });

  it("carries the full scope sentence once, near the top, and each figure carries the short one in its note line", async () => {
    const { container } = await studies();
    expect(container.textContent!.split(explorerHis.scopeSentence)).toHaveLength(2);
    const figures = [...container.querySelectorAll("figure.card")];
    expect(figures).toHaveLength(2);
    for (const figure of figures) {
      expect(figure.querySelector("figcaption")!.textContent).toContain(explorerHis.scopeShort);
      expect(figure.textContent).not.toContain(explorerHis.scopeSentence);
      expect(figure.getAttribute("aria-labelledby")).toBe(figure.querySelector(".frame-title")!.id);
      expect(figure.querySelector(".frame-unit")!.textContent).toBe(L.shareKey["s1"]);
    }
    expect(before(container.querySelector("h1")!, figures[0]!)).toBe(true);
  });

  it("fetches only paths under /data/, and renders without a console error", async () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const requested: string[] = [];
    await studies(realApi(requested));
    expect(requested.length).toBeGreaterThan(3);
    for (const p of requested) expect(p.startsWith("/data/"), p).toBe(true);
    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
  });
});

describe("the thinking sub-study", () => {
  it("is labeled as a sub-study on s1, on Haiku 5.5 only, not one of the 16 main comparisons, before anything it shows", async () => {
    const { container } = await studies();
    const label = container.querySelector("[data-label=sub-study]")!;
    expect(label.textContent).toBe(L.studiesSubStudyLabel);
    for (const part of ["sub-study", "s1", "Haiku 5.5", "not one of the 16 main comparisons"])
      expect(label.textContent).toContain(part);
    expect(before(label, container.querySelector(".studies-figures")!)).toBe(true);
    expect(before(label, container.querySelector(".x-sentence-list")!)).toBe(true);
  });

  it("states its settings and links to protocol 9.5 at the pre-registered tag", async () => {
    const { container } = await studies();
    expect(container.textContent).toContain(L.studiesSettings);
    const link = within(container).getByRole("link", { name: L.studiesSettingsLink });
    expect(link.getAttribute("href")).toBe(protocolUrl(THINKING_ANCHOR));
    expect(link.getAttribute("href")).toContain("/blob/prereg-v1/");
  });

  it("sets the grid's wording w2 beside the sub-study, like for like: the same strip, the same size", async () => {
    const { container } = await studies();
    const [left, right] = [...container.querySelectorAll<HTMLElement>(".studies-figures figure")];
    expect(left!.querySelector(".frame-title")!.textContent).toBe(L.studiesGridCard);
    expect(right!.querySelector(".frame-title")!.textContent).toBe(L.studiesThinkingCard);
    expect(container.textContent).toContain(L.studiesGridNote);
    // The same component at the same size: a strip with a row for every goal and the same plot height.
    for (const card of [left!, right!]) {
      expect(card.querySelectorAll(".chart.strip")).toHaveLength(1);
      expect(card.querySelectorAll(".goal-row[data-goal]")).toHaveLength(GOALS.length);
    }
    const heights = (card: HTMLElement) =>
      [...card.querySelectorAll("svg.x-plot")].map((s) => s.getAttribute("height"));
    expect(heights(left!)).toEqual(heights(right!));
    // The two figures sit side by side across the page's width (step 11 pages, item 14), with the words that explain
    // them above and the five comparisons below; no column of their own beside them to leave empty.
    const figures = container.querySelector<HTMLElement>(".studies-figures")!;
    const words = container.querySelector<HTMLElement>(".studies-words")!;
    expect(figures.children).toHaveLength(2);
    expect(container.querySelector(".beside, .beside-studies, .beside-text")).toBeNull();
    expect(words.contains(figures)).toBe(false);
    expect(before(words, figures)).toBe(true);
    expect(before(figures, container.querySelector(".x-sentence-list")!)).toBe(true);
    expect(words.textContent).toContain(L.studiesSubStudyLabel);
    expect(words.textContent).toContain(L.studiesGridNote);
  });

  it("draws the grid's runs of wording w2 only, with each goal's count from the descriptive cell of that wording", async () => {
    const { container } = await studies();
    const [left, right] = [...container.querySelectorAll<HTMLElement>(".studies-figures figure")];
    for (const goal of GOALS) {
      const gridRow = left!.querySelector<HTMLElement>(`.goal-row[data-goal=${goal}]`)!;
      const subRow = right!.querySelector<HTMLElement>(`.goal-row[data-goal=${goal}]`)!;
      expect(gridRow.querySelector(".goal-count")!.textContent).toBe(
        L.runCount(goalRunCount(grid, goal, SEALED)),
      );
      expect(subRow.querySelector(".goal-count")!.textContent).toBe(L.runCount(goalRunCount(thinking, goal)));
      expect(gridRow.querySelectorAll("circle")).toHaveLength(runsOfGoal(grid, goal, SEALED).length);
      expect(subRow.querySelectorAll("circle")).toHaveLength(runsOfGoal(thinking, goal).length);
    }
    // Not the grid's three wordings: it has three times the rows the card draws.
    expect(grid.descriptive.per_run.length).toBeGreaterThan(left!.querySelectorAll("circle").length);
    for (const title of left!.querySelectorAll("circle title"))
      expect(title.textContent).toContain(`wording ${SEALED}`);
    expect(right!.querySelector("figcaption")!.textContent).toContain(
      L.capValidOfAttempted(thinking.descriptive.runs, 100),
    );
    // The grid's figure draws wording w2 alone, so its note line states w2's valid runs of those attempted (cells of the
    // file), not the whole grid's: it was the one figure with no such line before the redesign.
    const w2 = wordingRuns(grid, SEALED);
    expect(w2.valid).toBe(GOALS.reduce((sum, goal) => sum + goalRunCount(grid, goal, SEALED), 0));
    expect(left!.querySelector("figcaption")!.textContent).toContain(
      L.capValidOfAttempted(w2.valid, w2.attempted),
    );
    expect(left!.querySelector("figcaption")!.textContent).toContain(explorerHis.scopeShort);
    expect(right!.querySelector("figcaption")!.textContent).toContain(explorerHis.scopeShort);
  });

  it("states the interval level from alpha, without the family, and shows no protocol reading", async () => {
    const { container } = await studies();
    const sub = part(container, "thinking-sub-study");
    const level = confidenceLevel(thinking.comparisons[0]!.alpha);
    expect(level).toBe("99.7%");
    const line = L.studiesLevel(level);
    expect(sub.textContent).toContain(line);
    expect(line).not.toMatch(/family|Bonferroni|16/);
    expect(sub.textContent).not.toContain(L.verdictNote(level)); // the scenario view's note names the family
    expect(sub.textContent).not.toContain("Bonferroni");
    expect(sub.querySelector("[data-reading]")).toBeNull();
    for (const reading of Object.values(PROTOCOL_READINGS))
      expect(sub.textContent).not.toContain(reading.reading);
    expect(sub.textContent).not.toContain(L.protocolReadingLabel);
  });

  it("shows its five comparisons, C vs D first, each with the template's sentence, its run counts, its verdict and its headline", async () => {
    const { container } = await studies();
    const items = [...container.querySelectorAll<HTMLElement>(".x-sentence-list li.sent")];
    expect(items.map((li) => li.dataset["pair"])).toEqual(["C-D", "A-C", "B-D", "A-B", "A-D"]);
    expect(items[0]!.classList.contains("lead")).toBe(true);
    expect(items[0]!.textContent).toContain(L.roundtableFlag);
    expect(items[4]!.textContent).toContain(L.secondaryFlag);
    for (const [i, c] of orderedComparisons(thinking).entries()) {
      const li = items[i]!;
      const sentence = resultSentence(c, L.objectiveNames, L.outcomePhrases["s1"]!);
      const element = li.querySelector<HTMLElement>(".result-sentence")!;
      expect(element.textContent).toBe(sentence.text);
      expect(element.dataset["template"]).toBe(sentence.id);
      const runs = comparisonRuns(c);
      expect(li.textContent).toContain(L.runsPair(runs.first, runs.second));
      // The official verdict and the analysis headline are in the closed per-comparison section, not in the visible
      // lines (step 11 pages, item 15); the runs line stays visible.
      const more = li.querySelector<HTMLDetailsElement>("details.finding-more")!;
      expect(more.open).toBe(false);
      expect(more.textContent).toContain(`${L.officialVerdict} ${verdictWord(c.final_verdict)}`);
      expect(more.querySelector(".headline")!.textContent).toBe(`${L.headlineLabel}: ${c.headline}`); // verbatim
      const visible = [...li.querySelectorAll(".paired-main > .fine")].map((p) => p.textContent);
      expect(visible).toEqual([
        c.final_verdict === "not_assessable" ? L.noRunsCompared : L.runsPair(runs.first, runs.second),
      ]);
      expect(li.querySelectorAll(".headline")).toHaveLength(1);
    }
  });

  it("shows the grid's verdict on wording w2 alone for each pair as a column: the long phrase once, as its heading, and only the verdict word in each row (step 11 pages, item 16)", async () => {
    const { container } = await studies();
    const sub = part(container, "thinking-sub-study");
    // Every real pair's sealed wording is the index's, so one heading can say it for the column.
    for (const c of thinking.comparisons)
      expect(findComparison(grid, c.first, c.second)!.sealed.sealed_wording).toBe(SEALED);
    const phrase = L.studiesGridColumn(SEALED);
    expect(phrase).toContain("not one of the 16 main comparisons");
    expect(sub.textContent!.split(phrase)).toHaveLength(2); // once
    const head = sub.querySelector<HTMLElement>(".paired-head")!;
    expect(head.textContent).toBe(phrase);
    // The caveat reaches a screen reader: the heading is not hidden from it (Opus review, section 33a).
    expect(head.closest("[aria-hidden]")).toBeNull();
    expect(before(head, sub.querySelector(".x-sentence-list")!)).toBe(true);
    for (const c of thinking.comparisons) {
      const li = container.querySelector<HTMLElement>(`li.sent[data-pair=${c.first}-${c.second}]`)!;
      const gridPair = findComparison(grid, c.first, c.second)!;
      const cell = li.querySelector<HTMLElement>(".paired-grid")!;
      expect(cell.querySelector(".paired-verdict")!.textContent).toBe(
        verdictWord(gridPair.sealed.final_verdict),
      );
      // The short row label is in every row, at every width (section 33b, note C); the cell says nothing else.
      expect(cell.querySelector(".paired-row-label")!.textContent).toBe(`${L.studiesGridRowLabel(SEALED)}: `);
      expect(cell.textContent).toBe(
        `${L.studiesGridRowLabel(SEALED)}: ${verdictWord(gridPair.sealed.final_verdict)}`,
      );
      expect(cell.dataset["gridSealed"]).toBe(gridPair.sealed.final_verdict);
      expect(cell.textContent).not.toContain("not one of the 16");
      expect(li.classList.contains("paired")).toBe(true);
    }
    // The two do not always agree, and the page shows both: C vs D is inconclusive in the sub-study, in the grid's w2 too.
    expect(findComparison(grid, "C", "D")!.sealed.final_verdict).toBe("inconclusive");
  });

  it("links to the sub-study's memos in the reader, and every run id in its table to that run's memo", async () => {
    const { container } = await studies();
    const link = within(container).getByRole("link", { name: L.studiesMemosLink });
    expect(link.getAttribute("href")).toBe(
      memoHref({ kind: "thinking", scenario: "s1", objective: "A" }, HAIKU),
    );
    const details = container.querySelector<HTMLDetailsElement>("details.x-details")!;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    const ids = [...details.querySelectorAll<HTMLAnchorElement>("th.mono a")];
    expect(ids).toHaveLength(thinking.descriptive.per_run.length);
    for (const [i, run] of thinking.descriptive.per_run.entries()) {
      expect(ids[i]!.textContent).toBe(run.run_id);
      expect(ids[i]!.getAttribute("href")).toBe(
        memoHref({ kind: "thinking", scenario: "s1", objective: run.objective_id, run: run.run_id }, HAIKU),
      );
    }
  });

  it("builds its runs table only once opened", async () => {
    const { container } = await studies();
    expect(container.querySelector<HTMLDetailsElement>("details.x-details")!.open).toBe(false);
    expect(container.querySelector("details table")).toBeNull();
  });
});

describe("the awareness probes", () => {
  it("quote the protocol's instruction word for word, say they are context only, and link to protocol 9.6", async () => {
    const { container } = await studies();
    const probes = part(container, "awareness-probes");
    expect(probes.querySelector("blockquote.probe-instruction")!.textContent).toBe(AWARENESS_INSTRUCTION);
    expect(probes.querySelectorAll("blockquote")).toHaveLength(1); // the only quote on the page: no reply is one
    expect(probes.querySelector("[data-label=awareness]")!.textContent).toBe(L.awarenessLabel);
    expect(L.awarenessLabel).toMatch(/context only/i);
    expect(L.awarenessLabel).toMatch(/never|none is used to filter or weight/);
    expect(within(probes).getByRole("link", { name: L.awarenessLink }).getAttribute("href")).toBe(
      protocolUrl(AWARENESS_ANCHOR),
    );
    // The instruction comes before the first reply.
    expect(before(probes.querySelector("blockquote")!, probes.querySelector("article")!)).toBe(true);
  });

  it.each(MODELS)(
    "shows only %s's 15 replies, under a heading naming that model: a row a goal, a column a template (step 11 pages, item 17)",
    async (model) => {
      const { container } = await studies(realApi(), model);
      const models = [...container.querySelectorAll<HTMLElement>(".awareness-model")];
      expect(models.map((m) => m.dataset["model"])).toEqual([model]);
      const section = models[0]!;
      expect(section.querySelector("h3")!.textContent).toBe(modelName(model));
      const file = readAwareness(model);
      const rows = [...section.querySelectorAll<HTMLElement>(".reply-row")];
      expect(rows.map((g) => g.dataset["goal"])).toEqual(GOALS);
      expect(section.querySelectorAll("article")).toHaveLength(15);
      expect(container.querySelectorAll("#awareness-probes article")).toHaveLength(15);
      for (const row of rows) {
        const goal = row.dataset["goal"]!;
        expect(row.querySelector("h4")!.textContent).toBe(
          L.awarenessGoalHeading(L.objectiveNames[goal]!, goal),
        );
        expect(row.querySelector("h4 .swatch")).not.toBeNull(); // the goal's color dot
        const cells = [...row.querySelectorAll<HTMLElement>("article.reply-cell")];
        expect(cells.map((c) => c.dataset["template"])).toEqual(["w1", "w2", "w3"]); // a column a template
        for (const cell of cells) {
          const call = file.calls.find(
            (c) => c.objective_id === goal && c.template_id === cell.dataset["template"],
          )!;
          expect(call.recorded).toBe(true);
          if (!call.recorded) continue;
          expect(cell.querySelector(".reply-tag")!.textContent).toBe(
            L.awarenessTemplateTag(call.template_id),
          );
          expect(cell.querySelector(".fine")!.textContent).toBe(
            L.awarenessStatus(call.status, call.stop_reason, call.output_tokens),
          );
          // Unedited and untruncated (protocol section 9.6).
          expect(cell.querySelector(".memo-text")!.textContent).toBe(call.reply);
          // The sentence that these are not decision memos is said once above the grid, not on a cell.
          expect(cell.textContent).not.toContain("not decision memos");
          expect(cell.getAttribute("aria-labelledby")).toContain(row.querySelector("h4")!.id);
        }
      }
      // Said once, above the grid, with the model's name.
      expect(section.textContent!.split("not decision memos")).toHaveLength(2);
      const label = [...section.querySelectorAll(".chart-key")].find(
        (p) => p.textContent === L.awarenessGridLabel(modelName(model)),
      )!;
      expect(before(label, section.querySelector(".reply-grid")!)).toBe(true);
      // The other model's replies are not on the page.
      const other = MODELS.find((m) => m !== model)!;
      for (const call of readAwareness(other).calls)
        if (call.recorded && call.reply.length > 200) expect(container.textContent).not.toContain(call.reply);
      // The sub-study above does not follow the switch.
      expect(container.querySelectorAll(".studies-figures figure")).toHaveLength(2);
    },
  );

  it("changes the replies, and nothing above them, when the model changes", async () => {
    const first = await studies(realApi(), HAIKU);
    const thinkingText = part(first.container, "thinking-sub-study").textContent;
    first.rerender(<StudiesView index={realIndex} model={GPT} data={realApi()} />);
    await waitFor(() =>
      expect(first.container.querySelector(".awareness-model")!.getAttribute("data-model")).toBe(GPT),
    );
    expect(part(first.container, "thinking-sub-study").textContent).toBe(thinkingText);
  });

  it("sets each reply as a document: no quote element, no quotation marks added", async () => {
    for (const model of MODELS) {
      const { container, unmount } = await studies(realApi(), model);
      const cells = container.querySelectorAll("#awareness-probes article");
      expect(cells).toHaveLength(15);
      for (const cell of cells) {
        expect(cell.querySelector("blockquote, q, em, i, cite")).toBeNull();
        expect(cell.querySelector(".memo-text")!.firstChild!.nodeType).toBe(Node.TEXT_NODE);
      }
      unmount();
    }
  });

  it("have no card of their own: no bordered cell, and a rule between the rows", async () => {
    const { container } = await studies();
    expect(container.querySelector(".reply-card, .memo-card")).toBeNull();
    expect(container.querySelectorAll(".reply-row")).toHaveLength(GOALS.length);
  });

  it("say so when a call was not recorded, and show a label in place of '(no text)' for a reply that had none", async () => {
    const edit = (body: AwarenessFile) => {
      body.calls[0] = { objective_id: "A", template_id: "w1", recorded: false };
      const second = body.calls[1]!;
      if (second.recorded) {
        second.reply = "(no text)";
        second.empty_reply = true;
      }
    };
    const { container } = await studies(editedApi({ "/data/awareness/haiku-5-5.json": edit }));
    const haiku = container.querySelector<HTMLElement>(`.awareness-model[data-model="${HAIKU}"]`)!;
    const [first, second] = haiku.querySelectorAll("article");
    expect(first!.querySelector(".memo-none")!.textContent).toBe(L.awarenessNotRecorded);
    expect(first!.querySelector(".memo-text")).toBeNull();
    expect(second!.querySelector(".memo-none")!.textContent).toBe(L.awarenessEmpty);
    expect(second!.textContent).not.toContain("(no text)");
  });
});

describe("accessibility", () => {
  it("has no axe violations on the studies page", async () => {
    const { container } = await studies();
    expect(await violations(container)).toEqual([]);
  });

  it("has no axe violations with the sub-study's runs table open", async () => {
    const { container } = await studies();
    const details = container.querySelector<HTMLDetailsElement>("details.x-details")!;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    expect(container.querySelectorAll("details table")).toHaveLength(1);
    expect(await violations(details)).toEqual([]);
  });
});
