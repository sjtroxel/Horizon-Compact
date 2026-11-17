// The methods page (Phase 6.5 step 4): the rendered frame, the two data parts, and that nothing else on the page can carry
// a number before step 5 gives its words a source.
import { cleanup, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { explorerHis, explorerLabels as L, METHODS_PLACEHOLDER } from "./copy";
import type { DataApi, MethodsFile } from "./data";
import { editedApi, readData, realApi, realGrids, realIndex, warmViews, WEB_ROOT } from "./fixtures";
import { formatCount, formatUtc, sessionSpan, statusCounts } from "./format";
import { mainFileUrl, mainFolderUrl } from "./links";
import { MethodsView, OUTLINE } from "./Methods";
import { modelName } from "./models";
import { Shell } from "./Shell";

beforeAll(warmViews);
beforeEach(() => {
  window.history.replaceState(null, "", "/methods/");
  window.scrollTo = vi.fn(); // jsdom has no scrolling
});
afterEach(cleanup);

const HAIKU = "haiku-5-5";
const GPT = "gpt-oss-openrouter";
const methodsFile = readData<MethodsFile>("methods.json");

async function methods(data: DataApi = realApi()) {
  const rendered = render(<MethodsView index={realIndex} data={data} />);
  await waitFor(() => expect(rendered.container.querySelector("[data-part=data]")).not.toBeNull());
  return rendered;
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

const section = (container: HTMLElement, id: string) =>
  container.querySelector<HTMLElement>(`section#${id}`)!;
const anchorOf = (id: string) => OUTLINE.find((s) => s.id === id)!.anchor;

describe("the methods page's frame", () => {
  it("has a title, a contents list of thirteen links and thirteen sections, each with its heading and its body placeholder", async () => {
    const { container } = await methods();
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(container.querySelector("h1")!.textContent).toBe(explorerHis.pages.methods.title);
    expect(container.querySelectorAll("h2")).toHaveLength(13);
    const sections = [...container.querySelectorAll<HTMLElement>("section.methods-section")];
    expect(sections.map((s) => s.id)).toEqual(OUTLINE.map((s) => s.anchor));
    sections.forEach((el, i) => {
      const id = OUTLINE[i]!.id;
      expect(within(el).getByRole("heading", { level: 2 }).textContent, id).toBe(
        explorerHis.methods.sectionTitles[id],
      );
      // The section can take focus (a contents link or a hash lands on it), and is not a landmark of its own.
      expect(el.hasAttribute("aria-labelledby"), id).toBe(false);
      expect(el.getAttribute("tabindex"), id).toBe("-1");
      const bodies = el.querySelectorAll("[data-placeholder=body]");
      expect(bodies, id).toHaveLength(1);
      expect(bodies[0]!.textContent, id).toBe(METHODS_PLACEHOLDER.body);
    });
  });

  it("marks every placeholder where it stands, with the class that draws a dashed outline", async () => {
    const { container } = await methods();
    const marked = (selector: string) => [...container.querySelectorAll(selector)];
    expect(marked("h1.methods-placeholder")).toHaveLength(1);
    expect(marked("h2.methods-placeholder")).toHaveLength(13);
    expect(marked(".jump-menu a.methods-placeholder")).toHaveLength(13);
    expect(marked("p.methods-placeholder")).toHaveLength(13);
    const css = readFileSync(resolve(WEB_ROOT, "src/explorer/explorer.css"), "utf8");
    expect(css).toMatch(/\.methods-placeholder\s*\{[^}]*dashed/);
  });

  it("links the contents to the sections' anchors, in order, and every link finds its section", async () => {
    const { container } = await methods();
    const nav = container.querySelector("nav.jump-menu")!;
    expect(nav.getAttribute("aria-label")).toBe(L.methodsContentsLabel);
    const links = [...nav.querySelectorAll("a")];
    expect(links.map((a) => a.getAttribute("href"))).toEqual(OUTLINE.map((s) => `#${s.anchor}`));
    for (const a of links) {
      const target = container.querySelector(a.getAttribute("href")!);
      expect(target?.tagName, a.getAttribute("href")!).toBe("SECTION");
    }
  });

  it("shows a loading line and then the sections, and an alert and no section when the data fails", async () => {
    const view = render(<MethodsView index={realIndex} data={realApi()} />);
    expect(view.getByRole("status").textContent).toBe(L.methodsLoading);
    expect(view.container.querySelectorAll("section")).toHaveLength(0);
    await waitFor(() => expect(view.container.querySelectorAll("section")).toHaveLength(13));
    cleanup();
    const failing: DataApi = { ...realApi(), loadMethods: () => Promise.reject(new Error("down")) };
    const failed = render(<MethodsView index={realIndex} data={failing} />);
    await failed.findByRole("alert");
    expect(failed.container.querySelectorAll("section")).toHaveLength(0);
  });

  it("refuses to show half a table: a methods file with no sweep for a model is an alert", async () => {
    const data = editedApi({
      "/data/methods.json": (body) => {
        body.sweeps = body.sweeps.filter((s: { model_key: string }) => s.model_key !== GPT);
      },
    });
    const view = render(<MethodsView index={realIndex} data={data} />);
    await view.findByRole("alert");
    expect(view.container.querySelectorAll("table")).toHaveLength(0);
  });

  it("reveals the section an address names once the data has loaded, and does nothing without one", async () => {
    const scrolled = vi.fn();
    Element.prototype.scrollIntoView = scrolled; // jsdom has none
    window.history.replaceState(null, "", `/methods/#${anchorOf("M6")}`);
    const { container } = await methods();
    await waitFor(() => expect(scrolled).toHaveBeenCalledTimes(1));
    expect(document.activeElement).toBe(section(container, anchorOf("M6")));
    cleanup();
    scrolled.mockClear();
    window.history.replaceState(null, "", "/methods/#not-a-section");
    await methods();
    cleanup();
    window.history.replaceState(null, "", "/methods/");
    await methods();
    expect(scrolled).not.toHaveBeenCalled();
  });

  it("has no axe violation (colour contrast is measured in the browser pass)", async () => {
    const { container } = await methods();
    expect(await violations(container)).toEqual([]);
  });
});

describe("M3's data: models, settings, dates and run counts", () => {
  const sweepOf = (model: string, kind: string) =>
    methodsFile.sweeps.find((s) => s.model_key === model && s.kind === kind)!;

  it("shows both models, the main one first, then the side study in its own labelled part, never added together", async () => {
    const { container } = await methods();
    const part = section(container, anchorOf("M3")).querySelector<HTMLElement>("[data-part=data]")!;
    expect([...part.querySelectorAll("h3")].map((h) => h.textContent)).toEqual([
      modelName(HAIKU),
      modelName(GPT),
      L.methodsSideStudy,
    ]);
    // Three runs-by-scenario tables, one per sweep, and no row that is a total.
    const counts = [...part.querySelectorAll("table")].filter((t) =>
      t.querySelector("caption")!.textContent!.endsWith("runs by scenario"),
    );
    expect(counts.map((t) => t.querySelectorAll("tbody tr").length)).toEqual([4, 4, 1]);
    expect(counts.map((t) => t.querySelector("caption")!.textContent)).toEqual([
      L.methodsCountsCaption(modelName(HAIKU)),
      L.methodsCountsCaption(modelName(GPT)),
      L.methodsCountsCaption(modelName(HAIKU)),
    ]);
  });

  it("copies every setting of each sweep, as the record has it, under the label for its field", async () => {
    const { container } = await methods();
    const part = section(container, anchorOf("M3"));
    const tables = [...part.querySelectorAll("table")].filter((t) =>
      t.querySelector("caption")!.textContent!.includes("settings"),
    );
    expect(tables).toHaveLength(3);
    const order = [sweepOf(HAIKU, "grid"), sweepOf(GPT, "grid"), sweepOf(HAIKU, "thinking")];
    tables.forEach((table, i) => {
      const rows = [...table.querySelectorAll("tbody tr")].map((tr) => [
        tr.querySelector("th")!.textContent,
        tr.querySelector("td")!.textContent,
      ]);
      const expected = Object.entries(order[i]!.settings).map(([field, value]) => [
        L.methodsSettingLabels[field],
        value === null
          ? L.methodsNone
          : typeof value === "boolean"
            ? value
              ? L.methodsYes
              : L.methodsNo
            : String(value),
      ]);
      expect(rows).toEqual(expected);
    });
    // The side study differs from the grid in effort, and the page shows it as the record has it.
    const effort = (i: number) => tables[i]!.querySelector("tbody tr:nth-child(8) td")!.textContent;
    expect(effort(0)).toBe(String(sweepOf(HAIKU, "grid").settings["effort"]));
    expect(effort(2)).toBe(String(sweepOf(HAIKU, "thinking").settings["effort"]));
    expect(effort(0)).not.toBe(effort(2));
  });

  it("shows who served the attempts with the number of attempts each, including the attempts that reported none", async () => {
    const { container } = await methods();
    const part = section(container, anchorOf("M3"));
    const served = [...part.querySelectorAll("table")].filter((t) =>
      /provider that served|model the provider reported/.test(t.querySelector("caption")!.textContent!),
    );
    // Haiku (and its side study) report a model only; gpt-oss reports a provider and a model.
    expect(served.map((t) => t.querySelector("caption")!.textContent)).toEqual([
      L.methodsServedCaption(modelName(HAIKU), L.methodsServedLabels["served_model"]!),
      L.methodsServedCaption(modelName(GPT), L.methodsServedLabels["served_by"]!),
      L.methodsServedCaption(modelName(GPT), L.methodsServedLabels["served_model"]!),
      L.methodsServedCaption(modelName(HAIKU), L.methodsServedLabels["served_model"]!),
    ]);
    const rows = (table: HTMLElement) =>
      [...table.querySelectorAll("tbody tr")].map((tr) => [
        tr.querySelector("th")!.textContent,
        tr.querySelector("td")!.textContent,
      ]);
    const gpt = sweepOf(GPT, "grid");
    expect(rows(served[1]!)).toEqual(gpt.served["served_by"]!.map((v) => [v.value, formatCount(v.attempts)]));
    expect(rows(served[1]!).map(([, n]) => n)).toEqual(["1,322", "11"]);
    expect(rows(served[2]!)).toEqual(
      gpt.served["served_model"]!.map((v) => [v.value, formatCount(v.attempts)]),
    );
  });

  it("gives each sweep's first start and last finish in UTC, picked from its sessions, and how many sessions", async () => {
    const { container } = await methods();
    const part = section(container, anchorOf("M3"));
    const dates = [...part.querySelectorAll("table")].filter((t) =>
      t.querySelector("caption")!.textContent!.endsWith("dates and sessions"),
    );
    expect(dates).toHaveLength(3);
    const order = [sweepOf(HAIKU, "grid"), sweepOf(GPT, "grid"), sweepOf(HAIKU, "thinking")];
    dates.forEach((table, i) => {
      const span = sessionSpan(order[i]!.sessions)!;
      expect(
        [...table.querySelectorAll("tbody tr")].map((tr) => tr.querySelector("td")!.textContent),
      ).toEqual([formatUtc(span.first), formatUtc(span.last), String(order[i]!.sessions.length)]);
    });
    expect(dates[1]!.querySelectorAll("tbody tr td")[2]!.textContent).toBe("2"); // gpt-oss ran in two sessions
  });

  it("counts each scenario's runs from the results files' cells: attempted, valid, refused, and failures by type", async () => {
    const { container } = await methods();
    const part = section(container, anchorOf("M3"));
    const counts = [...part.querySelectorAll("table")].filter((t) =>
      t.querySelector("caption")!.textContent!.endsWith("runs by scenario"),
    );
    const order = [
      ["grid", HAIKU],
      ["grid", GPT],
      ["thinking", HAIKU],
    ] as const;
    counts.forEach((table, i) => {
      const [kind, model] = order[i]!;
      const files = realGrids.filter((g) => g.label.startsWith(`${kind} ${model} `)).map((g) => g.file);
      expect(files.length).toBeGreaterThan(0);
      const rows = [...table.querySelectorAll<HTMLElement>("tbody tr")];
      expect(rows.map((r) => r.dataset["scenario"])).toEqual(files.map((f) => f.scenario_id));
      rows.forEach((row, j) => {
        const c = statusCounts(files[j]!.cells);
        const cells = [...row.querySelectorAll("td")].map((td) => td.textContent);
        expect(cells.slice(0, 3)).toEqual([c.attempted, c.valid, c.refused].map(formatCount));
        expect(cells[3]).toBe(
          c.failed.length === 0
            ? L.methodsNoFailures
            : c.failed.map(([t, n]) => `${t} ${formatCount(n)}`).join(", "),
        );
      });
    });
    // One measured case: gpt-oss s2 failed 27 of 300 runs, 26 of them by schema (the ledger's line 17, 9.0%).
    const s2 = counts[1]!.querySelector("tr[data-scenario=s2]")!;
    expect([...s2.querySelectorAll("td")].map((td) => td.textContent)).toEqual([
      "300",
      "273",
      "0",
      "schema_invalid 26, sum_mismatch 1",
    ]);
  });
});

describe("M7's data: the raw text", () => {
  it("gives the object count and the total bytes from the data, and links the folder and the manifest on GitHub", async () => {
    const { container } = await methods();
    const part = section(container, anchorOf("M7")).querySelector<HTMLElement>("[data-part=data]")!;
    const rows = [...part.querySelectorAll("tbody tr")].map((tr) => tr.querySelector("td")!.textContent);
    expect(rows).toEqual([
      formatCount(methodsFile.raw_text.object_count),
      formatCount(methodsFile.raw_text.total_bytes),
    ]);
    const links = [...part.querySelectorAll("a")];
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      "https://github.com/sjtroxel/horizon-compact/tree/main/experiment/raw",
      "https://github.com/sjtroxel/horizon-compact/blob/main/docs/phases/evidence/phase-4/raw-manifest.json",
    ]);
    expect(links.map((a) => a.getAttribute("href"))).toEqual([
      mainFolderUrl(methodsFile.raw_text.folder),
      mainFileUrl(methodsFile.raw_text.manifest),
    ]);
    for (const a of links) {
      expect(a.getAttribute("target")).toBe("_blank");
      expect(a.getAttribute("rel")).toBe("noopener noreferrer");
    }
  });
});

