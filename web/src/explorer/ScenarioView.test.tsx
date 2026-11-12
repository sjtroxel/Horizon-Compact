import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { findComparison, goalRunCount, runsOfGoal } from "./chartData";
import { explorerHis, explorerLabels as L } from "./copy";
import type { DataApi, GridFile } from "./data";
import { createDataApi } from "./data";
import { fileFetcher, realApi, realGrids, realIndex } from "./fixtures";
import { attemptedRuns, comparisonRuns } from "./format";
import { scenarioTextUrl } from "./links";
import { modelName } from "./models";
import { readingFor, PROTOCOL_READINGS } from "./protocol";
import { ScenarioView } from "./ScenarioView";
import { resultSentence, TEMPLATE_IDS } from "./sentences";

afterEach(cleanup);

const MODELS = ["haiku-5-5", "gpt-oss-openrouter"];
const SCENARIOS = realIndex.scenarios.map((s) => s.scenario_id);
const gridOf = (model: string, scenario: string): GridFile =>
  realGrids.find((g) => g.label === `grid ${model} ${scenario}`)!.file;

async function view(id: string, model: string, data: DataApi = realApi()) {
  const rendered = render(<ScenarioView id={id} index={realIndex} model={model} data={data} />);
  await rendered.findByRole("figure");
  return rendered;
}

/** Opens the "See the details" section the way a click does: the browser sets `open` and fires `toggle`. */
function openDetails(container: HTMLElement) {
  const details = container.querySelector<HTMLDetailsElement>("details.x-details")!;
  details.open = true;
  fireEvent(details, new Event("toggle"));
  return details;
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

const sentenceItems = (container: HTMLElement) => [...container.querySelectorAll<HTMLElement>("li.sent")];

describe("the scenario view, from the real files", () => {
  it("renders every scenario for both models without error", async () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const warnings = vi.spyOn(console, "warn").mockImplementation(() => {});
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const { container, unmount } = await view(id, model);
        expect(container.querySelector("h1")?.textContent, `${model} ${id}`).toContain(`(${id})`);
        expect(container.querySelectorAll(".result-sentence"), `${model} ${id}`).toHaveLength(5);
        expect(container.querySelector("figcaption")?.textContent).toContain(modelName(model));
        expect(container.querySelectorAll(".goal-row[data-goal]"), `${model} ${id}`).toHaveLength(5);
        unmount();
      }
    }
    expect(errors).not.toHaveBeenCalled();
    expect(warnings).not.toHaveBeenCalled();
    errors.mockRestore();
    warnings.mockRestore();
  });

  it("shows the scenario in brief (his, a placeholder), the full text's link, and the goals once", async () => {
    const { container, getByRole } = await view("s2", "haiku-5-5");
    expect(container.textContent).toContain(explorerHis.scenarioBriefs["s2"]);
    const link = getByRole("link", { name: new RegExp(L.sceneFullText) });
    expect(link.getAttribute("href")).toBe(scenarioTextUrl("s2"));
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
    const items = [...container.querySelectorAll(".x-goals li")];
    expect(items).toHaveLength(5);
    for (const [i, objective] of realIndex.objectives.entries()) {
      const text = items[i]!.textContent!;
      expect(text).toContain(L.objectiveNames[objective.id]);
      expect(text).toContain(`(${objective.id})`); // the letter beside the plain name
      if (objective.who === null) expect(text).toContain(L.goalUnstated);
      else expect(text).toContain(L.goalTold(objective.who, objective.when!)); // the literal description
    }
  });

  it("puts C vs D first as the lead, then A vs C, B vs D, A vs B, and A vs D last, marked secondary", async () => {
    for (const model of MODELS) {
      const { container, unmount } = await view("s1", model);
      const items = sentenceItems(container);
      expect(items.map((li) => li.dataset["pair"])).toEqual(["C-D", "A-C", "B-D", "A-B", "A-D"]);
      expect(items[0]!.classList.contains("lead")).toBe(true);
      expect(items.slice(1).some((li) => li.classList.contains("lead"))).toBe(false);
      expect(items[0]!.textContent).toContain(L.roundtableFlag);
      expect(items[4]!.textContent).toContain(L.secondaryFlag);
      unmount();
    }
  });

  it("states the confidence level once, in the closed 'about these results' section, from alpha (and not under the sentences)", async () => {
    const { container } = await view("s1", "haiku-5-5");
    const about = container.querySelector<HTMLDetailsElement>("details.about")!;
    expect(about.open).toBe(false);
    expect(about.querySelector("summary")!.textContent).toBe(L.aboutSummary);
    expect(about.querySelector(".about-body p")!.textContent).toBe(L.verdictNote("99.7%"));
    expect(container.textContent!.split(L.verdictNote("99.7%"))).toHaveLength(2);
    expect(container.querySelector(".x-sentences .chart-key")).toBeNull();
  });
});

