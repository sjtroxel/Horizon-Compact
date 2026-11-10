import { cleanup, render, waitFor } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { orderedReadings } from "./caseData";
import { CaseView, CasesView } from "./Cases";
import { explorerHis, explorerLabels as L } from "./copy";
import type { CaseFile, DataApi } from "./data";
import { DistanceChart } from "./distanceChart";
import { editedApi, realApi, realCaseFiles, realCasesIndex, realIndex } from "./fixtures";
import { axisPercent, formatDistance, formatPercent } from "./format";
import { SELECTION_LOGS, selectionLogUrl } from "./links";
import { modelName } from "./models";

afterEach(cleanup);

const HAIKU = "haiku-5-5";
const GPT = "gpt-oss-openrouter";
const MODELS = L.models.map((m) => m.key);
const LABELS = realCasesIndex.cases.map((c) => c.label);
const fileOf = (label: string, model: string): CaseFile =>
  realCaseFiles.find((c) => c.label === label && c.model === model)!.file;
const path = (label: string, model: string) => `/data/${realIndex.files.case_results[label]![model]!}`;

async function list(model = HAIKU, data: DataApi = realApi()) {
  const rendered = render(
    <CasesView index={realIndex} casesIndex={realCasesIndex} model={model} data={data} />,
  );
  await waitFor(() => expect(rendered.container.querySelector(".case-readings")).not.toBeNull());
  return rendered;
}

async function page(label: string, data: DataApi = realApi()) {
  const rendered = render(
    <CaseView label={label} index={realIndex} casesIndex={realCasesIndex} data={data} />,
  );
  await waitFor(() => expect(rendered.container.querySelectorAll(".case-model").length).toBe(MODELS.length));
  return rendered;
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

/** True when `a` comes before `b` in document order. */
const before = (a: Element, b: Element) =>
  Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);

const readingName = (id: string) => L.readingNames[id] ?? L.readingAlternative(id);

