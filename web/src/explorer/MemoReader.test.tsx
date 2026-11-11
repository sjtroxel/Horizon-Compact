import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { explorerLabels as L } from "./copy";
import type { DataApi, MemoRow } from "./data";
import { WEB_ROOT, readMemoRows, realApi, realGrids, realIndex, realMemoIndex } from "./fixtures";
import { MemoCard, MemosView } from "./MemoReader";
import { modelName } from "./models";
import { memoHref } from "./route";
import { RunsTable } from "./RunDetails";

afterEach(cleanup);

const HAIKU = "haiku-5-5";
const GPT = "gpt-oss-openrouter";
const manifest = realMemoIndex.raw_manifest;

async function reader(search: string, model = HAIKU, data: DataApi = realApi()) {
  const rendered = render(<MemosView index={realIndex} model={model} search={search} data={data} />);
  await rendered.findByRole("article");
  return rendered;
}

/** A view that ends in a plain message, not a card. */
async function refused(search: string, model = HAIKU) {
  const rendered = render(<MemosView index={realIndex} model={model} search={search} data={realApi()} />);
  const box = await waitFor(() => {
    const found = rendered.container.querySelector<HTMLElement>("[data-refusal]");
    expect(found).not.toBeNull();
    return found!;
  });
  return { ...rendered, box };
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

const cardOf = (container: HTMLElement) => container.querySelector<HTMLElement>("article.memo-card")!;
const rowsOf = (path: string) => readMemoRows(path);

describe("the memo card shows the text exactly", () => {
  // One cell of each kind and each model. gpt-oss-120b's s1 goal B holds runs that left no memo.
  it.each([
    ["grid", HAIKU, "s1", "A"],
    ["grid", GPT, "s1", "B"],
    ["thinking", HAIKU, "s1", "C"],
  ] as const)("on every row of the %s cell of %s %s %s", (kind, model, scenario, goal) => {
    const rows = rowsOf(`${kind}/${model}/${scenario}/${goal}.jsonl`);
    expect(rows.length).toBeGreaterThan(10);
    const { container } = render(
      <>
        {rows.map((row) => (
          <MemoCard key={row.run_id} row={row} model={model} goal={goal} kind={kind} manifest={manifest} />
        ))}
      </>,
    );
    const cards = [...container.querySelectorAll<HTMLElement>("article.memo-card")];
    expect(cards).toHaveLength(rows.length);
    for (const [i, row] of rows.entries()) {
      const text = cards[i]!.querySelector(".memo-text");
      if (row.memo === null) {
        expect(text, row.run_id).toBeNull();
        expect(cards[i]!.querySelector(".memo-none")!.textContent).toBe(L.memoLeftNone);
      } else {
        expect(text!.textContent, row.run_id).toBe(row.memo); // not one character changed, trimmed or added
      }
    }
  });

  it("keeps leading and trailing space, blank lines and tabs, and does not read the text as Markdown", () => {
    const memo = "  leading\n\n  # Not a heading **not bold** [not a link](x)\n\ttab\t \n\n\ntrailing  \n";
    const row: MemoRow = { ...rowsOf("grid/haiku-5-5/s1/A.jsonl")[0]!, memo };
    const { container } = render(
      <MemoCard row={row} model={HAIKU} goal="A" kind="grid" manifest={manifest} />,
    );
    const text = container.querySelector(".memo-text")!;
    expect(text.textContent).toBe(memo);
    expect(text.children).toHaveLength(0); // no element made from the text
    expect(container.querySelector("h1, h2, h3, strong, em, a, ul, code")).toBeNull();
  });

  it("is a document, not a quote or speech: no quote elements, no quotation marks added, no italics", () => {
    const row = rowsOf("grid/haiku-5-5/s1/A.jsonl")[0]!;
    const { container } = render(
      <MemoCard row={row} model={HAIKU} goal="A" kind="grid" manifest={manifest} />,
    );
    expect(container.querySelector("blockquote, q, cite, em, i")).toBeNull();
    const card = cardOf(container);
    expect(card.textContent).not.toMatch(/[“”"]/);
    const css = readFileSync(resolve(WEB_ROOT, "src/explorer/explorer.css"), "utf8");
    const rule = (selector: string) => {
      const start = css.indexOf(`\n${selector} {`);
      expect(start, selector).toBeGreaterThan(-1);
      return css.slice(start, css.indexOf("}", start));
    };
    expect(rule(".memo-text")).toContain("white-space: pre-wrap");
    for (const selector of [".memo-card", ".memo-text", ".view .memo-label"]) {
      expect(rule(selector)).not.toMatch(/font-style:\s*italic|quotes:|border-left/);
    }
    // No rule styles a memo as a quote: no selector of the memo card names a blockquote.
    const selectors = [...css.replace(/\/\*[\s\S]*?\*\//g, "").matchAll(/([^{}]+)\{/g)].map((m) => m[1]!);
    expect(selectors.filter((sel) => /\.memo-|\.reply-card/.test(sel))).not.toHaveLength(0);
    expect(
      selectors.filter((sel) => /\.(memo-|reply-card)/.test(sel) && /blockquote|\bq\b/.test(sel)),
    ).toEqual([]);
  });

  it("carries its label inside the card, first, with the model, the goal, the fictional company and the run id", () => {
    const row = rowsOf("grid/gpt-oss-openrouter/s2/D.jsonl")[3]!;
    const { container } = render(<MemoCard row={row} model={GPT} goal="D" kind="grid" manifest={manifest} />);
    const card = cardOf(container);
    expect(card.firstElementChild!.className).toBe("memo-label");
    const label = card.firstElementChild!.textContent!;
    expect(label).toBe(L.memoCardLabel("gpt-oss-120b", "D", L.objectiveNames["D"]!, false));
    for (const part of [
      "gpt-oss-120b",
      "goal D",
      "Everyone with a stake, long term",
      "fictional company",
      "not the project",
    ]) {
      expect(label).toContain(part);
    }
    expect(card.textContent).toContain(row.run_id);
    expect(card.querySelector("[aria-labelledby]") ?? card.getAttribute("aria-labelledby")).toBeTruthy();
  });

  it("says thinking was on for the sub-study's memos and only for those", () => {
    const row = rowsOf("thinking/haiku-5-5/s1/A.jsonl")[0]!;
    const thinking = render(
      <MemoCard row={row} model={HAIKU} goal="A" kind="thinking" manifest={manifest} />,
    );
    expect(cardOf(thinking.container).textContent).toContain("Thinking was on for this run");
    cleanup();
    const grid = render(<MemoCard row={row} model={HAIKU} goal="A" kind="grid" manifest={manifest} />);
    expect(cardOf(grid.container).textContent).not.toContain("Thinking was on");
  });

  it("shows the run id, wording, repeat and status, what the text is from, and the source records under it", () => {
    const row = rowsOf("grid/haiku-5-5/s1/A.jsonl")[1]!;
    const { container } = render(
      <MemoCard row={row} model={HAIKU} goal="A" kind="grid" manifest={manifest} />,
    );
    const card = cardOf(container);
    const meta = card.querySelector(".memo-meta")!.textContent!;
    for (const part of [row.run_id, row.wording_id, String(row.repeat), row.status, L.memoSources["memo"]!]) {
      expect(meta).toContain(part);
    }
    const sources = card.querySelector(".memo-sources")!;
    expect(sources.textContent).toContain(L.memoSourceNote(manifest.path, manifest.sha256));
    for (const part of [row.final.key, row.final.sha256, row.attempt.key, row.attempt.sha256]) {
      expect(sources.textContent).toContain(part);
    }
    expect(
      card.querySelector(".memo-text")!.compareDocumentPosition(sources) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});

describe("the reader", () => {
  it("shows s1, goal A and the first run when nothing is chosen", async () => {
    const { container } = await reader("");
    const first = rowsOf("grid/haiku-5-5/s1/A.jsonl")[0]!;
    expect(container.querySelector("h1")).not.toBeNull();
    expect(cardOf(container).dataset["run"]).toBe(first.run_id);
    expect(cardOf(container).querySelector(".memo-text")!.textContent).toBe(first.memo);
    expect(cardOf(container).textContent).toContain("goal A");
  });

  it("shows the run the query names, on the model the query names", async () => {
    const rows = rowsOf("grid/gpt-oss-openrouter/s3/E.jsonl");
    const row = rows[7]!;
    const { container } = await reader(`?kind=grid&scenario=s3&objective=E&run=${row.run_id}`, GPT);
    expect(cardOf(container).dataset["run"]).toBe(row.run_id);
    expect(cardOf(container).textContent).toContain(modelName(GPT));
    expect(cardOf(container).querySelector(".memo-text")!.textContent).toBe(row.memo);
  });

  it("shows a run that left no memo with its status and a label, and nothing in the text's place", async () => {
    const rows = rowsOf("grid/gpt-oss-openrouter/s1/B.jsonl");
    const row = rows.find((r) => r.memo === null)!;
    const { container } = await reader(`?kind=grid&scenario=s1&objective=B&run=${row.run_id}`, GPT);
    const card = cardOf(container);
    expect(card.querySelector(".memo-text")).toBeNull();
    expect(card.querySelector(".memo-none")!.textContent).toBe(L.memoLeftNone);
    expect(card.querySelector(".memo-meta")!.textContent).toContain(row.status);
    expect(card.textContent).not.toContain(L.memoSource); // no "Text from": there is no text
  });

  it("opens the thinking sub-study's memos, labeled", async () => {
    const row = rowsOf("thinking/haiku-5-5/s1/E.jsonl")[2]!;
    const { container } = await reader(`?kind=thinking&scenario=s1&objective=E&run=${row.run_id}`);
    expect(cardOf(container).textContent).toContain("Thinking was on");
    expect(cardOf(container).querySelector(".memo-text")!.textContent).toBe(row.memo);
  });

  it("links to the cell's file under /data/memos/, labeled", async () => {
    const { container } = await reader("?kind=grid&scenario=s2&objective=C");
    const link = within(container).getByRole("link", { name: L.memoFileLink });
    expect(link.getAttribute("href")).toBe("/data/memos/grid/haiku-5-5/s2/C.jsonl");
    expect(realMemoIndex.files).toContain("grid/haiku-5-5/s2/C.jsonl");
  });

  it("lists the cell's runs, one link each, and marks the shown one", async () => {
    const rows = rowsOf("grid/haiku-5-5/s1/A.jsonl");
    const { container } = await reader("?kind=grid&scenario=s1&objective=A");
    const items = [...container.querySelectorAll<HTMLAnchorElement>(".memo-runs a")];
    expect(items.map((a) => a.getAttribute("href"))).toEqual(
      rows.map((r) => memoHref({ kind: "grid", scenario: "s1", objective: "A", run: r.run_id }, HAIKU)),
    );
    expect(items.filter((a) => a.getAttribute("aria-current") === "true")).toHaveLength(1);
    expect(items[0]!.getAttribute("aria-current")).toBe("true");
    expect(items[0]!.textContent).toContain(
      L.memoRunLine(rows[0]!.wording_id, rows[0]!.repeat, rows[0]!.status),
    );
  });

  it("moves to the previous and the next run by links that keep every parameter and the model", async () => {
    const rows = rowsOf("grid/gpt-oss-openrouter/s2/B.jsonl");
    const href = (r: MemoRow) =>
      memoHref({ kind: "grid", scenario: "s2", objective: "B", run: r.run_id }, GPT);
    const first = await reader("?kind=grid&scenario=s2&objective=B", GPT);
    const nav = () => within(first.container).getByRole("navigation", { name: L.memoNavLabel });
    expect(within(nav()).queryByText(L.memoPrevious)).toBeNull();
    expect(within(nav()).getByText(L.memoNone)).toBeTruthy();
    expect(within(nav()).getByText(L.memoNext).getAttribute("href")).toBe(href(rows[1]!));
    cleanup();

    const middle = await reader(`?kind=grid&scenario=s2&objective=B&run=${rows[5]!.run_id}`, GPT);
    const midNav = within(middle.container).getByRole("navigation", { name: L.memoNavLabel });
    expect(within(midNav).getByText(L.memoPrevious).getAttribute("href")).toBe(href(rows[4]!));
    expect(within(midNav).getByText(L.memoNext).getAttribute("href")).toBe(href(rows[6]!));
    cleanup();

    const last = await reader(`?kind=grid&scenario=s2&objective=B&run=${rows.at(-1)!.run_id}`, GPT);
    const lastNav = within(last.container).getByRole("navigation", { name: L.memoNavLabel });
    expect(within(lastNav).getByText(L.memoPrevious).getAttribute("href")).toBe(href(rows.at(-2)!));
    expect(within(lastNav).queryByText(L.memoNext)).toBeNull();
    expect(within(lastNav).getByText(L.memoNoneNext)).toBeTruthy();
  });
});

describe("the choosers are links, so every choice is a URL", () => {
  const group = (container: HTMLElement, name: string) => within(container).getByRole("group", { name });
  const hrefs = (el: HTMLElement) =>
    within(el)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"));
  const current = (el: HTMLElement) =>
    within(el)
      .getAllByRole("link")
      .filter((a) => a.getAttribute("aria-current") === "true")
      .map((a) => a.textContent);

  it("mark the current kind, scenario and goal with aria-current, and offer every scenario and goal", async () => {
    const { container } = await reader("?kind=grid&scenario=s2&objective=C");
    expect(current(group(container, L.memoKindLabel))).toEqual([L.memoKinds["grid"]]);
    expect(current(group(container, L.memoScenarioLabel))).toEqual(["s2"]);
    expect(current(group(container, L.memoGoalLabel))).toEqual([`${L.objectiveNames["C"]} (C)`]);
    expect(hrefs(group(container, L.memoScenarioLabel))).toEqual(
      ["s1", "s2", "s3", "s4"].map((s) => memoHref({ kind: "grid", scenario: s, objective: "C" }, HAIKU)),
    );
    expect(hrefs(group(container, L.memoGoalLabel))).toEqual(
      ["A", "B", "C", "D", "E"].map((g) => memoHref({ kind: "grid", scenario: "s2", objective: g }, HAIKU)),
    );
  });

  it("carry the model in every link", async () => {
    const { container } = await reader("?kind=grid&scenario=s4&objective=D", GPT);
    for (const a of within(container).getAllByRole("link")) {
      const href = a.getAttribute("href")!;
      if (href.startsWith("/memos/")) expect(href, href).toContain(`model=${GPT}`);
    }
  });

  it("offer the thinking sub-study only on the model it ran on, and open it on its first cell from a scenario it lacks", async () => {
    const haiku = await reader("?kind=grid&scenario=s2&objective=C");
    const kinds = group(haiku.container, L.memoKindLabel);
    expect(hrefs(kinds)).toEqual([
      memoHref({ kind: "grid", scenario: "s2", objective: "C" }, HAIKU),
      memoHref({ kind: "thinking", scenario: "s1", objective: "A" }, HAIKU),
    ]);
    cleanup();
    const other = await reader("?kind=grid&scenario=s2&objective=C", GPT);
    expect(within(group(other.container, L.memoKindLabel)).getAllByRole("link")).toHaveLength(1);
  });

  it("within the sub-study, offer s1 only", async () => {
    const { container } = await reader("?kind=thinking&scenario=s1&objective=B");
    expect(hrefs(group(container, L.memoScenarioLabel))).toEqual([
      memoHref({ kind: "thinking", scenario: "s1", objective: "B" }, HAIKU),
    ]);
  });
});

describe("a choice the reader cannot show is a plain message and a link to the default", () => {
  it.each([
    ["?kind=other", "kind"],
    ["?scenario=s9", "scenario"],
    ["?objective=Z", "objective"],
    ["?kind=thinking&scenario=s2", "cell"],
  ])("%s", async (search, why) => {
    const { box, container } = await refused(search);
    expect(box.dataset["refusal"]).toBe(why);
    expect(within(box).getByText(L.memoMessages[why]!)).toBeTruthy();
    const link = within(box).getByRole("link", { name: L.memoToFirst });
    expect(link.getAttribute("href")).toBe(memoHref({ kind: "grid", scenario: "s1", objective: "A" }, HAIKU));
    expect(container.querySelector("article")).toBeNull();
  });

  it("a run that is not in the cell", async () => {
    const { box } = await refused("?kind=grid&scenario=s1&objective=A&run=r-nosuchrun");
    expect(box.dataset["refusal"]).toBe("run");
    expect(within(box).getByText(L.memoMessages["run"]!)).toBeTruthy();
    expect(within(box).getByRole("link", { name: L.memoToFirst }).getAttribute("href")).toBe(
      memoHref({ kind: "grid", scenario: "s1", objective: "A" }, HAIKU),
    );
  });

  it("the default link names the model that is chosen", async () => {
    const { box } = await refused("?kind=other", GPT);
    expect(within(box).getByRole("link", { name: L.memoToFirst }).getAttribute("href")).toBe(
      memoHref({ kind: "grid", scenario: "s1", objective: "A" }, GPT),
    );
  });

  it("the thinking kind on gpt-oss-120b says the sub-study ran on Haiku 5.5 only, and links to it", async () => {
    const { box } = await refused("?kind=thinking", GPT);
    expect(box.dataset["refusal"]).toBe("thinking_model");
    expect(box.textContent).toContain(L.memoThinkingOnly("Haiku 5.5"));
    const link = within(box).getByRole("link", { name: L.memoSeeSubStudy });
    expect(link.getAttribute("href")).toBe(`/studies/?model=${GPT}#thinking-sub-study`);
  });
});

describe("every view renders from the real files, for both models", () => {
  it.each([HAIKU, GPT])("%s", async (model) => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const warnings = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { container } = await reader("", model);
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(cardOf(container).textContent).toContain(modelName(model));
    expect(errors).not.toHaveBeenCalled();
    expect(warnings).not.toHaveBeenCalled();
    errors.mockRestore();
    warnings.mockRestore();
  });

  it("fetches only paths under /data/", async () => {
    const requested: string[] = [];
    const { container } = await reader("?kind=thinking&scenario=s1&objective=A", HAIKU, realApi(requested));
    expect(container.querySelector("article")).not.toBeNull();
    expect(requested.length).toBeGreaterThan(1);
    for (const path of requested) expect(path.startsWith("/data/"), path).toBe(true);
  });
});

describe("a run id in a table is a link to its memo", () => {
  it("in the scenario view's runs table, on the file's own model and set", () => {
    const file = realGrids.find((g) => g.label === `grid ${GPT} s3`)!.file;
    const { container } = render(<RunsTable file={file} kind="grid" />);
    const links = [...container.querySelectorAll<HTMLAnchorElement>("th.mono a")];
    expect(links).toHaveLength(file.descriptive.per_run.length);
    for (const [i, run] of file.descriptive.per_run.entries()) {
      expect(links[i]!.textContent).toBe(run.run_id);
      expect(links[i]!.getAttribute("href")).toBe(
        memoHref({ kind: "grid", scenario: "s3", objective: run.objective_id, run: run.run_id }, GPT),
      );
    }
  });

  it("has a memo in the reader for every run of every grid and sub-study file", () => {
    let checked = 0;
    for (const { label, file } of realGrids) {
      const kind = label.startsWith("thinking") ? "thinking" : "grid";
      const byGoal = new Map<string, Set<string>>();
      for (const run of file.descriptive.per_run) {
        let ids = byGoal.get(run.objective_id);
        if (ids === undefined) {
          ids = new Set(
            rowsOf(`${kind}/${file.model_key}/${file.scenario_id}/${run.objective_id}.jsonl`).map(
              (r) => r.run_id,
            ),
          );
          byGoal.set(run.objective_id, ids);
        }
        expect(ids.has(run.run_id), `${label} ${run.run_id}`).toBe(true);
        checked = checked + 1;
      }
    }
    expect(checked).toBeGreaterThan(2000);
  });
});

describe("accessibility", () => {
  it("has no axe violations on a memo with text, or on one without", async () => {
    const withText = await reader("?kind=grid&scenario=s1&objective=A");
    expect(await violations(withText.container)).toEqual([]);
    cleanup();
    const row = rowsOf("grid/gpt-oss-openrouter/s1/B.jsonl").find((r) => r.memo === null)!;
    const without = await reader(`?kind=grid&scenario=s1&objective=B&run=${row.run_id}`, GPT);
    expect(without.container.querySelector(".memo-text")).toBeNull();
    expect(await violations(without.container)).toEqual([]);
  });

  it("has no axe violations on a refusal", async () => {
    const { container } = await refused("?kind=thinking", GPT);
    expect(await violations(container)).toEqual([]);
  });
});