describe("every result sentence is a template's output (section 12)", () => {
  it("names a known template and equals that template's output, on every view of both models", async () => {
    let sentences = 0;
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const file = gridOf(model, id);
        const { container, unmount } = await view(id, model);
        for (const li of sentenceItems(container)) {
          const element = li.querySelector<HTMLElement>(".result-sentence")!;
          const template = element.dataset["template"]!;
          expect(TEMPLATE_IDS as readonly string[], `${model} ${id}`).toContain(template);
          const [first, second] = li.dataset["pair"]!.split("-") as [string, string];
          const comparison = findComparison(file, first, second)!;
          const expected = resultSentence(comparison, L.objectiveNames, L.outcomePhrases[id]!);
          expect(template, `${model} ${id} ${first}-${second}`).toBe(expected.id);
          expect(element.textContent, `${model} ${id} ${first}-${second}`).toBe(expected.text);
          sentences += 1;
        }
        unmount();
      }
    }
    expect(sentences).toBe(2 * 4 * 5);
  });

  it("never shows a result sentence's text anywhere else in the view as a bare string", async () => {
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const { container, unmount } = await view(id, model);
        openDetails(container);
        const texts = [...container.querySelectorAll(".result-sentence")].map((e) => e.textContent!);
        const clone = container.cloneNode(true) as HTMLElement;
        clone.querySelectorAll(".result-sentence").forEach((e) => e.remove());
        for (const text of texts) expect(clone.textContent, `${model} ${id}`).not.toContain(text);
        unmount();
      }
    }
  });

  it("exercises all four templates across the real files", async () => {
    const seen = new Set<string>();
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const { container, unmount } = await view(id, model);
        container
          .querySelectorAll<HTMLElement>(".result-sentence")
          .forEach((e) => seen.add(e.dataset["template"]!));
        unmount();
      }
    }
    expect([...seen].sort()).toEqual([...TEMPLATE_IDS].sort());
  });
});

describe("the counts under each sentence", () => {
  it("are the comparison's own, and name the wordings when one was dropped", async () => {
    const { container } = await view("s1", "gpt-oss-openrouter");
    const file = gridOf("gpt-oss-openrouter", "s1");
    const ab = sentenceItems(container).find((li) => li.dataset["pair"] === "A-B")!;
    // The chart counts 56 dots for B, but A vs B counts only the wordings it kept: 40 and 39.
    expect(goalRunCount(file, "B")).toBe(56);
    expect(comparisonRuns(findComparison(file, "A", "B")!)).toEqual({ first: 40, second: 39 });
    expect(ab.textContent).toContain("40 and 39 runs");
    expect(ab.textContent).toContain(L.keptWordings("w1, w3"));
    expect(ab.textContent).toContain(L.droppedWordings("w2"));
    expect(ab.textContent).toContain(`${L.officialVerdict} ${L.verdictWords["split"]}`);
    const cd = sentenceItems(container).find((li) => li.dataset["pair"] === "C-D")!;
    expect(cd.textContent).not.toContain(L.droppedWordings(""));
  });

  it("show every comparison's own counts, and no count for one that is not assessable", async () => {
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const file = gridOf(model, id);
        const { container, unmount } = await view(id, model);
        for (const li of sentenceItems(container)) {
          const [first, second] = li.dataset["pair"]!.split("-") as [string, string];
          const comparison = findComparison(file, first, second)!;
          const small = li.querySelector(".fine")!.textContent!;
          if (comparison.final_verdict === "not_assessable") {
            expect(small).toContain(L.noRunsCompared);
            expect(small).not.toMatch(/\d+ and \d+ runs/);
          } else {
            const runs = comparisonRuns(comparison);
            expect(small, `${model} ${id} ${first}-${second}`).toContain(L.runsPair(runs.first, runs.second));
          }
          expect(small).toContain(`${L.officialVerdict} ${L.verdictWords[comparison.final_verdict]}`);
        }
        unmount();
      }
    }
  });
});