describe("/cases/", () => {
  it("shows his introduction and the framing: the protocol applied to real decisions, not a validation", async () => {
    const { container } = await list();
    expect(container.textContent).toContain(explorerHis.casesIntro);
    const framing = container.querySelector(".case-framing")!;
    expect(framing.textContent).toBe(L.casesFraming);
    expect(framing.textContent).toMatch(/not a validation/);
    expect(framing.textContent).not.toMatch(/validates|proves|confirms/);
  });

  it("puts the exploratory label first: before any sentence about the readings, any count and any card's readings", async () => {
    const { container } = await list();
    const first = container.querySelector(".exploratory-lead .exploratory-label")!;
    expect(first.textContent).toBe(realCasesIndex.cases[0]!.exploratory_label);
    for (const later of [
      container.querySelector("[data-sentence]")!,
      container.querySelector(".shortfall")!,
      container.querySelector(".shortfall table")!,
      ...container.querySelectorAll(".case-readings"),
    ]) {
      expect(before(first, later)).toBe(true);
    }
    for (const card of container.querySelectorAll(".case-card")) {
      const label = card.querySelector(".exploratory-label")!;
      expect(before(label, card.querySelector(".case-readings")!)).toBe(true);
    }
  });

  it("lists one card per case in the file's order, each with its exploratory label verbatim, first after its heading", async () => {
    const { container } = await list();
    const cards = [...container.querySelectorAll<HTMLElement>(".case-card")];
    expect(cards.map((c) => c.dataset["case"])).toEqual(LABELS);
    for (const [i, entry] of realCasesIndex.cases.entries()) {
      const card = cards[i]!;
      expect(card.querySelector("h2")!.textContent).toBe(entry.label);
      expect(card.querySelector("h2")!.nextElementSibling!.textContent).toBe(entry.exploratory_label);
      expect(card.querySelector("h2 a")!.getAttribute("href")).toBe(`/cases/${entry.label}/`);
    }
  });

  it("shows a case's coarse description text, or the word for withheld, and nothing else about the company", async () => {
    const { container } = await list();
    for (const entry of realCasesIndex.cases) {
      const card = container.querySelector<HTMLElement>(`.case-card[data-case="${entry.label}"]`)!;
      const text = card.querySelector(".case-description")!.textContent;
      if (entry.description.status === "published") expect(text).toBe(entry.description.text);
      else expect(text).toBe(L.caseDescriptionStatus("withheld"));
    }
    expect(realCasesIndex.cases.filter((c) => c.description.status !== "published")).toHaveLength(1);
  });

  it("shows each model's label for each reading, through the labels map", async () => {
    const { container } = await list();
    for (const entry of realCasesIndex.cases) {
      const card = container.querySelector<HTMLElement>(`.case-card[data-case="${entry.label}"]`)!;
      const rows = [...card.querySelectorAll<HTMLElement>(".case-readings li")];
      expect(rows.map((r) => r.dataset["model"])).toEqual(MODELS); // the labels' order, Haiku 5.5 first
      for (const [i, model] of MODELS.entries()) {
        const expected = orderedReadings(fileOf(entry.label, model))
          .map((r) => `${readingName(r.reading)}: ${L.readingLabels[r.label]}`)
          .join("; ");
        expect(rows[i]!.textContent).toBe(`${modelName(model)}: ${expected}`);
      }
    }
  });

  it("says first, once, that every reading of every case is no good match, because that is what the files say", async () => {
    const { container } = await list();
    const sentence = container.querySelectorAll("[data-sentence]");
    expect(sentence).toHaveLength(1);
    expect(sentence[0]!.textContent).toBe(L.allNoGoodMatch);
    expect(before(sentence[0]!, container.querySelector(".shortfall")!)).toBe(true);
    expect(before(sentence[0]!, container.querySelector(".case-cards")!)).toBe(true);
  });

  it("drops that sentence when one reading in one file differs, and shows the differing label", async () => {
    const edits = {
      [path("pre-25", HAIKU)]: (body: CaseFile) => {
        body.readings[1]!.label = "match";
      },
    };
    const { container } = await list(HAIKU, editedApi(edits));
    expect(container.querySelector("[data-sentence]")).toBeNull();
    expect(container.querySelector(`.case-card[data-case="pre-25"]`)!.textContent).toContain(
      `${readingName("u1")}: ${L.readingLabels["match"]}`,
    );
    expect(container.querySelector(`.case-card[data-case="pre-11"]`)!.textContent).not.toMatch(
      /: match(;|$)/,
    );
  });

  it("shows the shortfall from cases.json beside the list: found and short by type, filled, and at most", async () => {
    const { container } = await list();
    const shortfall = realCasesIndex.shortfall;
    const section = container.querySelector<HTMLElement>(".shortfall")!;
    expect(before(section, container.querySelector(".case-cards")!)).toBe(true);
    expect(section.querySelector("h2")!.textContent).toBe(L.shortfallHeading);
    const rows = [...section.querySelectorAll<HTMLElement>("tbody tr")];
    expect(rows.map((r) => r.dataset["type"])).toEqual(Object.keys(shortfall.cases_by_type));
    for (const row of rows) {
      const type = row.dataset["type"]!;
      expect(row.querySelector("th")!.textContent).toBe(L.caseTypes[type]);
      const [found, short] = [...row.querySelectorAll("td")].map((td) => td.textContent);
      expect(found).toBe(String(shortfall.cases_by_type[type]));
      expect(short).toBe(String(shortfall.short_by_type[type]));
    }
    const facts = [...section.querySelectorAll(".x-facts dt")].map((dt) => [
      dt.textContent,
      dt.nextElementSibling!.textContent,
    ]);
    expect(facts).toEqual([
      [L.shortfallAtMost, String(shortfall.at_most)],
      [L.shortfallFilled, `${shortfall.filled} (${L.shortfallFilledNote})`],
    ]);
    // Today's shortfall, as a reviewer reads it: closure five, retool and AI none; retool two and AI one short.
    expect(shortfall.short_by_type).toEqual({ closure: 0, retool: 2, ai: 1 });
  });

  it("links to the two public selection logs on GitHub", async () => {
    const { container } = await list();
    const links = [...container.querySelectorAll<HTMLAnchorElement>(".shortfall .x-sources a")];
    expect(links.map((a) => a.getAttribute("href"))).toEqual(
      SELECTION_LOGS.map((l) => selectionLogUrl(l.path)),
    );
    expect(links.map((a) => a.textContent)).toEqual(SELECTION_LOGS.map((l) => L.selectionLogs[l.id]));
    for (const a of links) expect(a.getAttribute("rel")).toContain("noopener");
  });

  it("links to no memo file and shows no memo text: only links to the cases and the logs", async () => {
    const { container } = await list();
    for (const a of container.querySelectorAll("a")) {
      const href = a.getAttribute("href")!;
      expect(href, href).not.toMatch(/memo|\.jsonl|\/data\//i);
    }
  });

  it("carries the model in its links", async () => {
    const { container } = await list(GPT);
    for (const a of container.querySelectorAll<HTMLAnchorElement>(".case-card a")) {
      expect(a.getAttribute("href")).toBe(`${a.getAttribute("href")!.split("?")[0]}?model=${GPT}`);
    }
  });

  it("renders without error and fetches only paths under /data/", async () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const requested: string[] = [];
    await list(HAIKU, realApi(requested));
    expect(requested.length).toBeGreaterThan(10);
    for (const p of requested) expect(p.startsWith("/data/"), p).toBe(true);
    expect(errors).not.toHaveBeenCalled();
    errors.mockRestore();
  });
});

