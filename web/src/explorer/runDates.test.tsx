// Phase 7 step 2: the model and run dates on the results surfaces. Each expected line is built here from the index's
// own `runs` block, by a route that does not use format.ts (the browser's own calendar, in UTC), and the approved
// words are pinned as strings: a date on a page that is not the data's, a surface that lacks its line, or a line on a
// surface that should not carry one, fails a test.
import { cleanup, render, waitFor } from "@testing-library/react";
import type { RenderResult } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { againstWords } from "./againstWords";
import { CaseView, CasesView } from "./Cases";
import type { DataIndex, RunSpan } from "./data";
import { realApi, realCasesIndex, realIndex } from "./fixtures";
import { MemosView } from "./MemoReader";
import { ScenarioView } from "./ScenarioView";
import { Story } from "./Story";
import { StudiesView } from "./Studies";
import { STUDIES_AWARENESS_ID, STUDIES_THINKING_ID } from "./links";

afterEach(cleanup);

const HAIKU = "haiku-5-5";
const GPT = "gpt-oss-openrouter";
const MODELS = [HAIKU, GPT]; // the order the page shows them
const NAME: Record<string, string> = { [HAIKU]: "Haiku 5.5", [GPT]: "gpt-oss-120b" };
const SCENARIOS = realIndex.scenarios.map((s) => s.scenario_id);
const CASES = realCasesIndex.cases.map((c) => c.label);

const full = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
const monthDay = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });

function datesOf(span: RunSpan): string {
  if (span.from === span.to) return full(span.from);
  expect(span.from.slice(0, 4)).toBe(span.to.slice(0, 4)); // a different-year range is format.test.ts's
  return `${monthDay(span.from)} to ${full(span.to)}`;
}

/** The approved words (Phase 7 step 2, his "yes" of 2026-11-23), built from a span the data holds. */
function runsLine(model: string, span: RunSpan | undefined): string {
  expect(span).toBeDefined();
  const started = span!.basis === "run_log" ? "started " : "";
  return `Runs: ${NAME[model]}, ${started}${datesOf(span!)} (UTC).`;
}
const retiredLine = (model: string, iso: string) =>
  `${NAME[model]} was retired on ${full(iso)}; these results describe it as it was.`;

const linesIn = (root: ParentNode): string[] =>
  [...root.querySelectorAll(".runs-line")].map((e) => e.textContent ?? "");

function withRuns(patch: Partial<DataIndex["runs"]>): DataIndex {
  return { ...realIndex, runs: { ...realIndex.runs, ...patch } };
}
const RETIRED_HAIKU = withRuns({ retired_on: { ...realIndex.runs.retired_on, [HAIKU]: "2027-10-07" } });

async function scenario(id: string, model: string, index: DataIndex = realIndex): Promise<RenderResult> {
  const rendered = render(<ScenarioView id={id} index={index} model={model} data={realApi()} />);
  await waitFor(() => expect(rendered.container.querySelector(".x-loaded")).not.toBeNull());
  return rendered;
}

async function story(index: DataIndex = realIndex): Promise<RenderResult> {
  const rendered = render(<Story index={index} casesIndex={realCasesIndex} data={realApi()} />);
  await waitFor(() => expect(rendered.container.querySelectorAll(".story-wait")).toHaveLength(0));
  return rendered;
}

async function studies(model: string, index: DataIndex = realIndex): Promise<RenderResult> {
  const rendered = render(<StudiesView index={index} model={model} data={realApi()} />);
  await waitFor(() => expect(rendered.container.querySelector(".awareness-model")).not.toBeNull());
  return rendered;
}

async function cases(model: string, index: DataIndex = realIndex): Promise<RenderResult> {
  const rendered = render(
    <CasesView index={index} casesIndex={realCasesIndex} model={model} data={realApi()} />,
  );
  await waitFor(() => expect(rendered.container.querySelector(".case-readings")).not.toBeNull());
  return rendered;
}