describe("the protocol's readings in the view", () => {
  it("quotes the row for C vs D's verdict under the lead, as written", async () => {
    const { container } = await view("s1", "haiku-5-5"); // C vs D: split
    const lead = sentenceItems(container)[0]!;
    const quote = lead.querySelector("blockquote")!;
    expect(quote.getAttribute("data-reading")).toBe("cd_split");
    expect(quote.textContent).toContain(PROTOCOL_READINGS.cd_split.reading);
  });

  it("quotes nothing where no row applies, and says so once for the column, not per pair", async () => {
    const { container } = await view("s1", "haiku-5-5");
    const items = sentenceItems(container);
    const ac = items.find((li) => li.dataset["pair"] === "A-C")!;
    expect(ac.querySelector("blockquote")).toBeNull();
    const bd = items.find((li) => li.dataset["pair"] === "B-D")!; // no split, but the protocol has no B vs D row
    expect(bd.querySelector("blockquote")).toBeNull();
    expect(container.textContent).not.toContain(L.noReading);
    expect(container.querySelectorAll(".readings-note")).toHaveLength(1);
    // Said once, in the 'about these results' section (the step 11 redesign moved it there from the sentence column).
    expect(container.querySelector(".about .readings-note")!.textContent).toBe(L.readingsNote);
    expect(container.querySelector(".x-sentences .readings-note")).toBeNull();
  });

  it("quotes no pulled-apart reading under A vs B where C vs D is only inconclusive (Haiku 5.5 s2)", async () => {
    const file = gridOf("haiku-5-5", "s2");
    expect(findComparison(file, "A", "B")!.final_verdict).toBe("split");
    expect(findComparison(file, "C", "D")!.final_verdict).toBe("inconclusive");
    const { container } = await view("s2", "haiku-5-5");
    const ab = sentenceItems(container).find((li) => li.dataset["pair"] === "A-B")!;
    expect(ab.querySelector("blockquote")).toBeNull();
    expect(container.textContent).not.toContain(PROTOCOL_READINGS.ab_split_cd_not.reading);
  });

  it("agrees with readingFor on every sentence of every view", async () => {
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const file = gridOf(model, id);
        const { container, unmount } = await view(id, model);
        const cd = findComparison(file, "C", "D")!.final_verdict;
        for (const li of sentenceItems(container)) {
          const [first, second] = li.dataset["pair"]!.split("-") as [string, string];
          const c = findComparison(file, first, second)!;
          const key = readingFor(first, second, c.final_verdict, cd);
          const quote = li.querySelector("blockquote");
          expect(quote?.getAttribute("data-reading") ?? null, `${model} ${id} ${first}-${second}`).toBe(key);
        }
        unmount();
      }
    }
  });
});

