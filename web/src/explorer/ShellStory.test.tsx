import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { explorerLabels as L } from "./copy";
import { createDataApi } from "./data";
import { fileFetcher, realApi, realIndex, warmViews } from "./fixtures";
import { Shell } from "./Shell";

const OTHER = realIndex.models.map((m) => m.model_key).find((key) => key !== "haiku-5-5")!;

beforeAll(warmViews);
beforeEach(() => {
  window.history.replaceState(null, "", "/");
  window.scrollTo = vi.fn(); // jsdom has no scrolling
});
afterEach(cleanup);

async function shellAt(path: string, data = realApi()) {
  window.history.replaceState(null, "", path);
  const view = render(<Shell data={data} />);
  await view.findByRole("heading", { level: 1 });
  return view;
}

const story = (container: HTMLElement) => container.querySelector<HTMLElement>(".story")!;
const filled = (container: HTMLElement) =>
  waitFor(() => {
    expect(container.querySelector(".story")).not.toBeNull();
    expect(container.querySelectorAll(".story-wait")).toHaveLength(0);
  });

describe("the model switch and the story", () => {
  it("shows no model switch on /", async () => {
    const home = await shellAt("/");
    expect(home.queryByRole("region", { name: L.modelSwitch })).toBeNull();
  });

  it.each(["/scenario/s1/", "/cases/", "/studies/", "/memos/"])(
    "shows a model switch on %s",
    async (path) => {
      const view = await shellAt(path);
      expect(view.getByRole("region", { name: L.modelSwitch })).toBeTruthy();
    },
  );

  it("shows the same story under ?model= as without it, and the header's links keep the query", async () => {
    const plain = await shellAt("/");
    await filled(plain.container);
    const without = story(plain.container).textContent;
    cleanup();
    const asked = await shellAt(`/?model=${OTHER}`);
    await filled(asked.container);
    expect(story(asked.container).textContent).toBe(without);
    expect(asked.container.querySelector(".switch-bar")).toBeNull();
    const nav = asked.getByRole("navigation", { name: L.navLabel });
    for (const a of within(nav).getAllByRole("link"))
      expect(a.getAttribute("href")).toMatch(new RegExp(`\\?model=${OTHER}$`));
    // A link out of a beat that is about one model carries that model: the story's own links never follow the query.
    const links = [...story(asked.container).querySelectorAll("a")].map((a) => a.getAttribute("href"));
    expect(links).toContain("/scenario/s1/");
    expect(links).toContain(`/scenario/s2/?model=${OTHER}`);
  });
});

describe("a hash on / waits for the story's data", () => {
  const scrolledTo: Array<{ element: Element; waiting: number }> = [];
  const original = Element.prototype.scrollIntoView;
  beforeEach(() => {
    scrolledTo.length = 0;
    Element.prototype.scrollIntoView = function (this: Element) {
      // Record how many beats were still waiting for their data at the moment of the scroll.
      scrolledTo.push({ element: this, waiting: document.querySelectorAll(".story-wait").length });
    };
  });
  afterEach(() => {
    Element.prototype.scrollIntoView = original;
  });

  /** A data source whose grid and case files wait for `release`, so the beats above the target are still empty. */
  function delayed() {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => (release = resolve));
    const base = fileFetcher();
    const data = createDataApi(async (path) => {
      if ((path.includes("/grid/") || path.includes("/cases/")) && !path.endsWith("/index.json")) await gate;
      return base(path);
    });
    return { data, release };
  }

  it("on a first load scrolls once, after the data, to the section, and focuses it", async () => {
    const { data, release } = delayed();
    const view = await shellAt("/#against-the-thesis", data);
    // The story is mounted and the section is in the page, but the beats above it are still empty: no reveal yet.
    expect(view.container.querySelector("#against-the-thesis")).not.toBeNull();
    expect(view.container.querySelectorAll(".story-wait").length).toBeGreaterThan(0);
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(scrolledTo).toEqual([]);
    expect(document.activeElement?.id).not.toBe("against-the-thesis");

    release();
    await waitFor(() => expect(document.activeElement?.id).toBe("against-the-thesis"));
    expect(scrolledTo).toHaveLength(1);
    expect(scrolledTo[0]!.element).toBe(view.container.querySelector("#against-the-thesis"));
    expect(scrolledTo[0]!.waiting).toBe(0); // every beat had loaded
    expect(view.container.querySelector("section#beat-s1 figure")).not.toBeNull();
  });

  it("scrolls once even when a beat's data failed, because the reveal waits for loaded or failed", async () => {
    const base = fileFetcher();
    const data = createDataApi(async (path) =>
      path.endsWith("/grid/haiku-5-5/s4.json") ? ({ ok: false, status: 500 } as Response) : base(path),
    );
    const view = await shellAt("/#against-the-thesis", data);
    await waitFor(() => expect(document.activeElement?.id).toBe("against-the-thesis"));
    expect(scrolledTo).toHaveLength(1);
    expect(view.container.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0);
  });

  it("on a navigation to / with a hash from another path, scrolls once, after the data", async () => {
    const { data, release } = delayed();
    // Start on a path that needs none of the delayed files, then follow a link to the section.
    const view = await shellAt("/memos/", data);
    const link = view.getByRole("link", { name: L.navStory });
    link.setAttribute("href", "/#against-the-thesis");
    fireEvent.click(link);
    await waitFor(() => expect(view.container.querySelector("#against-the-thesis")).not.toBeNull());
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(scrolledTo).toEqual([]);
    release();
    await waitFor(() => expect(document.activeElement?.id).toBe("against-the-thesis"));
    expect(scrolledTo).toHaveLength(1);
    expect(scrolledTo[0]!.waiting).toBe(0);
  });

  it("on a navigation to / with a hash when the story is already on screen, scrolls at once, once", async () => {
    const view = await shellAt("/");
    await filled(view.container);
    const link = view.getByRole("link", { name: L.navStory });
    link.setAttribute("href", `/?model=${OTHER}#against-the-thesis`);
    fireEvent.click(link);
    await waitFor(() => expect(document.activeElement?.id).toBe("against-the-thesis"));
    expect(scrolledTo).toHaveLength(1);
  });

  it("leaves / without a hash as before: no scroll into view on a first load, the heading on a navigation", async () => {
    const view = await shellAt("/scenario/s1/");
    const link = view.getByRole("link", { name: L.navStory });
    fireEvent.click(link);
    await waitFor(() => expect(document.activeElement).toBe(view.container.querySelector("h1")));
    expect(scrolledTo).toEqual([]);
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });
});