async function caseView(label: string, index: DataIndex = realIndex): Promise<RenderResult> {
  const rendered = render(
    <CaseView label={label} index={index} casesIndex={realCasesIndex} data={realApi()} />,
  );
  await waitFor(() => expect(rendered.container.querySelectorAll(".case-model").length).toBe(MODELS.length));
  return rendered;
}

async function memos(search: string, model: string, index: DataIndex = realIndex): Promise<RenderResult> {
  const rendered = render(<MemosView index={index} model={model} search={search} data={realApi()} />);
  await waitFor(() => expect(rendered.container.querySelector(".runs-line")).not.toBeNull());
  return rendered;
}

describe("the data these tests start from", () => {
  it("holds the dates the run records gave (the Python tests recompute them from the raw files)", () => {
    expect(realIndex.runs.grid[HAIKU]).toEqual({ from: "2026-10-14", to: "2026-10-14", basis: "sessions" });
    expect(realIndex.runs.grid[GPT]).toEqual({ from: "2026-10-14", to: "2026-10-14", basis: "sessions" });
    expect(realIndex.runs.awareness[GPT]).toEqual({ from: "2026-10-15", to: "2026-10-15", basis: "calls" });
    expect(realIndex.runs.cases["pre-11"]?.[GPT]).toEqual({
      from: "2026-10-29",
      to: "2026-10-30",
      basis: "run_log",
    });
  });
});

describe("the words are the approved ones", () => {
  it("reads as drafted, for a day, a range, a case's session starts and a retirement", () => {
    expect(runsLine(HAIKU, { from: "2026-10-14", to: "2026-10-14", basis: "sessions" })).toBe(
      "Runs: Haiku 5.5, October 14, 2026 (UTC).",
    );
    expect(runsLine(GPT, { from: "2026-10-29", to: "2026-10-30", basis: "run_log" })).toBe(
      "Runs: gpt-oss-120b, started October 29 to October 30, 2026 (UTC).",
    );
    expect(retiredLine(HAIKU, "2027-10-07")).toBe(
      "Haiku 5.5 was retired on October 7, 2027; these results describe it as it was.",
    );
  });
});

describe("the scenario view", () => {
  it.each(MODELS.flatMap((model) => SCENARIOS.map((id) => [model, id] as const)))(
    "%s %s states its model's grid dates, once, and nothing about retirement",
    async (model, id) => {
      const { container } = await scenario(id, model);
      expect(linesIn(container)).toEqual([runsLine(model, realIndex.runs.grid[model])]);
      expect(container.textContent).not.toContain("retired");
    },
  );

  it("takes the dates from the data: change the data and the page changes with it", async () => {
    const moved = withRuns({
      grid: { ...realIndex.runs.grid, [HAIKU]: { from: "2031-03-04", to: "2031-03-05", basis: "sessions" } },
    });
    const { container } = await scenario("s1", HAIKU, moved);
    expect(linesIn(container)).toEqual(["Runs: Haiku 5.5, March 4 to March 5, 2031 (UTC)."]);
    expect(container.textContent).not.toContain("October 14, 2026");
  });

  it("says nothing when the data holds no dates for the model, rather than guess", async () => {
    const none = withRuns({ grid: {} });
    const { container } = await scenario("s1", HAIKU, none);
    expect(linesIn(container)).toEqual([]);
  });
});