describe("the chart", () => {
  it("has one row per goal, labeled in text, with every run one dot and the run count beside it", async () => {
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const file = gridOf(model, id);
        const { container, unmount } = await view(id, model);
        const chart = container.querySelector<HTMLElement>(".chart[role=img]")!;
        expect(chart.getAttribute("aria-label")).toBe(L.chartLabel(id, modelName(model)));
        for (const goal of realIndex.objectives.map((o) => o.id)) {
          const row = chart.querySelector<HTMLElement>(`.goal-row[data-goal=${goal}]`)!;
          expect(row.textContent).toContain(L.objectiveNames[goal]); // never color alone
          expect(row.textContent).toContain(L.runCount(goalRunCount(file, goal)));
          expect(row.querySelectorAll("circle"), `${model} ${id} ${goal}`).toHaveLength(
            runsOfGoal(file, goal).length,
          );
        }
        unmount();
      }
    }
  });

  it("draws gpt-oss-120b's s1 goal B as 56 dots", async () => {
    const { container } = await view("s1", "gpt-oss-openrouter");
    expect(container.querySelectorAll(".goal-row[data-goal=B] circle")).toHaveLength(56);
    expect(container.querySelector(".goal-row[data-goal=B]")!.textContent).toContain("56 runs");
  });

  it("puts a share scenario's dots on the axis by their value, and words at the ends and the middle", async () => {
    const { container } = await view("s1", "haiku-5-5");
    const file = gridOf("haiku-5-5", "s1");
    const first = runsOfGoal(file, "A")[0]!;
    const dot = container.querySelector(".goal-row[data-goal=A] circle")!;
    expect(dot.getAttribute("cx")).toBe(`${first.primary * 100}%`);
    expect(dot.querySelector("title")!.textContent).toBe(
      L.dotTitleShare(
        L.objectiveNames["A"]!,
        first.wording_id,
        first.repeat,
        `${(first.primary * 100).toFixed(1)}%`,
      ),
    );
    const ends = L.axisEnds["s1"]!;
    expect(container.querySelector(".axis-words")!.textContent).toBe(ends.low + ends.mid + ends.high);
    // No ticks, interval, threshold or mean on the strip.
    expect(container.querySelector(".strip .band, .strip .interval, .strip .tick")).toBeNull();
    expect(container.querySelector(".strip")!.textContent).not.toMatch(/mean|threshold|interval/i);
  });

  it("groups a choice scenario's runs under the choice made, with n of N from the split", async () => {
    for (const model of MODELS) {
      for (const id of ["s3", "s4"]) {
        const file = gridOf(model, id);
        const { container, unmount } = await view(id, model);
        const order = file.descriptive.choice_splits
          .find((s) => s.wording_id === null)!
          .counts.map(([c]) => c);
        const heads = [...container.querySelectorAll(".units-head .unit-head")].map((e) => e.textContent);
        expect(heads).toEqual(order.map((c) => L.choices[c]));
        for (const goal of realIndex.objectives.map((o) => o.id)) {
          const split = file.descriptive.choice_splits.find(
            (s) => s.objective_id === goal && s.wording_id === null,
          )!;
          const cols = container.querySelectorAll(`.goal-row[data-goal=${goal}] .unit-col`);
          expect(cols).toHaveLength(order.length);
          split.counts.forEach(([, n], i) => {
            expect(cols[i]!.querySelectorAll("circle"), `${model} ${id} ${goal}`).toHaveLength(n);
            expect(cols[i]!.querySelector(".n-of-n")!.textContent).toBe(L.nOfN(n, split.runs));
          });
        }
        unmount();
      }
    }
  });

  it("titles a choice dot with the goal, the wording and repeat, and the choice's label", async () => {
    const { container } = await view("s3", "haiku-5-5");
    const file = gridOf("haiku-5-5", "s3");
    const col = container.querySelector(".goal-row[data-goal=A] .unit-col")!; // the first choice, close
    const run = runsOfGoal(file, "A").find((r) => r.choice === "close")!;
    expect(col.querySelector("title")!.textContent).toBe(
      L.dotTitleChoice(
        L.objectiveNames["A"]!,
        runsOfGoal(file, "A").find((r) => r.choice === "close")!.wording_id,
        run.repeat,
        L.choices["close"]!,
      ),
    );
  });

  it("keeps the model's name, the run counts and the scope line inside the figure, so a crop keeps them", async () => {
    for (const id of ["s1", "s3"]) {
      const file = gridOf("haiku-5-5", id);
      const { container, unmount } = await view(id, "haiku-5-5");
      const figure = container.querySelector("figure")!;
      expect(figure.textContent).toContain(modelName("haiku-5-5"));
      expect(figure.textContent).toContain(
        L.capValidOfAttempted(file.descriptive.runs, attemptedRuns(file.objective_rates)),
      );
      // The note line carries the short scope line; the full sentence is on the page once, not under the chart.
      expect(figure.querySelector("figcaption")!.textContent).toContain(explorerHis.scopeShort);
      expect(figure.textContent).not.toContain(explorerHis.scopeSentence);
      expect(container.textContent!.split(explorerHis.scopeSentence)).toHaveLength(2);
      // Framed by a rule: a title naming the measure (never a result) and the unit or how-to-read line, then the chart.
      const share = file.kind === "share";
      expect(figure.querySelector(".frame-title")!.textContent).toBe(
        share ? L.chartTitles.share[id] : L.chartTitles.choice,
      );
      expect(figure.querySelector(".frame-unit")!.textContent).toBe(share ? L.shareKey[id] : L.choiceKey);
      expect(figure.getAttribute("aria-labelledby")).toBe(figure.querySelector(".frame-title")!.id);
      expect(figure.querySelector(".frame-title")!.nextElementSibling!.className).toBe("frame-unit");
      unmount();
    }
  });

  it("uses no style attribute and no inline script anywhere", async () => {
    const { container } = await view("s4", "haiku-5-5");
    openDetails(container);
    expect(container.querySelectorAll("[style]")).toHaveLength(0);
    expect(container.querySelectorAll("script")).toHaveLength(0);
  });
});