describe("where a number can be", () => {
  it("holds data parts in M3 and M7 and nowhere else, and no digit on the page outside them", async () => {
    const { container } = await methods();
    const parts = [...container.querySelectorAll("[data-part=data]")];
    expect(parts.map((p) => p.closest("section")!.id)).toEqual([anchorOf("M3"), anchorOf("M7")]);
    const clone = container.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("[data-part=data]").forEach((p) => p.remove());
    expect(clone.textContent).not.toMatch(/\d/);
    // The page's own labels hold no digit either, except where a data part uses them (checked above by being inside it).
    expect(container.textContent).toMatch(/\d/); // the negative control: the data parts do hold digits
  });
});

describe("in the shell", () => {
  it("has a Methods link in the navigation, marks it current at /methods/, and has no model switch", async () => {
    const view = render(<Shell data={realApi()} />);
    await view.findByRole("heading", { level: 1 });
    const nav = view.getByRole("navigation", { name: L.navLabel });
    const link = within(nav).getByRole("link", { name: L.navMethods });
    expect(link.getAttribute("href")).toBe("/methods/");
    expect(link.getAttribute("aria-current")).toBe("page");
    expect(view.container.querySelector(".switch-bar")).toBeNull();
    expect(document.title).toBe(explorerHis.pages.methods.title);
    await waitFor(() => expect(view.container.querySelectorAll("section.methods-section")).toHaveLength(13));
  });

  it("asks only for files under /data/: the methods file, the grids and the thinking file, and no memo and no raw record", async () => {
    const requested: string[] = [];
    const view = render(<Shell data={realApi(requested)} />);
    await waitFor(() => expect(view.container.querySelectorAll("section.methods-section")).toHaveLength(13));
    for (const path of requested) expect(path.startsWith("/data/"), path).toBe(true);
    expect(requested).toContain("/data/methods.json");
    expect(requested.filter((p) => p.includes("/memos/") || p.includes("awareness"))).toEqual([]);
  });
});
