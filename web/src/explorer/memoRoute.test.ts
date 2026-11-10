import { describe, expect, it } from "vitest";
import {
  DEFAULT_MODEL,
  MEMO_KINDS,
  memoHref,
  modelFromSearch,
  readMemoQuery,
  searchAfterModelSwitch,
  searchWithModel,
} from "./route";

describe("the memo reader's query", () => {
  it("is read parameter by parameter, null where absent", () => {
    expect(readMemoQuery("")).toEqual({ kind: null, scenario: null, objective: null, run: null });
    expect(
      readMemoQuery("?kind=thinking&scenario=s1&objective=C&run=r-abc&model=gpt-oss-openrouter"),
    ).toEqual({
      kind: "thinking",
      scenario: "s1",
      objective: "C",
      run: "r-abc",
    });
    expect(MEMO_KINDS).toEqual(["grid", "thinking"]);
  });

  it("builds a link that keeps every parameter, the model dropped only for the default", () => {
    expect(memoHref({ kind: "grid", scenario: "s2", objective: "B", run: "r-x" }, DEFAULT_MODEL)).toBe(
      "/memos/?kind=grid&scenario=s2&objective=B&run=r-x",
    );
    expect(memoHref({ kind: "thinking", scenario: "s1", objective: "A" }, "gpt-oss-openrouter")).toBe(
      "/memos/?kind=thinking&scenario=s1&objective=A&model=gpt-oss-openrouter",
    );
    expect(memoHref({ kind: "grid", scenario: "s1", objective: "A", run: null }, DEFAULT_MODEL)).toBe(
      "/memos/?kind=grid&scenario=s1&objective=A",
    );
  });

  it("round-trips through the reader's parsing, with the model", () => {
    const href = memoHref({ kind: "grid", scenario: "s3", objective: "E", run: "r-1" }, "gpt-oss-openrouter");
    const search = href.slice(href.indexOf("?"));
    expect(readMemoQuery(search)).toEqual({ kind: "grid", scenario: "s3", objective: "E", run: "r-1" });
    expect(modelFromSearch(search, ["haiku-5-5", "gpt-oss-openrouter"])).toBe("gpt-oss-openrouter");
  });

  it("is kept by the model switch: every other parameter stays when the model changes", () => {
    const search = "?kind=thinking&scenario=s1&objective=D&run=r-9";
    const switched = searchWithModel(search, "gpt-oss-openrouter");
    expect(readMemoQuery(switched)).toEqual(readMemoQuery(search));
    expect(switched).toContain("model=gpt-oss-openrouter");
    expect(searchWithModel(switched, DEFAULT_MODEL)).toBe(search);
  });

  it("drops the run on the model switch on /memos/ only: a run id belongs to one model's set", () => {
    const search = "?kind=grid&scenario=s2&objective=D&run=r-9";
    const switched = searchAfterModelSwitch("/memos/", search, "gpt-oss-openrouter");
    expect(readMemoQuery(switched)).toEqual({ kind: "grid", scenario: "s2", objective: "D", run: null });
    expect(switched).toBe("?kind=grid&scenario=s2&objective=D&model=gpt-oss-openrouter");
    expect(searchAfterModelSwitch("/memos/", switched, DEFAULT_MODEL)).toBe(
      "?kind=grid&scenario=s2&objective=D",
    );
    // Every other page keeps every parameter, a `run` among them.
    for (const path of ["/", "/scenario/s1/", "/cases/", "/cases/closure-19/", "/studies/"])
      expect(searchAfterModelSwitch(path, search, "gpt-oss-openrouter"), path).toBe(
        searchWithModel(search, "gpt-oss-openrouter"),
      );
  });
});