describe("the goal toggles", () => {
  it("start all pressed, hide and show a goal's row, and carry aria-pressed", async () => {
    const { container, getByRole } = await view("s1", "haiku-5-5");
    const group = getByRole("group", { name: L.toggleGroup });
    const buttons = within(group).getAllByRole("button");
    expect(buttons).toHaveLength(5);
    expect(buttons.every((b) => b.getAttribute("aria-pressed") === "true")).toBe(true);
    const row = (goal: string) => container.querySelector<HTMLElement>(`.goal-row[data-goal=${goal}]`)!;
    expect(row("A").dataset["off"]).toBe("false");

    fireEvent.click(within(group).getByRole("button", { name: /Shareholders, short term \(A\)/ }));
    expect(within(group).getByRole("button", { name: /\(A\)/ }).getAttribute("aria-pressed")).toBe("false");
    expect(row("A").dataset["off"]).toBe("true");
    expect(row("A").getAttribute("aria-hidden")).toBe("true");
    expect(row("B").dataset["off"]).toBe("false");
    expect(row("B").getAttribute("aria-hidden")).toBeNull();

    fireEvent.click(within(group).getByRole("button", { name: /\(A\)/ }));
    expect(row("A").dataset["off"]).toBe("false");
    expect(within(group).getByRole("button", { name: /\(A\)/ }).getAttribute("aria-pressed")).toBe("true");
  });

  it("name their goal in text, and keep their state across a model switch", async () => {
    const data = realApi();
    const { container, rerender, getByRole } = await view("s3", "haiku-5-5", data);
    const group = getByRole("group", { name: L.toggleGroup });
    fireEvent.click(within(group).getByRole("button", { name: /\(D\)/ }));
    rerender(<ScenarioView id="s3" index={realIndex} model="gpt-oss-openrouter" data={data} />);
    await waitFor(() => expect(container.querySelector("figcaption")!.textContent).toContain("gpt-oss-120b"));
    expect(container.querySelector<HTMLElement>(".goal-row[data-goal=D]")!.dataset["off"]).toBe("true");
  });

  it("keep every goal in the details when a goal is hidden from the chart", async () => {
    const { container, getByRole } = await view("s1", "haiku-5-5");
    fireEvent.click(
      within(getByRole("group", { name: L.toggleGroup })).getByRole("button", { name: /\(E\)/ }),
    );
    openDetails(container);
    expect(container.querySelectorAll(".x-panel")).toHaveLength(5);
  });
});

