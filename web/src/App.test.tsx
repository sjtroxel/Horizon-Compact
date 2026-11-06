import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { his, isPlaceholder } from "./copy";
import { data, money } from "./data";

afterEach(cleanup);

const LINES = data.scenario.lines.length;
const RUNS_PER_PRIORITY = 3;

function dotsOf(container: HTMLElement, priority?: string): HTMLButtonElement[] {
  const scope = priority ? `.panel[data-priority="${priority}"] ` : "";
  return Array.from(container.querySelectorAll<HTMLButtonElement>(`${scope}.dot`));
}

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here; the tokens are checked by the palette
  // validator and the measured ratios are recorded in the IMPLEMENTATION doc (section 20).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

describe("the rendered page", () => {
  it("has no axe violations", async () => {
    const { container } = render(<App />);
    expect(await violations(container)).toEqual([]);
  });

  it("has no axe violations with a priority chosen and a run traced", async () => {
    const { container, getByRole } = render(<App />);
    fireEvent.click(getByRole("button", { name: "Fragrance" }));
    const dot = dotsOf(container, "fragrance")[4]!;
    fireEvent.pointerOver(dot);
    expect(container.querySelectorAll(".dot.on")).toHaveLength(LINES);
    expect(await violations(container)).toEqual([]);
  });

  it("draws one panel per priority and one dot per run and line", () => {
    const { container } = render(<App />);
    expect(container.querySelectorAll(".panel")).toHaveLength(data.cells.length);
    expect(dotsOf(container)).toHaveLength(data.runs.length * LINES);
  });

  it("has one name heading, and it is the project's name", () => {
    const { container } = render(<App />);
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(container.querySelector("h1")?.textContent).toBe("Horizon Compact");
  });

  it("shows his words in the placeholder class only while they are placeholders", () => {
    const { container } = render(<App />);
    const shown = [his.lede, his.notice, his.resultsTitle, his.resultsSentence];
    const expected = shown.filter(isPlaceholder).length;
    expect(container.querySelectorAll(".placeholder")).toHaveLength(expected);
    for (const text of shown) {
      const el = Array.from(container.querySelectorAll("p, h2")).find((e) => e.textContent === text);
      expect(el, text).toBeDefined();
      expect(el!.classList.contains("placeholder")).toBe(isPlaceholder(text));
    }
  });
});

describe("tracing a run", () => {
  it("marks 7 dots and 1 table row when a dot is pointed at, and clears on leaving the panel", () => {
    const { container } = render(<App />);
    const dot = dotsOf(container, "color")[5]!;
    fireEvent.pointerOver(dot);
    expect(container.querySelectorAll(".dot.on")).toHaveLength(LINES);
    expect(container.querySelectorAll(".runs tbody tr.on")).toHaveLength(1);
    expect(container.querySelectorAll(".panel.tracing")).toHaveLength(1);
    expect(container.querySelector(".tip.show")).not.toBeNull();
    fireEvent.pointerLeave(container.querySelector('.panel[data-priority="color"]')!);
    expect(container.querySelectorAll(".dot.on")).toHaveLength(0);
    expect(container.querySelectorAll(".runs tbody tr.on")).toHaveLength(0);
    expect(container.querySelector(".tip.show")).toBeNull();
  });

  it("marks the same 7 dots and 1 row on focus, and Escape clears", () => {
    const { container } = render(<App />);
    const dot = dotsOf(container, "water")[2]!;
    act(() => dot.focus());
    expect(container.querySelectorAll(".dot.on")).toHaveLength(LINES);
    expect(container.querySelectorAll(".runs tbody tr.on")).toHaveLength(1);
    fireEvent.keyDown(dot, { key: "Escape" });
    expect(container.querySelectorAll(".dot.on")).toHaveLength(0);
    expect(container.querySelectorAll(".runs tbody tr.on")).toHaveLength(0);
  });

  it("puts the amount first in the tooltip, then the line, then the run id and status", () => {
    const { container } = render(<App />);
    const mine = data.runs
      .filter((r) => r.objective_id === "butterflies")
      .sort((a, b) => a.repeat - b.repeat);
    const run = mine[1]!;
    const line = data.scenario.lines[3]!;
    const dot = dotsOf(container, "butterflies")[3 * RUNS_PER_PRIORITY + 1]!;
    fireEvent.pointerOver(dot);
    const tip = container.querySelector(".tip")!;
    expect(tip.querySelector("b")?.textContent).toBe(money(run.amounts[line.key]!));
    expect(tip.textContent).toContain(line.label);
    expect(tip.textContent).toContain(`${run.run_id}, ${run.status}`);
  });
});

