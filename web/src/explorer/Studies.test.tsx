import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { findComparison, goalRunCount, orderedComparisons, runsOfGoal } from "./chartData";
import { explorerHis, explorerLabels as L } from "./copy";
import type { AwarenessFile, DataApi } from "./data";
import { editedApi, readAwareness, realApi, realGrids, realIndex } from "./fixtures";
import { comparisonRuns, confidenceLevel } from "./format";
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

async function studies(data: DataApi = realApi()) {
  const rendered = render(<StudiesView index={realIndex} data={data} />);
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
    expect(before(label, container.querySelector(".layout-pair")!)).toBe(true);
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
    const [left, right] = [...container.querySelectorAll<HTMLElement>(".layout-pair figure")];
    expect(left!.querySelector(".study-card-title")!.textContent).toBe(L.studiesGridCard);
    expect(right!.querySelector(".study-card-title")!.textContent).toBe(L.studiesThinkingCard);
    expect(container.textContent).toContain(L.studiesGridNote);
    // The same component at the same size: a strip with a row for every goal and the same plot height.
    for (const card of [left!, right!]) {
      expect(card.querySelectorAll(".chart.strip")).toHaveLength(1);
      expect(card.querySelectorAll(".goal-row[data-goal]")).toHaveLength(GOALS.length);
    }
    const heights = (card: HTMLElement) =>
      [...card.querySelectorAll("svg.x-plot")].map((s) => s.getAttribute("height"));
    expect(heights(left!)).toEqual(heights(right!));
    expect(container.querySelector(".layout-pair")!.children).toHaveLength(2);
  });

  it("draws the grid's runs of wording w2 only, with each goal's count from the descriptive cell of that wording", async () => {
    const { container } = await studies();
    const [left, right] = [...container.querySelectorAll<HTMLElement>(".layout-pair figure")];
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
      expect(li.textContent).toContain(`${L.officialVerdict} ${verdictWord(c.final_verdict)}`);
      expect(li.querySelector(".headline")!.textContent).toBe(`${L.headlineLabel}: ${c.headline}`); // verbatim
    }
  });

  it("shows beside each comparison the grid's verdict on wording w2 alone for the same pair, labeled", async () => {
    const { container } = await studies();
    for (const c of thinking.comparisons) {
      const li = container.querySelector<HTMLElement>(`li.sent[data-pair=${c.first}-${c.second}]`)!;
      const gridPair = findComparison(grid, c.first, c.second)!;
      const beside = li.querySelector<HTMLElement>(".paired-grid")!;
      expect(beside.textContent).toBe(
        L.studiesGridSealed(SEALED, verdictWord(gridPair.sealed.final_verdict)),
      );
      expect(beside.dataset["gridSealed"]).toBe(gridPair.sealed.final_verdict);
      expect(beside.textContent).toContain("not one of the 16 main comparisons");
      // Both are in the same list item, side by side at 40rem and wider.
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
    const details = container.querySelector("details")!;
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
    expect(container.querySelector("details")!.open).toBe(false);
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

  it("show 15 replies for each model in the labels' order, grouped by goal and then by template", async () => {
    const { container } = await studies();
    const models = [...container.querySelectorAll<HTMLElement>(".awareness-model")];
    expect(models.map((m) => m.dataset["model"])).toEqual(MODELS);
    for (const [i, model] of MODELS.entries()) {
      const section = models[i]!;
      expect(section.querySelector("h3")!.textContent).toBe(modelName(model));
      const file = readAwareness(model);
      const groups = [...section.querySelectorAll<HTMLElement>(".awareness-goal")];
      expect(groups.map((g) => g.dataset["goal"])).toEqual(GOALS);
      expect(section.querySelectorAll("article")).toHaveLength(15);
      for (const group of groups) {
        const goal = group.dataset["goal"]!;
        const cards = [...group.querySelectorAll<HTMLElement>("article")];
        expect(cards.map((c) => c.dataset["template"])).toEqual(["w1", "w2", "w3"]);
        expect(group.querySelector("h4")!.textContent).toBe(
          L.awarenessGoalHeading(L.objectiveNames[goal]!, goal),
        );
        for (const card of cards) {
          const call = file.calls.find(
            (c) => c.objective_id === goal && c.template_id === card.dataset["template"],
          )!;
          expect(call.recorded).toBe(true);
          if (!call.recorded) continue;
          // The label is inside the card, first: a reply to the probe, not a decision memo.
          expect(card.firstElementChild!.textContent).toBe(
            L.awarenessCardLabel(modelName(model), goal, L.objectiveNames[goal]!, call.template_id),
          );
          expect(card.firstElementChild!.textContent).toContain("not a decision memo");
          expect(card.querySelector(".fine")!.textContent).toBe(
            L.awarenessStatus(call.status, call.stop_reason, call.output_tokens),
          );
          expect(card.querySelector(".memo-text")!.textContent).toBe(call.reply); // exactly
        }
      }
    }
  });

  it("sets each reply as a document: no quote element, no quotation marks added", async () => {
    const { container } = await studies();
    const cards = container.querySelectorAll("#awareness-probes article");
    expect(cards).toHaveLength(30);
    for (const card of cards) {
      expect(card.querySelector("blockquote, q, em, i, cite")).toBeNull();
      expect(card.querySelector(".memo-text")!.firstChild!.nodeType).toBe(Node.TEXT_NODE);
    }
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
    // The other model is untouched.
    const other = container.querySelector<HTMLElement>(`.awareness-model[data-model="${GPT}"]`)!;
    expect(other.querySelectorAll(".memo-none")).toHaveLength(0);
  });
});

describe("accessibility", () => {
  it("has no axe violations on the studies page", async () => {
    const { container } = await studies();
    expect(await violations(container)).toEqual([]);
  });

  it("has no axe violations with the sub-study's runs table open", async () => {
    const { container } = await studies();
    const details = container.querySelector("details")!;
    details.open = true;
    fireEvent(details, new Event("toggle"));
    expect(container.querySelectorAll("details table")).toHaveLength(1);
    expect(await violations(details)).toEqual([]);
  });
});
