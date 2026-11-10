import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { explorerHis, explorerLabels } from "./copy";
import { realApi, realIndex } from "./fixtures";
import { modelName } from "./models";
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

  it("shows a scenario's id in its title, then the chart card and its caption once the data has loaded", async () => {
    const view = await shellAt("/scenario/s3/");
    expect(h1Text(view.container)).toContain("(s3)");
    const caption = await waitFor(() => {
      const found = view.container.querySelector("figure figcaption");
      expect(found).not.toBeNull();
      return found!;
    });
    expect(caption.textContent).toContain(modelName("haiku-5-5"));
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
    fireEvent.click(within(group).getByRole("button", { name: modelName(OTHER) }));

    expect(window.location.pathname).toBe("/scenario/s1/");
    expect(window.location.search).toBe(`?model=${OTHER}`);
    expect(window.history.length).toBe(history); // replaced, not pushed
    expect(
      within(group)
        .getByRole("button", { name: modelName(OTHER) })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      within(group)
        .getByRole("button", { name: modelName("haiku-5-5") })
        .getAttribute("aria-pressed"),
    ).toBe("false");
    const nav = view.getByRole("navigation", { name: explorerLabels.navLabel });
    for (const a of within(nav).getAllByRole("link")) {
      expect(a.getAttribute("href")).toMatch(new RegExp(`\\?model=${OTHER}$`));
    }

    fireEvent.click(within(group).getByRole("button", { name: modelName("haiku-5-5") }));
    expect(window.location.search).toBe("");
  });

  it("starts on Haiku 5.5 for no model or an unknown one, and on the named model otherwise", async () => {
    for (const [search, pressed] of [
      ["", modelName("haiku-5-5")],
      ["?model=nonsense", modelName("haiku-5-5")],
      [`?model=${OTHER}`, modelName(OTHER)],
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

describe("a hash in the address", () => {
  const scrolledTo: Element[] = [];
  const original = Element.prototype.scrollIntoView;
  beforeEach(() => {
    scrolledTo.length = 0;
    // jsdom has no scrolling; record what the shell asks to scroll into view.
    Element.prototype.scrollIntoView = function (this: Element) {
      scrolledTo.push(this);
    };
  });
  afterEach(() => {
    Element.prototype.scrollIntoView = original;
  });

  it("scrolls to and focuses the section after a click on a link to it, not the heading", async () => {
    const view = await shellAt("/scenario/s1/");
    const link = await view.findByRole("link", { name: explorerLabels.againstLink });
    const clicks = watchClicks();
    fireEvent.click(link);
    clicks.stop();

    expect(clicks.seen).toEqual([true]); // the shell took the click: a different page, so not the browser's jump
    expect(window.location.pathname + window.location.hash).toBe("/#against-the-thesis");
    const section = view.container.querySelector("#against-the-thesis")!;
    expect(section).not.toBeNull();
    expect(document.activeElement).toBe(section);
    expect(scrolledTo).toEqual([section]);
    expect(document.activeElement).not.toBe(view.container.querySelector("h1"));
  });

  it("keeps the model on that link, and the hash after it", async () => {
    const view = await shellAt(`/scenario/s1/?model=${OTHER}`);
    const link = await view.findByRole("link", { name: explorerLabels.againstLink });
    const clicks = watchClicks();
    fireEvent.click(link);
    clicks.stop();
    expect(window.location.pathname + window.location.search + window.location.hash).toBe(
      `/?model=${OTHER}#against-the-thesis`,
    );
  });

  it("scrolls to and focuses the section on a first load with the hash, once the data has rendered", async () => {
    const view = await shellAt("/#against-the-thesis");
    await waitFor(() => expect(document.activeElement?.id).toBe("against-the-thesis"));
    expect(scrolledTo).toHaveLength(1);
    expect(scrolledTo[0]).toBe(view.container.querySelector("#against-the-thesis"));
  });

  it("falls back to the heading when the hash names nothing, on a first load and after a click", async () => {
    const first = await shellAt("/#no-such-element");
    await waitFor(() => expect(document.activeElement).toBe(first.container.querySelector("h1")));
    expect(scrolledTo).toEqual([]);
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
    cleanup();

    const view = await shellAt("/");
    const link = view.getByRole("link", { name: explorerLabels.navStudies });
    link.setAttribute("href", "/studies/#no-such-element");
    const clicks = watchClicks();
    fireEvent.click(link);
    clicks.stop();
    expect(window.location.pathname + window.location.hash).toBe("/studies/#no-such-element");
    expect(document.activeElement).toBe(view.container.querySelector("h1"));
    expect(scrolledTo).toEqual([]);
  });

  it("leaves focus alone on a first load with no hash", async () => {
    await shellAt("/");
    expect(document.activeElement).toBe(document.body);
    expect(scrolledTo).toEqual([]);
  });

  it("tolerates a malformed percent escape in the hash", async () => {
    const view = await shellAt("/#%E0%A4%A");
    await waitFor(() => expect(document.activeElement).toBe(view.container.querySelector("h1")));
  });
});

describe("the scenario view in the shell", () => {
  it("shows the section for results against the thesis on the story, with today's two entries", async () => {
    const view = await shellAt("/");
    const section = view.container.querySelector("#against-the-thesis")!;
    expect(section).not.toBeNull();
    expect(section.querySelectorAll("li.x-entry")).toHaveLength(realIndex.against_thesis.entries.length);
  });

  it("re-renders the chart and the sentences when the model is switched, and keeps ?model=", async () => {
    const view = await shellAt("/scenario/s1/");
    await view.findByRole("figure");
    const leadOf = () => view.container.querySelector("li.lead .result-sentence")!.textContent;
    const haiku = leadOf();
    expect(view.container.querySelector("figcaption")!.textContent).toContain("Haiku 5.5");
    expect(view.container.querySelectorAll(".goal-row[data-goal=B] circle")).toHaveLength(60);

    const group = view.getByRole("group", { name: explorerLabels.modelSwitch });
    fireEvent.click(within(group).getByRole("button", { name: modelName(OTHER) }));
    await waitFor(() =>
      expect(view.container.querySelector("figcaption")!.textContent).toContain("gpt-oss-120b"),
    );
    expect(window.location.search).toBe(`?model=${OTHER}`);
    expect(view.container.querySelectorAll(".goal-row[data-goal=B] circle")).toHaveLength(56);
    expect(leadOf()).not.toBe(haiku); // gpt-oss-120b's C vs D is a different result from Haiku 5.5's
    expect(view.container.querySelectorAll(".result-sentence")).toHaveLength(5);
  });

  it("starts the goal toggles over on another scenario", async () => {
    const view = await shellAt("/scenario/s1/");
    await view.findByRole("figure");
    fireEvent.click(view.getByRole("button", { name: /\(A\)/ }));
    expect(view.container.querySelector<HTMLElement>(".goal-row[data-goal=A]")!.dataset["off"]).toBe("true");
    const clicks = watchClicks();
    fireEvent.click(view.getByRole("link", { name: explorerLabels.navScenario("s2") }));
    clicks.stop();
    await view.findByRole("figure");
    expect(view.container.querySelector<HTMLElement>(".goal-row[data-goal=A]")!.dataset["off"]).toBe("false");
  });

  it("has no axe violations on / with the section, or on a loaded scenario view", async () => {
    const story = await shellAt("/");
    expect(await violations(story.container)).toEqual([]);
    cleanup();
    const scenario = await shellAt("/scenario/s3/");
    await scenario.findByRole("figure");
    expect(await violations(scenario.container)).toEqual([]);
  });
});