describe("the details", () => {
  it("are closed on load and build nothing until opened", async () => {
    const { container } = await view("s4", "haiku-5-5");
    const details = container.querySelector<HTMLDetailsElement>("details.x-details")!;
    expect(details.open).toBe(false);
    expect(details.hasAttribute("open")).toBe(false);
    expect(container.querySelector(".x-details-body")).toBeNull();
    expect(details.querySelector("summary")!.textContent).toContain(L.seeDetails);
  });

  it("hold the interval chart, each comparison as the file has it, the allocation, the failures and the runs", async () => {
    for (const [model, id] of [
      ["gpt-oss-openrouter", "s2"],
      ["haiku-5-5", "s3"],
    ] as const) {
      const file = gridOf(model, id);
      const { container, unmount } = await view(id, model);
      openDetails(container);

      // The interval chart: five rows, the verdict word beside each, the confidence level stated.
      const rows = container.querySelectorAll(".intervals .interval-row:not(.interval-axis)");
      expect(rows).toHaveLength(5);
      // The interval key is said once, in the 'about these results' section, not again under this chart; the chart
      // has its own title and unit line, and a note line with the model, the valid runs and the short scope line.
      expect(container.querySelector(".about")!.textContent).toContain(L.intervalKey("99.7%"));
      expect(container.querySelector(".x-details-body")!.textContent).not.toContain(L.intervalKey("99.7%"));
      const intervalFigure = container.querySelector(".x-details-body figure")!;
      expect(intervalFigure.querySelector(".frame-title")!.textContent).toBe(
        L.chartTitles.interval(L.outcomePhrases[id]!),
      );
      expect(intervalFigure.querySelector(".frame-unit")!.textContent).toBe(L.intervalAxis);
      expect(intervalFigure.querySelector("figcaption")!.textContent).toContain(explorerHis.scopeShort);
      rows.forEach((row, i) => {
        const c = file.comparisons.find(
          (x) => `${x.first}-${x.second}` === sentenceItems(container)[i]!.dataset["pair"],
        )!;
        expect(row.querySelector(".verdict-word")!.textContent).toBe(L.verdictWords[c.final_verdict]);
        // A row that is not assessable has no line and says so.
        expect(row.querySelector("line.interval") === null).toBe(c.difference === null);
        expect(row.textContent!.includes(L.intervalRowNotAssessable)).toBe(c.difference === null);
      });

      // Each comparison: the headline verbatim, the sealed wording labeled as outside the family, the first attempt.
      const compares = [...container.querySelectorAll(".x-compare")];
      expect(compares).toHaveLength(5);
      for (const el of compares) {
        const [first, second] = (el as HTMLElement).dataset["pair"]!.split("-") as [string, string];
        const c = findComparison(file, first, second)!;
        expect(el.querySelector(".headline")!.textContent).toBe(c.headline);
        expect(el.textContent).toContain(c.sealed.label);
        expect(el.textContent).toContain(L.firstAttemptLabel);
      }

      // The allocation: a panel per goal, a row per lever, every run a dot.
      const panels = [...container.querySelectorAll<HTMLElement>(".x-panel")];
      expect(panels).toHaveLength(5);
      for (const panel of panels) {
        const goal = panel.dataset["goal"]!;
        const levers = panel.querySelectorAll(".lever-row:not(.lever-axis)");
        expect(levers.length).toBeGreaterThan(1);
        levers.forEach((lever) =>
          expect(lever.querySelectorAll("circle")).toHaveLength(goalRunCount(file, goal)),
        );
        expect(panel.textContent).toContain(L.objectiveNames[goal]);
      }

      // Failures: a row for every cell, zeros shown, and the file's own failure types.
      const failures = container.querySelector<HTMLElement>('[aria-label="' + L.failuresHeading + '"]')!;
      const failureRows = [...failures.querySelectorAll("tbody tr")];
      expect(failureRows).toHaveLength(file.cells.length);
      failureRows.forEach((tr, i) => {
        const cell = file.cells[i]!;
        const text = [...tr.querySelectorAll("td")].map((td) => td.textContent);
        expect(text.slice(1, 5)).toEqual(
          [cell.attempted, cell.valid, cell.rescaled, cell.refused].map(String),
        );
        expect(text[5]).toBe(
          cell.failed_by_type.length === 0
            ? L.noneWord
            : cell.failed_by_type.map(([t, n]) => L.tableFailures(t, n)).join("; "),
        );
      });

      // The runs: the chart's text equivalent, one row per run.
      const runs = container.querySelector<HTMLElement>('[aria-label="' + L.runsHeading + '"]')!;
      expect(runs.querySelectorAll("tbody tr")).toHaveLength(file.descriptive.per_run.length);
      unmount();
    }
  });

  it("keep every allocation dot on its plot: a lever that passes 100% (s4) gets the data's own scale, noted, in every panel", async () => {
    const { container } = await view("s4", "haiku-5-5");
    openDetails(container);
    const file = gridOf("haiku-5-5", "s4");
    // The scale for a lever is the highest summary maximum over the goals, when that is over 1.
    const highest = (lever: string) =>
      Math.max(
        1,
        ...file.descriptive.cells
          .filter((c) => c.wording_id === null && c.choice === null)
          .flatMap((c) => c.lines.filter((l) => l.key === lever).map((l) => l.summary.maximum)),
      );
    expect(highest("retain_cash")).toBeGreaterThan(3);
    const cashRows = [...container.querySelectorAll(".x-panel .lever-row")].filter((row) =>
      row.textContent!.includes(L.levers["retain_cash"]!),
    );
    expect(cashRows).toHaveLength(5);
    for (const row of cashRows) {
      expect(row.querySelector(".lever-scale")!.textContent).toBe(
        L.leverScale(`${Math.round(highest("retain_cash") * 100)}%`),
      );
    }
    for (const circle of container.querySelectorAll(".x-panel circle")) {
      const x = parseFloat(circle.getAttribute("cx")!);
      expect(x).toBeGreaterThanOrEqual(0);
      expect(x).toBeLessThanOrEqual(100 + 1e-9);
    }
    // A lever that stays within 100% carries no note.
    const programRow = [...container.querySelectorAll(".x-panel .lever-row")].find((row) =>
      row.textContent!.startsWith(L.levers["program"]!),
    )!;
    expect(programRow.querySelector(".lever-scale")).toBeNull();
  });

  it("note no scale on a scenario whose levers all stay within 100%", async () => {
    const { container } = await view("s1", "haiku-5-5");
    openDetails(container);
    expect(container.querySelectorAll(".lever-scale")).toHaveLength(0);
  });

  it("show gpt-oss-120b's s2 not-assessable row and the dropped wordings with their failures", async () => {
    const { container } = await view("s2", "gpt-oss-openrouter");
    openDetails(container);
    const ac = container.querySelector('.x-compare[data-pair="A-C"]')!;
    expect(ac.textContent).toContain("every wording has a cell over the 10% failure limit");
    expect(ac.textContent).toContain(L.droppedCell(L.objectiveNames["A"]!, 5, 20));
    const row = [...container.querySelectorAll(".intervals .interval-row")].find((r) =>
      r.textContent!.startsWith("A vs C"),
    )!;
    expect(row.querySelector("line.interval")).toBeNull();
    expect(row.textContent).toContain(L.intervalRowNotAssessable);
    const ab = container.querySelector('.x-compare[data-pair="A-B"]')!;
    expect(ab.textContent).toContain(L.droppedCell(L.objectiveNames["A"]!, 5, 20));
  });

  it("show the sealed wording's own result and the first attempt beside the final one", async () => {
    const { container } = await view("s1", "haiku-5-5");
    openDetails(container);
    const file = gridOf("haiku-5-5", "s1");
    const ac = file.comparisons.find((c) => c.first === "A" && c.second === "C")!;
    const el = container.querySelector('.x-compare[data-pair="A-C"]')!;
    expect(el.textContent).toContain(L.sealedWordingIs(ac.sealed.sealed_wording));
    expect(el.textContent).toContain(ac.sealed.relation_reason);
    expect(el.textContent).toContain(L.firstAttemptNote);
    expect(el.textContent).toContain(L.finalLabel);
  });
});

