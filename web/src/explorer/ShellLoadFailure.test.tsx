import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { explorerLabels } from "./copy";
import { realApi } from "./fixtures";
import { Shell } from "./Shell";

// A view chunk that will not load (C6 part A): the studies view's module throws when it is imported, which is what a
// dynamic import that rejects looks like to `React.lazy`. The other views are the real ones.
vi.mock("./Studies", () => {
  throw new Error("the studies chunk did not load");
});

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  window.scrollTo = vi.fn();
  vi.spyOn(console, "error").mockImplementation(() => {}); // React logs an error that an error boundary catches
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("a view chunk that fails to load", () => {
  it("shows the load-failed line as an alert, with the header still there, not a blank page", async () => {
    window.history.replaceState(null, "", "/studies/");
    const view = render(<Shell data={realApi()} />);
    const alert = await view.findByRole("alert");
    expect(alert.textContent).toBe(explorerLabels.loadFailed);
    expect(view.container.querySelector("header.site-header")).not.toBeNull();
    expect(view.container.querySelector("main")?.textContent).toBe(explorerLabels.loadFailed);
    expect(view.container.querySelector("footer")).not.toBeNull();
  });

  it("clears on a navigation to another path, which loads normally", async () => {
    window.history.replaceState(null, "", "/studies/");
    const view = render(<Shell data={realApi()} />);
    await view.findByRole("alert");
    const clicks: boolean[] = [];
    const listener = (event: Event) => {
      clicks.push(event.defaultPrevented);
      event.preventDefault();
    };
    document.addEventListener("click", listener);
    fireEvent.click(view.getByRole("link", { name: explorerLabels.navMemos }));
    document.removeEventListener("click", listener);
    expect(window.location.pathname).toBe("/memos/");
    await waitFor(() => expect(view.container.querySelector("article.memo-card")).not.toBeNull());
    expect(view.queryByRole("alert")).toBeNull();
  });
});