describe("the story", () => {
  it("states the grid dates in the first decision, under each model in the second, and in the section against the thesis", async () => {
    const { container } = await story();
    const inside = (id: string) => linesIn(container.querySelector(`#${id}`)!);
    expect(inside("beat-s1")).toEqual([runsLine(HAIKU, realIndex.runs.grid[HAIKU])]);
    expect(inside("beat-second-model")).toEqual(MODELS.map((m) => runsLine(m, realIndex.runs.grid[m])));
    expect(inside(againstWords.sectionId)).toEqual(MODELS.map((m) => runsLine(m, realIndex.runs.grid[m])));
    // The case cards only summarize and link to the case pages, which carry the lines (his "yes").
    expect(inside("beat-cases")).toEqual([]);
    expect(inside("beat-comparisons")).toEqual([]);
    expect(inside("beat-other-scenarios")).toEqual([]);
    expect(linesIn(container)).toHaveLength(1 + 2 + 2);
  });

  it("carries a retirement line after each of the retired model's dates, and none for the other model", async () => {
    const { container } = await story(RETIRED_HAIKU);
    const lines = linesIn(container);
    expect(lines.filter((l) => l === retiredLine(HAIKU, "2027-10-07"))).toHaveLength(3);
    expect(lines.filter((l) => l.includes("retired"))).toHaveLength(3);
    for (const [at, l] of lines.entries()) {
      if (l.includes("retired")) expect(lines[at - 1]).toBe(runsLine(HAIKU, realIndex.runs.grid[HAIKU]));
    }
  });

  it("says nothing of retirement while the data holds no date", async () => {
    const { container } = await story();
    expect(container.textContent).not.toContain("retired");
  });
});

describe("the studies page", () => {
  it.each(MODELS)("states the sub-study's dates, and the awareness probe's dates for %s", async (model) => {
    const { container } = await studies(model);
    const inside = (id: string) => linesIn(container.querySelector(`#${id}`)!);
    expect(inside(STUDIES_THINKING_ID)).toEqual([runsLine(HAIKU, realIndex.runs.thinking[HAIKU])]);
    expect(inside(STUDIES_AWARENESS_ID)).toEqual([runsLine(model, realIndex.runs.awareness[model])]);
    expect(linesIn(container)).toHaveLength(2);
  });

  it("shows the second model's probe on its own date, which is the next UTC day", async () => {
    const { container } = await studies(GPT);
    expect(linesIn(container.querySelector(`#${STUDIES_AWARENESS_ID}`)!)).toEqual([
      "Runs: gpt-oss-120b, October 15, 2026 (UTC).",
    ]);
  });
});

describe("the cases pages", () => {
  it.each(MODELS)(
    "the list states each case's session starts for both models (page model %s)",
    async (page) => {
      const { container } = await cases(page);
      for (const label of CASES) {
        const card = container.querySelector(`[data-case="${label}"]`)!;
        expect(linesIn(card)).toEqual(MODELS.map((m) => runsLine(m, realIndex.runs.cases[label]?.[m])));
      }
      expect(linesIn(container)).toHaveLength(CASES.length * MODELS.length);
    },
  );

  it.each(CASES)("%s states, under each model's heading, that model's session starts", async (label) => {
    const { container } = await caseView(label);
    for (const m of MODELS) {
      const section = container.querySelector(`.case-model[data-model="${m}"]`)!;
      expect(linesIn(section)).toEqual([runsLine(m, realIndex.runs.cases[label]?.[m])]);
    }
    expect(linesIn(container)).toHaveLength(MODELS.length);
  });

  it("shows the one case that took two UTC days as a range", async () => {
    const { container } = await caseView("pre-11");
    const section = container.querySelector(`.case-model[data-model="${GPT}"]`)!;
    expect(linesIn(section)).toEqual(["Runs: gpt-oss-120b, started October 29 to October 30, 2026 (UTC)."]);
  });

  it("carries the retirement line under the retired model's heading on a case page and in the list", async () => {
    const page = await caseView("pre-11", RETIRED_HAIKU);
    const section = page.container.querySelector(`.case-model[data-model="${HAIKU}"]`)!;
    expect(linesIn(section)).toEqual([
      runsLine(HAIKU, realIndex.runs.cases["pre-11"]?.[HAIKU]),
      retiredLine(HAIKU, "2027-10-07"),
    ]);
    expect(linesIn(page.container.querySelector(`.case-model[data-model="${GPT}"]`)!)).toHaveLength(1);
    cleanup();
    const list = await cases(HAIKU, RETIRED_HAIKU);
    expect(linesIn(list.container).filter((l) => l.includes("retired"))).toHaveLength(CASES.length);
  });
});