describe("loading, failing and switching", () => {
  it("shows a loading line until the grid arrives, and the load-failed text when it does not", async () => {
    const failing = createDataApi(async (path) =>
      path === "/data/index.json" ? fileFetcher()(path) : ({ ok: false, status: 500 } as Response),
    );
    const rendered = render(<ScenarioView id="s1" index={realIndex} model="haiku-5-5" data={failing} />);
    expect(rendered.getByRole("status").textContent).toBe(L.loadingScenario);
    expect((await rendered.findByRole("alert")).textContent).toBe(L.loadFailed);
    expect(rendered.container.querySelector("figure")).toBeNull();
  });

  it("holds the previous model's chart at reduced opacity while the next loads, then swaps it", async () => {
    const real = fileFetcher();
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => (release = resolve));
    const data = createDataApi(async (path) => {
      if (path.includes("gpt-oss")) await gate;
      return real(path);
    });
    const { container, rerender } = await view("s1", "haiku-5-5", data);
    expect(container.querySelector<HTMLElement>(".x-loaded")!.dataset["stale"]).toBe("false");
    rerender(<ScenarioView id="s1" index={realIndex} model="gpt-oss-openrouter" data={data} />);
    // Held: still Haiku's chart, marked stale, not a loading flash.
    expect(container.querySelector<HTMLElement>(".x-loaded")!.dataset["stale"]).toBe("true");
    expect(container.querySelector("figcaption")!.textContent).toContain("Haiku 5.5");
    expect(container.querySelector("[role=status]")).toBeNull();
    await act(async () => release());
    await waitFor(() => expect(container.querySelector("figcaption")!.textContent).toContain("gpt-oss-120b"));
    expect(container.querySelector<HTMLElement>(".x-loaded")!.dataset["stale"]).toBe("false");
    expect(container.querySelectorAll(".goal-row[data-goal=B] circle")).toHaveLength(56);
  });

  it("does not fetch a model's file again when switching back", async () => {
    const requested: string[] = [];
    const data = createDataApi(fileFetcher(requested));
    const { container, rerender } = await view("s1", "haiku-5-5", data);
    rerender(<ScenarioView id="s1" index={realIndex} model="gpt-oss-openrouter" data={data} />);
    await waitFor(() => expect(container.querySelector("figcaption")!.textContent).toContain("gpt-oss-120b"));
    rerender(<ScenarioView id="s1" index={realIndex} model="haiku-5-5" data={data} />);
    await waitFor(() => expect(container.querySelector("figcaption")!.textContent).toContain("Haiku 5.5"));
    expect(requested.filter((p) => p === "/data/grid/haiku-5-5/s1.json")).toHaveLength(1);
    expect(requested.filter((p) => p === "/data/grid/gpt-oss-openrouter/s1.json")).toHaveLength(1);
  });
});