describe.each(LABELS)("/cases/%s/", (label) => {
  const entry = realCasesIndex.cases.find((c) => c.label === label)!;

  it("opens with the exploratory label, verbatim, before every reading, distance and count", async () => {
    const { container } = await page(label);
    const heading = container.querySelector("h1")!;
    const exploratory = heading.nextElementSibling!;
    expect(exploratory.className).toBe("exploratory-label");
    expect(exploratory.textContent).toBe(entry.exploratory_label);
    for (const later of [
      container.querySelector(".case-model")!,
      container.querySelector("table")!,
      container.querySelector(".distance-figure")!,
      container.querySelector("[data-reading]")!,
    ]) {
      expect(before(exploratory, later)).toBe(true);
    }
  });

  it("shows the description or withheld with its status, the dossier and the re-identification check as the file has them", async () => {
    const { container } = await page(label);
    const text = container.textContent!;
    if (entry.description.status === "published") expect(text).toContain(entry.description.text!);
    else {
      expect(text).toContain(L.caseDescriptionStatus(entry.description.status));
      expect(text).toContain(L.caseDescriptionWithheld);
    }
    expect(text).toContain(L.caseDossierStatus(entry.dossier.published));
    expect(text).toContain(entry.dossier.reason); // verbatim
    expect(text).toContain(L.caseReidentStatus(entry.reidentification.status));
    expect(text).toContain(entry.reidentification.reason);
    expect(text).toContain(`${L.caseThresholdLabel}: ${entry.reidentification.threshold}`);
  });

  it("shows the recognition probes, as the index has them", async () => {
    const { container } = await page(label);
    const rows = [...container.querySelectorAll("section")]
      .find((s) => s.querySelector("h2")?.textContent === L.caseProbesHeading)!
      .querySelectorAll("tbody tr");
    expect([...rows].map((r) => [...r.children].map((c) => c.textContent))).toEqual(
      entry.probes.map((p) => [String(p.set), modelName(p.model), String(p.calls), String(p.passed)]),
    );
  });

  it("shows the company's decision as the case codes it, and the dimensions matched on and left out", async () => {
    const { container } = await page(label);
    const file = fileOf(label, HAIKU);
    const text = container.textContent!;
    expect(text).toContain(L.caseCompanyChoice(L.choices[file.company.choice]!));
    for (const alt of file.company_alternatives) {
      for (const [lever, share] of Object.entries(alt.shares)) {
        expect(text).toContain(`${L.levers[lever]}: ${formatPercent(share)}`);
      }
    }
    const dims = container.querySelectorAll(".x-facts")[0]!.textContent!;
    for (const key of file.dimensions.observable)
      expect(dims).toContain(key === "choice" ? L.caseDimensionChoice : L.levers[key]!);
    for (const key of file.dimensions.excluded) expect(dims).toContain(L.levers[key]!);
    // Both models code the company's decision and the dimensions the same way.
    for (const model of MODELS) {
      expect(fileOf(label, model).company).toEqual(file.company);
      expect(fileOf(label, model).dimensions).toEqual(file.dimensions);
    }
  });

  it("shows, per model in the labels' order and per reading, the label word and the reason verbatim, and every final status", async () => {
    const { container } = await page(label);
    const sections = [...container.querySelectorAll<HTMLElement>(".case-model")];
    expect(sections.map((s) => s.dataset["model"])).toEqual(MODELS);
    for (const [i, model] of MODELS.entries()) {
      const file = fileOf(label, model);
      const section = sections[i]!;
      expect(section.querySelector("h2")!.textContent).toBe(modelName(model));
      expect(section.textContent).toContain(L.caseRunCounts(file.run_counts.runs));
      for (const [status, runs] of Object.entries(file.run_counts.by_final_status)) {
        expect(section.textContent).toContain(L.caseFinalStatus(status, runs));
      }
      const readings = [...section.querySelectorAll<HTMLElement>(".case-reading")];
      expect(readings.map((r) => r.dataset["reading"])).toEqual(orderedReadings(file).map((r) => r.reading));
      for (const [j, reading] of orderedReadings(file).entries()) {
        const block = readings[j]!;
        expect(block.querySelector("h3")!.textContent).toBe(readingName(reading.reading));
        expect(block.textContent).toContain(L.readingLabelIs(L.readingLabels[reading.label]!));
        expect(block.querySelector(".reading-reason")!.textContent).toBe(
          `${L.readingReason}: ${reading.reason}`,
        );
      }
    }
  });

  it("shows each model's memo counts and the reason for each held count, with no memo text and no link to one", async () => {
    const { container } = await page(label);
    for (const [i, model] of MODELS.entries()) {
      const section = container.querySelectorAll<HTMLElement>(".case-model")[i]!;
      const counts = fileOf(label, model).memo_counts;
      const facts = section.querySelector(".x-facts")!.textContent!;
      for (const [key, word] of Object.entries(L.memoCountLabels)) {
        expect(facts).toContain(`${word}${String(counts[key as keyof typeof counts])}`);
      }
      for (const [reason, n] of Object.entries(counts.held_by_reason)) {
        expect(section.textContent).toContain(`${L.heldReasons[reason]}: ${n}`);
      }
      expect(section.textContent).toContain(explorerHis.caseMemosHeld);
      expect(section.textContent).toContain(L.caseMemosNone);
    }
    for (const a of container.querySelectorAll("a")) {
      expect(a.getAttribute("href") ?? "", "no link on the page points at a memo").not.toMatch(
        /memo|\.jsonl|\/data\//i,
      );
    }
  });

  it("draws a distance chart for every reading, in a figure whose caption names the case, the model and the reading", async () => {
    const { container } = await page(label);
    for (const [i, model] of MODELS.entries()) {
      const file = fileOf(label, model);
      const figures = [
        ...container.querySelectorAll<HTMLElement>(".case-model")[i]!.querySelectorAll("figure"),
      ];
      expect(figures).toHaveLength(file.readings.length);
      for (const [j, reading] of orderedReadings(file).entries()) {
        const figure = figures[j]!;
        const caption = figure.querySelector("figcaption")!.textContent!;
        for (const part of [
          label,
          modelName(model),
          readingName(reading.reading),
          L.readingLabels[reading.label]!,
        ]) {
          expect(caption).toContain(part);
        }
        expect(figure.querySelector("[role=group]")!.getAttribute("aria-label")).toBe(
          L.distanceChartLabel(label, modelName(model), readingName(reading.reading)),
        );
      }
    }
  });

  it("shows the matcher notes exactly where their conditions hold, and a nearest goal exactly where it is not a tie", async () => {
    const { container } = await page(label);
    for (const [i, model] of MODELS.entries()) {
      const file = fileOf(label, model);
      const section = container.querySelectorAll<HTMLElement>(".case-model")[i]!;
      const blocks = [...section.querySelectorAll<HTMLElement>(".case-reading")];
      for (const [j, reading] of orderedReadings(file).entries()) {
        const block = blocks[j]!;
        const where = `${label} ${model} ${reading.reading}`;
        expect(block.querySelector("[data-note=tie]") !== null, where).toBe(reading.all_distances_equal);
        expect(block.querySelector("[data-note=one-line]") !== null, where).toBe(reading.one_observable_line);
        expect(block.querySelector("[data-nearest]") !== null, where).toBe(!reading.all_distances_equal);
        if (reading.all_distances_equal) {
          expect(block.textContent, where).not.toContain(
            L.nearestLine(L.objectiveNames[reading.nearest!]!, reading.nearest!),
          );
          expect(block.querySelector("[data-note=tie]")!.textContent).toBe(L.tieNote);
        } else {
          expect(block.querySelector<HTMLElement>("[data-nearest]")!.dataset["nearest"]).toBe(
            reading.nearest,
          );
        }
        if (reading.one_observable_line)
          expect(block.querySelector("[data-note=one-line]")!.textContent).toBe(L.oneLineNote);
      }
      // depends_on_reading is shown with the tie note exactly where some reading is a tie.
      const some = file.readings.some((r) => r.all_distances_equal);
      expect(section.querySelector("[data-note=depends-tie]") !== null, `${label} ${model}`).toBe(some);
      expect(section.querySelector("[data-depends]")!.getAttribute("data-depends")).toBe(
        file.depends_on_reading ? "yes" : "no",
      );
    }
  });
});

