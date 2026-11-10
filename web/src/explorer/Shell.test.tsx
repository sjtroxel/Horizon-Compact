import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { explorerHis, explorerLabels } from "./copy";
import { realApi, realIndex } from "./fixtures";
import { pageMeta } from "./page-meta.mjs";
import { Shell } from "./Shell";

const MODELS = realIndex.models.map((m) => m.model_key);
const OTHER = MODELS.find((key) => key !== "haiku-5-5")!;

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  window.scrollTo = vi.fn(); // jsdom has no scrolling
});
afterEach(cleanup);

/** Records whether anything had already prevented the click when it reached the document, then prevents it, so
 * jsdom never attempts a real navigation. */
function watchClicks() {
  const seen: boolean[] = [];
  const listener = (event: Event) => {
    seen.push(event.defaultPrevented);
    event.preventDefault();
  };
  document.addEventListener("click", listener);
  return { seen, stop: () => document.removeEventListener("click", listener) };
}

async function shellAt(path: string) {
  window.history.replaceState(null, "", path);
  const view = render(<Shell data={realApi()} />);
  await view.findByRole("heading", { level: 1 });
  return view;
}

const h1Text = (container: HTMLElement) => container.querySelector("h1")?.textContent;

async function violations(container: HTMLElement) {
  // jsdom has no layout, so the color-contrast rule cannot run here (the tokens were validated in the Phase 6 doc,
  // sections 24.1 and 24.2).
  const results = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join("; ")}`);
}

describe("the shell", () => {
  it("shows a loading line until the data arrives, then the story at /", async () => {
    const view = render(<Shell data={realApi()} />);
    expect(view.getByRole("status").textContent).toBe(explorerLabels.loading);
    await view.findByRole("heading", { level: 1 });
    expect(h1Text(view.container)).toBe(pageMeta({ kind: "story" }, explorerHis.pages).title);
  });

  it("links to the story, every scenario, the cases, the studies and the memos, and marks the current page", async () => {
    const view = await shellAt("/scenario/s2/");
    const nav = view.getByRole("navigation", { name: explorerLabels.navLabel });
    const hrefs = within(nav)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual([
      "/",
      "/scenario/s1/",
      "/scenario/s2/",
      "/scenario/s3/",
      "/scenario/s4/",
      "/cases/",
      "/studies/",
      "/memos/",
    ]);
    const current = within(nav)
      .getAllByRole("link")
      .filter((a) => a.getAttribute("aria-current") === "page");
    expect(current.map((a) => a.getAttribute("href"))).toEqual(["/scenario/s2/"]);
  });

  it("shows the scenario's id and its primary outcome from the data", async () => {
    const view = await shellAt("/scenario/s3/");
    const outcome = realIndex.scenarios.find((s) => s.scenario_id === "s3")!.primary_outcome;
    expect(view.container.querySelector("main")?.textContent).toContain("s3");
    expect(view.container.querySelector("main")?.textContent).toContain(outcome);
    expect(view.container.querySelector("figure figcaption")).not.toBeNull();
  });

  it("shows the case's label and 'exploratory' on a case, and a plain not-found view elsewhere", async () => {
    const view = await shellAt("/cases/pre-25/");
    expect(view.container.querySelector("main")?.textContent).toContain("pre-25");
    expect(view.container.querySelector("main")?.textContent).toContain(explorerLabels.exploratory);
    cleanup();
    const missing = await shellAt("/scenario/s9/");
    expect(h1Text(missing.container)).toBe(explorerLabels.notFoundTitle);
    expect(missing.queryByRole("group")).toBeNull(); // no model switch on a page that does not exist
    expect(document.title).toBe(explorerLabels.notFoundTitle);
  });
});

describe("the links", () => {
  it("a plain click pushes state, re-renders, retitles the document and focuses the new heading", async () => {
    const view = await shellAt("/");
    const clicks = watchClicks();
    const before = window.history.length;
    fireEvent.click(view.getByRole("link", { name: explorerLabels.navScenario("s2") }));
    clicks.stop();

    expect(clicks.seen).toEqual([true]); // the shell had already prevented the browser's navigation
    expect(window.location.pathname).toBe("/scenario/s2/");
    expect(window.history.length).toBe(before + 1);
    const expected = pageMeta({ kind: "scenario", id: "s2" }, explorerHis.pages).title;
    expect(h1Text(view.container)).toBe(expected);
    expect(document.title).toBe(expected);
    expect(document.activeElement).toBe(view.container.querySelector("h1"));
    expect(window.scrollTo).toHaveBeenCalled();
  });

  it("leaves a modifier click, a middle click and a link with a target to the browser", async () => {
    const view = await shellAt("/");
    const link = view.getByRole("link", { name: explorerLabels.navCases });
    const targeted = document.createElement("a");
    targeted.href = "/memos/";
    targeted.target = "_blank";
    targeted.textContent = "targeted";
    view.container.querySelector(".explorer")!.appendChild(targeted);
    const outside = document.createElement("a");
    outside.href = "https://example.com/";
    outside.textContent = "outside";
    view.container.querySelector(".explorer")!.appendChild(outside);

    const clicks = watchClicks();
    fireEvent.click(link, { ctrlKey: true });
    fireEvent.click(link, { metaKey: true });
    fireEvent.click(link, { shiftKey: true });
    fireEvent.click(link, { altKey: true });
    fireEvent.click(link, { button: 1 });
    fireEvent.click(targeted);
    fireEvent.click(outside);
    clicks.stop();

    expect(clicks.seen).toEqual(Array(7).fill(false)); // none was prevented: all left to the browser
    expect(window.location.pathname).toBe("/");
    expect(h1Text(view.container)).toBe(pageMeta({ kind: "story" }, explorerHis.pages).title);
  });

  it("re-renders on popstate", async () => {
    const view = await shellAt("/");
    const clicks = watchClicks();
    fireEvent.click(view.getByRole("link", { name: explorerLabels.navStudies }));
    clicks.stop();
    expect(window.location.pathname).toBe("/studies/");

    await act(async () => {
      window.history.back();
    });
    await waitFor(() => expect(window.location.pathname).toBe("/"));
    await waitFor(() =>
      expect(h1Text(view.container)).toBe(pageMeta({ kind: "story" }, explorerHis.pages).title),
    );
    expect(document.title).toBe(pageMeta({ kind: "story" }, explorerHis.pages).title);
  });
});

describe("the model switch in the shell", () => {
  it("writes ?model= without reloading, keeps the path, and carries the model on the links", async () => {
    const view = await shellAt("/scenario/s1/");
    const group = view.getByRole("group", { name: explorerLabels.modelSwitch });
    const history = window.history.length;
    fireEvent.click(within(group).getByRole("button", { name: OTHER }));

    expect(window.location.pathname).toBe("/scenario/s1/");
    expect(window.location.search).toBe(`?model=${OTHER}`);
    expect(window.history.length).toBe(history); // replaced, not pushed
    expect(within(group).getByRole("button", { name: OTHER }).getAttribute("aria-pressed")).toBe("true");
    expect(within(group).getByRole("button", { name: "haiku-5-5" }).getAttribute("aria-pressed")).toBe(
      "false",
    );
    const nav = view.getByRole("navigation", { name: explorerLabels.navLabel });
    for (const a of within(nav).getAllByRole("link")) {
      expect(a.getAttribute("href")).toMatch(new RegExp(`\\?model=${OTHER}$`));
    }

    fireEvent.click(within(group).getByRole("button", { name: "haiku-5-5" }));
    expect(window.location.search).toBe("");
  });

  it("starts on Haiku 5.5 for no model or an unknown one, and on the named model otherwise", async () => {
    for (const [search, pressed] of [
      ["", "haiku-5-5"],
      ["?model=nonsense", "haiku-5-5"],
      [`?model=${OTHER}`, OTHER],
    ] as const) {
      const view = await shellAt(`/scenario/s1/${search}`);
      const group = view.getByRole("group", { name: explorerLabels.modelSwitch });
      const on = within(group)
        .getAllByRole("button")
        .filter((b) => b.getAttribute("aria-pressed") === "true");
      expect(
        on.map((b) => b.textContent),
        search,
      ).toEqual([pressed]);
      cleanup();
    }
  });

  it("keeps the chosen model through a click on a link", async () => {
    const view = await shellAt(`/?model=${OTHER}`);
    const clicks = watchClicks();
    fireEvent.click(view.getByRole("link", { name: explorerLabels.navCases }));
    clicks.stop();
    expect(window.location.pathname + window.location.search).toBe(`/cases/?model=${OTHER}`);
  });
});

describe("accessibility", () => {
  it("has no axe violations on the shell", async () => {
    for (const path of [
      "/",
      "/scenario/s1/",
      "/cases/",
      "/cases/pre-25/",
      "/studies/",
      "/memos/",
      "/nowhere/",
    ]) {
      const view = await shellAt(path);
      expect(await violations(view.container), path).toEqual([]);
      cleanup();
    }
  });

  it("has one h1 per view", async () => {
    const view = await shellAt("/scenario/s1/");
    expect(view.container.querySelectorAll("h1")).toHaveLength(1);
  });
});
