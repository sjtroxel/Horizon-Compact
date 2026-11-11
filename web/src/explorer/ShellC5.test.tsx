import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { explorerLabels as L } from "./copy";
import { readMemoRows, realApi, realCasesIndex, realIndex, warmViews } from "./fixtures";
import { modelName } from "./models";
import { memoHref } from "./route";
import { Shell } from "./Shell";

const MODELS = realIndex.models.map((m) => m.model_key);
const OTHER = MODELS.find((key) => key !== "haiku-5-5")!;

// A view is a lazy chunk (C6): load the modules once up front, so a test's wait is for React, not for a transform.
beforeAll(warmViews);

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  window.scrollTo = vi.fn(); // jsdom has no scrolling
});
afterEach(cleanup);

/** Records whether anything had already prevented the click when it reached the document, then prevents it. */
function watchClicks() {
  const seen: boolean[] = [];
  const listener = (event: Event) => {
    seen.push(event.defaultPrevented);
    event.preventDefault();
  };
  document.addEventListener("click", listener);
  return { seen, stop: () => document.removeEventListener("click", listener) };
}

/** The element each route's view ends up with once its data has arrived. */
const LOADED: Record<string, string> = {
  "/memos/": "article.memo-card",
  "/cases/": ".case-readings",
  "/cases/closure-19/": ".case-model",
  "/studies/": ".awareness-model",
};

async function shellAt(path: string, requested: string[] = []) {
  window.history.replaceState(null, "", path);
  const view = render(<Shell data={realApi(requested)} />);
  await view.findByRole("heading", { level: 1 });
  const selector = LOADED[path.split("?")[0]!];
  if (selector !== undefined)
    await waitFor(() => expect(view.container.querySelector(selector)).not.toBeNull());
  return view;
}

function addLink(view: { container: HTMLElement }, href: string, text: string) {
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.textContent = text;
  view.container.querySelector(".explorer")!.appendChild(anchor);
  return anchor;
}

describe("the shell leaves files to the browser (carried from review 25a)", () => {
  it("does not intercept a link under /data/, or a link whose last path segment has a file extension", async () => {
    const view = await shellAt("/");
    const links = [
      addLink(view, "/data/memos/index.json", "data"),
      addLink(view, "/data/memos/grid/haiku-5-5/s1/A.jsonl", "a memo file"),
      addLink(view, "/data/memos/", "a folder under data, no extension"),
      addLink(view, "/files/report.json", "json"),
      addLink(view, "/x/y.jsonl", "jsonl"),
      addLink(view, "/docs/paper.pdf", "pdf"),
    ];
    const clicks = watchClicks();
    for (const link of links) fireEvent.click(link);
    clicks.stop();
    expect(clicks.seen).toEqual(Array(links.length).fill(false)); // none was prevented: all left to the browser
    expect(window.location.pathname).toBe("/");
  });

  it("still intercepts an ordinary path, one with a query, and one with a dot in an earlier segment", async () => {
    const view = await shellAt("/");
    for (const [href, expected] of [
      ["/cases/", "/cases/"],
      ["/memos/?kind=grid&scenario=s2&objective=B", "/memos/"],
      ["/a.b/cases/", "/a.b/cases/"],
      ["/scenario/s3/", "/scenario/s3/"],
    ] as const) {
      const link = addLink(view, href, href);
      const clicks = watchClicks();
      fireEvent.click(link);
      clicks.stop();
      expect(clicks.seen, href).toEqual([true]); // the shell took it
      expect(window.location.pathname, href).toBe(expected);
    }
  });
});