describe("the matcher notes on today's files (KNOWN-GAPS OPEN 2026-10-31)", () => {
  it("shows note 1 on Haiku 5.5's primary reading of all five cases, and nowhere on gpt-oss-120b", async () => {
    for (const label of LABELS) {
      const { container } = await page(label);
      const [haiku, gpt] = [...container.querySelectorAll<HTMLElement>(".case-model")];
      expect(haiku!.querySelectorAll("[data-note=tie]")).toHaveLength(1);
      expect(haiku!.querySelector(".case-reading[data-reading=primary] [data-note=tie]")).not.toBeNull();
      expect(gpt!.querySelectorAll("[data-note=tie]")).toHaveLength(0);
      expect(gpt!.querySelectorAll("[data-note=depends-tie]")).toHaveLength(0);
      cleanup();
    }
  });

  it("shows both notes on closure-19: note 1 once, on Haiku 5.5, and note 2 on u1 for both models", async () => {
    const { container } = await page("closure-19");
    expect(container.querySelectorAll("[data-note=tie]")).toHaveLength(1);
    expect(container.querySelectorAll("[data-note=one-line]")).toHaveLength(2);
    for (const section of container.querySelectorAll<HTMLElement>(".case-model")) {
      expect(section.querySelector(".case-reading[data-reading=u1] [data-note=one-line]")).not.toBeNull();
      expect(section.querySelector(".case-reading[data-reading=primary] [data-note=one-line]")).toBeNull();
    }
  });

  it("shows note 2 on no other case's reading", async () => {
    for (const label of LABELS.filter((l) => l !== "closure-19")) {
      const { container } = await page(label);
      expect(container.querySelectorAll("[data-note=one-line]"), label).toHaveLength(0);
      cleanup();
    }
  });

  it("explains depends_on_reading where it is inherited, and says the label is the same under every reading", async () => {
    const { container } = await page("closure-07");
    const haiku = container.querySelector<HTMLElement>('.case-model[data-model="haiku-5-5"]')!;
    const note = haiku.querySelector("[data-note=depends-tie]")!.textContent!;
    expect(note).toContain(L.dependsTieNote);
    expect(note).toContain(L.dependsSameLabel("no good match"));
    expect(haiku.querySelector("[data-depends]")!.getAttribute("data-depends")).toBe("yes");
  });
});