describe("the priority control", () => {
  it("marks one panel chosen and 3 table rows in, with aria-pressed to match", () => {
    const { container, getByRole } = render(<App />);
    expect(getByRole("button", { name: "All five" }).getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(getByRole("button", { name: "Butterflies" }));
    expect(container.querySelectorAll(".panel.chosen")).toHaveLength(1);
    expect(container.querySelector(".panel.chosen")?.getAttribute("data-priority")).toBe("butterflies");
    expect(container.querySelectorAll(".runs tbody tr.in")).toHaveLength(RUNS_PER_PRIORITY);
    expect(container.querySelector(".panels.focus")).not.toBeNull();
    expect(getByRole("button", { name: "Butterflies" }).getAttribute("aria-pressed")).toBe("true");
    expect(getByRole("button", { name: "All five" }).getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(getByRole("button", { name: "All five" }));
    expect(container.querySelectorAll(".panel.chosen")).toHaveLength(0);
    expect(container.querySelectorAll(".runs tbody tr.in")).toHaveLength(0);
    expect(container.querySelector(".panels.focus")).toBeNull();
  });
});

/** jsdom has no layout: place a panel by hand, and stand in for scrollIntoView and matchMedia. */
function placePanel(container: HTMLElement, priority: string, top: number, bottom: number) {
  const panel = container.querySelector<HTMLElement>(`.panel[data-priority="${priority}"]`)!;
  panel.getBoundingClientRect = () => ({ top, bottom }) as DOMRect;
  return panel;
}

describe("choosing a priority brings its panel into view", () => {
  const original = {
    scrollIntoView: Element.prototype.scrollIntoView,
    matchMedia: window.matchMedia,
  };
  afterEach(() => {
    Element.prototype.scrollIntoView = original.scrollIntoView;
    window.matchMedia = original.matchMedia;
  });

  function mock(reduced: boolean, twoColumns = false) {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    window.matchMedia = ((query: string) => ({
      matches:
        (reduced && query === "(prefers-reduced-motion: reduce)") ||
        (twoColumns && query === "(min-width: 54rem)"),
    })) as typeof window.matchMedia;
    return scrollIntoView;
  }

  it("never moves the page in the two-column layout", () => {
    const scrollIntoView = mock(false, true);
    const { container, getByRole } = render(<App />);
    placePanel(container, "fragrance", window.innerHeight + 200, window.innerHeight + 700);
    fireEvent.click(getByRole("button", { name: "Fragrance" }));
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("scrolls a panel that is out of view to the top, smoothly", () => {
    const scrollIntoView = mock(false);
    const { container, getByRole } = render(<App />);
    const panel = placePanel(container, "fragrance", window.innerHeight + 200, window.innerHeight + 700);
    fireEvent.click(getByRole("button", { name: "Fragrance" }));
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "start", behavior: "smooth" });
    expect(scrollIntoView.mock.contexts[0]).toBe(panel);
  });

  it("scrolls a panel that is only partly in view", () => {
    const scrollIntoView = mock(false);
    const { container, getByRole } = render(<App />);
    placePanel(container, "water", window.innerHeight - 100, window.innerHeight + 300);
    fireEvent.click(getByRole("button", { name: "Low water use" }));
    expect(scrollIntoView).toHaveBeenCalledTimes(1);
  });

  it("does not move the page for a panel that is fully in view", () => {
    const scrollIntoView = mock(false);
    const { container, getByRole } = render(<App />);
    placePanel(container, "color", 80, 520);
    fireEvent.click(getByRole("button", { name: "Color" }));
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("never scrolls for All five", () => {
    const scrollIntoView = mock(false);
    const { container, getByRole } = render(<App />);
    fireEvent.click(getByRole("button", { name: "Butterflies" }));
    scrollIntoView.mockClear();
    for (const cell of data.cells) placePanel(container, cell.objective_id, 5000, 5400);
    fireEvent.click(getByRole("button", { name: "All five" }));
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("does not animate under prefers-reduced-motion", () => {
    const scrollIntoView = mock(true);
    const { container, getByRole } = render(<App />);
    placePanel(container, "fragrance", window.innerHeight + 200, window.innerHeight + 700);
    fireEvent.click(getByRole("button", { name: "Fragrance" }));
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "start", behavior: "auto" });
  });
});

describe("the layout hooks the stylesheet depends on", () => {
  it("gives every priority button its own label as data-label, for the reserved semibold width", () => {
    const { container } = render(<App />);
    const buttons = Array.from(container.querySelectorAll<HTMLButtonElement>(".control button"));
    expect(buttons).toHaveLength(data.cells.length + 1);
    for (const button of buttons) expect(button.getAttribute("data-label")).toBe(button.textContent);
  });

  it("marks the run table's frame wide and its seven line headings as amounts", () => {
    const { container } = render(<App />);
    const frames = container.querySelectorAll(".frame");
    expect(frames).toHaveLength(2);
    expect(frames[0]!.classList.contains("wide")).toBe(false);
    expect(frames[1]!.classList.contains("wide")).toBe(true);
    expect(container.querySelectorAll("table.runs th.amt")).toHaveLength(LINES);
    expect(container.querySelectorAll("table.status th.amt")).toHaveLength(0);
  });
});

describe("the keyboard", () => {
  it("gives each panel one tab stop", () => {
    const { container } = render(<App />);
    for (const cell of data.cells) {
      const stops = dotsOf(container, cell.objective_id).filter((d) => d.tabIndex === 0);
      expect(stops).toHaveLength(1);
    }
  });

  it("moves between runs with Left and Right and between lines with Up and Down, inside the panel", () => {
    const { container } = render(<App />);
    const dots = dotsOf(container, "fragrance");
    act(() => dots[0]!.focus());
    fireEvent.keyDown(document.activeElement!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(dots[1]);
    fireEvent.keyDown(document.activeElement!, { key: "ArrowDown" });
    expect(document.activeElement).toBe(dots[1 + RUNS_PER_PRIORITY]);
    fireEvent.keyDown(document.activeElement!, { key: "ArrowUp" });
    expect(document.activeElement).toBe(dots[1]);
    fireEvent.keyDown(document.activeElement!, { key: "ArrowLeft" });
    fireEvent.keyDown(document.activeElement!, { key: "ArrowLeft" });
    expect(document.activeElement).toBe(dots[0]);
    fireEvent.keyDown(document.activeElement!, { key: "ArrowUp" });
    expect(document.activeElement).toBe(dots[0]);
    act(() => dots[dots.length - 1]!.focus());
    fireEvent.keyDown(document.activeElement!, { key: "ArrowDown" });
    fireEvent.keyDown(document.activeElement!, { key: "ArrowRight" });
    expect(document.activeElement).toBe(dots[dots.length - 1]);
    expect(dots.filter((d) => d.tabIndex === 0)).toHaveLength(1);
    expect(dots[dots.length - 1]!.tabIndex).toBe(0);
  });

  it("follows focus with the tracing and the tooltip", () => {
    const { container } = render(<App />);
    const dots = dotsOf(container, "color");
    act(() => dots[0]!.focus());
    fireEvent.keyDown(document.activeElement!, { key: "ArrowDown" });
    const runId = /run (r-[0-9a-f]+)/.exec(dots[3]!.getAttribute("aria-label")!)![1]!;
    expect(container.querySelectorAll(".runs tbody tr.on")).toHaveLength(1);
    expect(container.querySelector(".runs tbody tr.on")?.getAttribute("data-run")).toBe(runId);
    expect(container.querySelector(".tip.show")?.textContent).toContain(runId);
  });
});

describe("every value is reachable as text", () => {
  it("shows each run's amount for each line in the run table", () => {
    const { container } = render(<App />);
    const table = container.querySelector<HTMLTableElement>("table.runs")!;
    for (const run of data.runs) {
      const row = within(table).getByText(run.run_id).closest("tr")!;
      const cells = Array.from(row.querySelectorAll("td")).map((td) => td.textContent);
      data.scenario.lines.forEach((line, i) => {
        expect(cells[4 + i]).toBe(money(run.amounts[line.key]!));
      });
    }
  });

  it("names every run in each dot's accessible label", () => {
    const { container } = render(<App />);
    for (const dot of dotsOf(container)) {
      expect(dot.getAttribute("aria-label")).toMatch(/^\$[\d,]+, .+, run r-[0-9a-f]+, \w+$/);
    }
  });
});
