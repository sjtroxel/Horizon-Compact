// The distribution's viewer-request function (infra/terraform/main/functions/site-paths.js; Phase 6.5 decision B),
// run here on each kind of path. The file is CloudFront's own runtime's script, a bare `handler`; it is read and
// evaluated as written, so what is tested is the code Terraform uploads.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

interface Param {
  value: string;
  multiValue?: Array<{ value: string }>;
}
interface Request {
  uri: string;
  querystring: Record<string, Param>;
}
interface Redirect {
  statusCode: number;
  statusDescription: string;
  headers: Record<string, { value: string }>;
}

const SOURCE = readFileSync(
  resolve(import.meta.dirname, "../../infra/terraform/main/functions/site-paths.js"),
  "utf8",
);
const handler = new Function(`${SOURCE}\nreturn handler;`)() as (event: {
  request: Request;
}) => Request | Redirect;

const run = (uri: string, querystring: Record<string, Param> = {}) =>
  handler({ request: { uri, querystring } });

describe("the site's viewer-request function", () => {
  it("serves a path ending in / its own index.html, the root included", () => {
    for (const [uri, file] of [
      ["/", "/index.html"],
      ["/methods/", "/methods/index.html"],
      ["/scenario/s1/", "/scenario/s1/index.html"],
      ["/cases/closure-07/", "/cases/closure-07/index.html"],
    ]) {
      expect(run(uri!), uri).toMatchObject({ uri: file });
    }
  });

  it("keeps the query string of a page path (the memo reader's address)", () => {
    const querystring = { set: { value: "grid" }, run: { value: "r1" } };
    expect(run("/memos/", querystring)).toEqual({ uri: "/memos/index.html", querystring });
  });

  it("passes a file through unchanged", () => {
    for (const uri of [
      "/assets/explorer-x.js",
      "/data/index.json",
      "/cards/story.png",
      "/404.html",
      "/favicon.svg",
    ]) {
      expect(run(uri), uri).toEqual({ uri, querystring: {} });
    }
  });

  it("redirects a page path missing its slash, permanently and relatively, with its query string", () => {
    expect(run("/methods")).toEqual({
      statusCode: 301,
      statusDescription: "Moved Permanently",
      headers: { location: { value: "/methods/" } },
    });
    const redirect = run("/memos", {
      set: { value: "grid" },
      g: { value: "A", multiValue: [{ value: "A" }, { value: "B" }] },
    }) as Redirect;
    expect(redirect.statusCode).toBe(301);
    expect(redirect.headers["location"]!.value).toBe("/memos/?set=grid&g=A&g=B");
    // Relative, so it stays on whichever host was asked: the public address's rewrite or the distribution's own.
    expect(redirect.headers["location"]!.value.startsWith("/")).toBe(true);
  });

  it("treats a dot in an earlier segment as part of a page path, not a file", () => {
    expect(run("/v1.2/page")).toMatchObject({ statusCode: 301 });
    expect(run("/v1.2/page/")).toMatchObject({ uri: "/v1.2/page/index.html" });
  });
});