describe("the notes on an edited file (a condition the real files do not hold)", () => {
  it("shows note 1, no nearest goal and no gap for a reading edited to an exact tie, and the tie-break is not named", async () => {
    const tied = (body: CaseFile) => {
      const reading = body.readings[1]!;
      reading.all_distances_equal = true;
    };
    const { container } = await page("pre-25", editedApi({ [path("pre-25", GPT)]: tied }));
    const gpt = container.querySelector<HTMLElement>(`.case-model[data-model="${GPT}"]`)!;
    const u1 = gpt.querySelector<HTMLElement>(".case-reading[data-reading=u1]")!;
    expect(u1.querySelector("[data-note=tie]")).not.toBeNull();
    expect(u1.querySelector("[data-nearest]")).toBeNull();
    expect(gpt.querySelector("[data-note=depends-tie]")).not.toBeNull();
  });

  it("shows note 2, and a nearest goal with its gap and any tie, for a reading edited to one line", async () => {
    const edit = (body: CaseFile) => {
      const reading = body.readings[0]!;
      reading.one_observable_line = true;
      reading.tied_with = ["A", "B"];
    };
    const { container } = await page("pre-224", editedApi({ [path("pre-224", GPT)]: edit }));
    const primary = container.querySelector<HTMLElement>(
      `.case-model[data-model="${GPT}"] .case-reading[data-reading=primary]`,
    )!;
    expect(primary.querySelector("[data-note=one-line]")).not.toBeNull();
    expect(primary.textContent).toContain(L.tiedWith("A, B"));
    const real = fileOf("pre-224", GPT).readings[0]!;
    expect(primary.textContent).toContain(
      L.gapLine(
        real.gap!.second,
        formatDistance(real.gap!.estimate),
        formatDistance(real.gap!.low),
        formatDistance(real.gap!.high),
      ),
    );
  });
});