describe("the memo reader", () => {
  it.each(MODELS)("states the grid dates for the %s memos", async (model) => {
    const { container } = await memos("", model);
    expect(linesIn(container)).toEqual([runsLine(model, realIndex.runs.grid[model])]);
  });

  it("states the sub-study's dates for the thinking memos", async () => {
    const { container } = await memos("?kind=thinking", HAIKU);
    expect(linesIn(container)).toEqual([runsLine(HAIKU, realIndex.runs.thinking[HAIKU])]);
  });

  it("states nothing where it shows no memos (a refused address)", async () => {
    const rendered = render(
      <MemosView index={realIndex} model={GPT} search="?kind=thinking" data={realApi()} />,
    );
    await waitFor(() => expect(rendered.container.querySelector("[data-refusal]")).not.toBeNull());
    expect(linesIn(rendered.container)).toEqual([]);
  });

  it("carries the retirement line after the dates when the data names one", async () => {
    const { container } = await memos("", HAIKU, RETIRED_HAIKU);
    expect(linesIn(container)).toEqual([
      runsLine(HAIKU, realIndex.runs.grid[HAIKU]),
      retiredLine(HAIKU, "2027-10-07"),
    ]);
  });
});

describe("each surface reads its own kind of run, even when the dates differ", () => {
  // The real grid and sub-study share a date, so a surface reading the wrong kind would still pass above.
  const apart = withRuns({
    grid: { ...realIndex.runs.grid, [HAIKU]: { from: "2031-03-04", to: "2031-03-04", basis: "sessions" } },
    thinking: { [HAIKU]: { from: "2032-05-06", to: "2032-05-06", basis: "sessions" } },
    awareness: {
      ...realIndex.runs.awareness,
      [HAIKU]: { from: "2033-07-08", to: "2033-07-08", basis: "calls" },
    },
    cases: {
      ...realIndex.runs.cases,
      "pre-11": {
        ...realIndex.runs.cases["pre-11"],
        [HAIKU]: { from: "2034-09-10", to: "2034-09-10", basis: "run_log" },
      },
    },
  });

  it("the memo reader: grid memos the grid's date, thinking memos the sub-study's", async () => {
    expect(linesIn((await memos("", HAIKU, apart)).container)).toEqual([
      "Runs: Haiku 5.5, March 4, 2031 (UTC).",
    ]);
    cleanup();
    expect(linesIn((await memos("?kind=thinking", HAIKU, apart)).container)).toEqual([
      "Runs: Haiku 5.5, May 6, 2032 (UTC).",
    ]);
  });

  it("the studies page: the sub-study's date, and the probe's own, apart from the grid's", async () => {
    const { container } = await studies(HAIKU, apart);
    expect(linesIn(container.querySelector(`#${STUDIES_THINKING_ID}`)!)).toEqual([
      "Runs: Haiku 5.5, May 6, 2032 (UTC).",
    ]);
    expect(linesIn(container.querySelector(`#${STUDIES_AWARENESS_ID}`)!)).toEqual([
      "Runs: Haiku 5.5, July 8, 2033 (UTC).",
    ]);
  });

  it("a case page and the scenario view: the case's session start, and the grid's date", async () => {
    const page = await caseView("pre-11", apart);
    expect(linesIn(page.container.querySelector(`.case-model[data-model="${HAIKU}"]`)!)).toEqual([
      "Runs: Haiku 5.5, started September 10, 2034 (UTC).",
    ]);
    cleanup();
    expect(linesIn((await scenario("s1", HAIKU, apart)).container)).toEqual([
      "Runs: Haiku 5.5, March 4, 2031 (UTC).",
    ]);
  });
});