describe("the model switch keeps the query on every new view", () => {
  it.each([
    "/memos/?kind=grid&scenario=s2&objective=C",
    "/studies/?note=kept",
    "/cases/?note=kept",
    "/cases/closure-19/?note=kept",
  ])("%s", async (path) => {
    const view = await shellAt(path);
    const before = new URLSearchParams(window.location.search);
    const group = view.getByRole("group", { name: L.modelSwitch });
    fireEvent.click(within(group).getByRole("button", { name: modelName(OTHER) }));
    const switched = new URLSearchParams(window.location.search);
    expect(switched.get("model")).toBe(OTHER);
    for (const [key, value] of before) expect(switched.get(key), key).toBe(value);
    expect(window.location.pathname).toBe(path.split("?")[0]);

    fireEvent.click(within(group).getByRole("button", { name: modelName("haiku-5-5") }));
    const back = new URLSearchParams(window.location.search);
    expect(back.has("model")).toBe(false);
    for (const [key, value] of before) expect(back.get(key), key).toBe(value);
  });

  it("re-reads the reader for the other model, on the same scenario and goal", async () => {
    const view = await shellAt("/memos/?kind=grid&scenario=s3&objective=B");
    const rows = readMemoRows("grid/gpt-oss-openrouter/s3/B.jsonl");
    const group = view.getByRole("group", { name: L.modelSwitch });
    fireEvent.click(within(group).getByRole("button", { name: modelName(OTHER) }));
    await waitFor(() =>
      expect(view.container.querySelector<HTMLElement>("article.memo-card")!.dataset["run"]).toBe(
        rows[0]!.run_id,
      ),
    );
    expect(new URLSearchParams(window.location.search).get("scenario")).toBe("s3");
  });

  it("drops the run on a switch, and opens the same set's first run for the other model", async () => {
    const haikuRows = readMemoRows("grid/haiku-5-5/s2/D.jsonl");
    const otherRows = readMemoRows(`grid/${OTHER}/s2/D.jsonl`);
    const view = await shellAt(`/memos/?kind=grid&scenario=s2&objective=D&run=${haikuRows[3]!.run_id}`);
    await waitFor(() =>
      expect(view.container.querySelector<HTMLElement>("article.memo-card")!.dataset["run"]).toBe(
        haikuRows[3]!.run_id,
      ),
    );
    const group = view.getByRole("group", { name: L.modelSwitch });
    fireEvent.click(within(group).getByRole("button", { name: modelName(OTHER) }));
    const switched = new URLSearchParams(window.location.search);
    expect(switched.has("run")).toBe(false);
    expect([switched.get("kind"), switched.get("scenario"), switched.get("objective")]).toEqual([
      "grid",
      "s2",
      "D",
    ]);
    await waitFor(() =>
      expect(view.container.querySelector<HTMLElement>("article.memo-card")!.dataset["run"]).toBe(
        otherRows[0]!.run_id,
      ),
    );
    expect(view.container.querySelector("[data-refusal=run]")).toBeNull();
  });

  it("shows the thinking kind's refusal on gpt-oss-120b, and the card again on Haiku 5.5, keeping ?kind=thinking", async () => {
    const view = await shellAt("/memos/?kind=thinking");
    const group = view.getByRole("group", { name: L.modelSwitch });
    fireEvent.click(within(group).getByRole("button", { name: modelName(OTHER) }));
    await waitFor(() => expect(view.container.querySelector("[data-refusal=thinking_model]")).not.toBeNull());
    expect(new URLSearchParams(window.location.search).get("kind")).toBe("thinking");
    fireEvent.click(within(group).getByRole("button", { name: modelName("haiku-5-5") }));
    await waitFor(() => expect(view.container.querySelector("article.memo-card")).not.toBeNull());
  });
});

describe("moving through the memos by link", () => {
  it("turns a click on 'Next run' into pushState and shows that run, keeping the model", async () => {
    const rows = readMemoRows("grid/gpt-oss-openrouter/s1/A.jsonl");
    const view = await shellAt(`/memos/?model=${OTHER}`, []);
    const first = () => view.container.querySelector<HTMLElement>("article.memo-card")!.dataset["run"];
    expect(first()).toBe(rows[0]!.run_id);
    const clicks = watchClicks();
    const history = window.history.length;
    fireEvent.click(view.getByRole("link", { name: L.memoNext }));
    clicks.stop();
    expect(clicks.seen).toEqual([true]);
    expect(window.history.length).toBe(history + 1);
    expect(window.location.pathname + window.location.search).toBe(
      memoHref({ kind: "grid", scenario: "s1", objective: "A", run: rows[1]!.run_id }, OTHER),
    );
    await waitFor(() => expect(first()).toBe(rows[1]!.run_id));
    await waitFor(() => expect(document.activeElement).toBe(view.container.querySelector("h1")));
  });

  it("follows a choice of scenario and goal, each a link", async () => {
    const view = await shellAt("/memos/");
    const clicks = watchClicks();
    fireEvent.click(view.getByRole("link", { name: "s2" }));
    clicks.stop();
    await waitFor(() => expect(window.location.search).toBe("?kind=grid&scenario=s2&objective=A"));
    await waitFor(() =>
      expect(view.container.querySelector<HTMLElement>("article.memo-card")!.dataset["run"]).toBe(
        readMemoRows("grid/haiku-5-5/s2/A.jsonl")[0]!.run_id,
      ),
    );
  });

  it("leaves the cell's file link to the browser", async () => {
    const view = await shellAt("/memos/");
    const link = view.getByRole("link", { name: L.memoFileLink });
    const clicks = watchClicks();
    fireEvent.click(link);
    clicks.stop();
    expect(clicks.seen).toEqual([false]);
    expect(window.location.pathname).toBe("/memos/");
  });
});

describe("every new route in the shell", () => {
  it.each(Object.keys(LOADED))(
    "%s fetches only paths under /data/ and has no axe violations",
    async (path) => {
      const requested: string[] = [];
      const view = await shellAt(path, requested);
      expect(requested.length).toBeGreaterThan(1);
      for (const p of requested) expect(p.startsWith("/data/"), p).toBe(true);
      const results = await axe.run(view.container, { rules: { "color-contrast": { enabled: false } } });
      expect(
        results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`),
      ).toEqual([]);
    },
  );

  it("puts the exploratory label on the cases page and on every card, through the shell", async () => {
    const view = await shellAt("/cases/");
    // The lead lists each distinct label once, and every card carries its own.
    const distinct = new Set(realCasesIndex.cases.map((c) => c.exploratory_label)).size;
    expect(view.container.querySelectorAll(".exploratory-label")).toHaveLength(
      distinct + realCasesIndex.cases.length,
    );
  });
});