describe("the distance chart", () => {
  const file = fileOf("closure-07", GPT);
  const reading = file.readings[1]!;
  const render1 = () =>
    render(
      <DistanceChart
        caseLabel="closure-07"
        model={modelName(GPT)}
        readingName={readingName(reading.reading)}
        labelWord={L.readingLabels[reading.label]!}
        reading={reading}
        dStar={file.thresholds.d_star}
        alpha={file.thresholds.alpha}
        names={L.objectiveNames}
      />,
    );

  it("draws one row per goal: the distance as a dot, low to high as a line, on a 0 to 1 axis", () => {
    const { container } = render1();
    const rows = [...container.querySelectorAll<HTMLElement>(".distance-row[data-goal]")];
    expect(rows.map((r) => r.dataset["goal"])).toEqual(reading.distances.map((d) => d.objective_id));
    for (const [i, d] of reading.distances.entries()) {
      const row = rows[i]!;
      expect(row.querySelector("circle.d-dot")!.getAttribute("cx")).toBe(axisPercent(d.distance, 0, 1));
      const range = row.querySelector("line.d-range")!;
      expect(range.getAttribute("x1")).toBe(axisPercent(d.low, 0, 1));
      expect(range.getAttribute("x2")).toBe(axisPercent(d.high, 0, 1));
      expect(row.querySelectorAll("circle")).toHaveLength(1); // one goal to a plot area, never two
      expect(row.querySelector(".goal-name")!.textContent).toContain(`${L.objectiveNames[d.objective_id]}`);
      expect(row.querySelector(".goal-name")!.textContent).toContain(`(${d.objective_id})`); // named in text, not by color alone
    }
  });

  it("draws d_star as a rule and labels it as the no-good-match line", () => {
    const { container } = render1();
    for (const rule of container.querySelectorAll("line.x-rule")) {
      expect(rule.getAttribute("x1")).toBe(axisPercent(file.thresholds.d_star, 0, 1));
    }
    expect(container.querySelectorAll("line.x-rule")).toHaveLength(reading.distances.length);
    expect(container.querySelector("text.edge")!.textContent).toBe(
      L.distanceRule(formatDistance(file.thresholds.d_star)),
    );
    expect(container.textContent).toContain("no good match above 0.546");
  });

  it("puts every number in text beside its row, with the runs behind it", () => {
    const { container } = render1();
    const group = container.querySelector("[role=group]")!;
    expect(group.getAttribute("aria-label")).toBe(
      L.distanceChartLabel("closure-07", "gpt-oss-120b", "Alternative reading u1"),
    );
    for (const d of reading.distances) {
      const row = container.querySelector(`.distance-row[data-goal="${d.objective_id}"] .distance-numbers`)!;
      expect(row.textContent).toContain(
        L.distanceRowNumbers(formatDistance(d.distance), formatDistance(d.low), formatDistance(d.high)),
      );
      expect(row.textContent).toContain(L.distanceRuns(d.runs, d.choice_only_runs, d.undistanced_runs));
    }
  });

  it("keeps the case, the model and the reading in a crop of the figure alone", () => {
    const { container } = render1();
    const figure = container.querySelector("figure")!;
    for (const part of ["closure-07", "gpt-oss-120b", "Alternative reading u1", "no good match"]) {
      expect(figure.textContent).toContain(part);
    }
  });

  it("colors carry no verdict: no class on the chart names a result as good, bad, a win or a loss", () => {
    const { container } = render1();
    const classes = [...container.querySelectorAll("[class]")].flatMap((el) => [...el.classList]);
    expect(classes.length).toBeGreaterThan(5);
    expect(classes.filter((c) => /^(win|loss|good|bad|success|danger|error|fail|ok|match)/i.test(c))).toEqual(
      [],
    );
  });
});

describe("accessibility", () => {
  it("has no axe violations on /cases/ or on /cases/closure-19/ (both notes)", async () => {
    const cases = await list();
    expect(await violations(cases.container)).toEqual([]);
    cleanup();
    const one = await page("closure-19");
    expect(await violations(one.container)).toEqual([]);
  });
});