describe("the link to the section for results against the thesis", () => {
  it("is on every scenario view, and carries the model", async () => {
    for (const [model, href] of [
      ["haiku-5-5", "/#against-the-thesis"],
      ["gpt-oss-openrouter", "/?model=gpt-oss-openrouter#against-the-thesis"],
    ] as const) {
      const { getByRole, unmount } = await view("s2", model);
      expect(getByRole("link", { name: L.againstLink }).getAttribute("href")).toBe(href);
      unmount();
    }
  });

  it("marks, with a small link, the sentences that the section lists, and only those", async () => {
    const entries = realIndex.against_thesis.entries;
    expect(entries.length).toBeGreaterThan(0);
    for (const model of MODELS) {
      for (const id of SCENARIOS) {
        const { container, unmount } = await view(id, model);
        for (const li of sentenceItems(container)) {
          const [first, second] = li.dataset["pair"]!.split("-");
          const listed = entries.some(
            (e) => e.model_key === model && e.scenario_id === id && e.first === first && e.second === second,
          );
          expect(li.querySelectorAll("a.marker").length, `${model} ${id} ${first}-${second}`).toBe(
            listed ? 1 : 0,
          );
        }
        unmount();
      }
    }
  });
});

describe("accessibility and the page's rules", () => {
  it("has no axe violations on a share scenario with the details open (the not-assessable and dropped case)", async () => {
    const { container } = await view("s2", "gpt-oss-openrouter");
    openDetails(container);
    expect(await violations(container)).toEqual([]);
  }, 60_000);

  it("has no axe violations on a choice scenario with the details open", async () => {
    const { container } = await view("s3", "haiku-5-5");
    openDetails(container);
    expect(await violations(container)).toEqual([]);
  }, 60_000);

  it("has one h1, and headings that step down by one", async () => {
    const { container } = await view("s4", "haiku-5-5");
    openDetails(container);
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    let last = 0;
    for (const heading of container.querySelectorAll("h1, h2, h3, h4")) {
      const level = Number(heading.tagName.slice(1));
      expect(level - last, heading.textContent!).toBeLessThanOrEqual(1);
      last = level;
    }
  });
});
