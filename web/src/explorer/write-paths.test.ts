import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { renderPage } from "../../scripts/write-paths.mjs";
import { explorerCardLabels, explorerHis } from "./copy";
import { WEB_ROOT, realCasesIndex, realIndex } from "./fixtures";
import {
  CARD_HEIGHT,
  CARD_WIDTH,
  SAFE_SEGMENT,
  SITE_ORIGIN,
  allRoutes,
  cardSlug,
  pageMeta,
  pathOf,
  routeOfPath,
} from "./page-meta.mjs";

const card = { slug: "scenario-s1", alt: "A card for one decision." };

describe("write-paths: one page's HTML", () => {
  const template =
    '<head>\n    <meta name="robots" content="noindex" />\n    <title>Horizon Compact</title>\n    <link rel="icon" href="/favicon.svg" />\n  </head>';

  it("sets the title, description and canonical address, and keeps the rest", () => {
    const html = renderPage(
      template,
      "/scenario/s1/",
      { title: "A title (s1)", description: "A description." },
      card,
    );
    expect(html).toContain("<title>A title (s1)</title>");
    expect(html).toContain('<meta name="description" content="A description." />');
    expect(html).toContain('<link rel="canonical" href="https://horizon-compact.vercel.app/scenario/s1/" />');
    expect(html).toContain('<meta name="robots" content="noindex" />');
    expect(html).toContain('<link rel="icon" href="/favicon.svg" />');
  });

  it("escapes what it is given", () => {
    const html = renderPage(
      template,
      "/",
      { title: 'A <b> & "c"', description: 'x" onload="y' },
      { slug: "story", alt: 'An "alt" <i> & more' },
    );
    expect(html).toContain("<title>A &lt;b&gt; &amp; &quot;c&quot;</title>");
    expect(html).toContain('content="x&quot; onload=&quot;y"');
    expect(html).toContain('<meta property="og:title" content="A &lt;b&gt; &amp; &quot;c&quot;" />');
    expect(html).toContain(
      '<meta property="og:image:alt" content="An &quot;alt&quot; &lt;i&gt; &amp; more" />',
    );
    expect(html).not.toContain("<b>");
    expect(html).not.toContain("<i>");
  });

  it("refuses a page with no title to replace, and a card with no safe name or no alternative text", () => {
    const meta = { title: "t", description: "d" };
    expect(() => renderPage("<head></head>", "/", meta, card)).toThrow(/no <title>/);
    expect(() => renderPage(template, "/", meta, undefined as never)).toThrow(/no card slug/);
    expect(() => renderPage(template, "/", meta, { slug: "../x", alt: "a" })).toThrow(/no card slug/);
    expect(() => renderPage(template, "/", meta, { slug: "story", alt: "" })).toThrow(/no card slug/);
  });
});

describe("write-paths: the link-preview tags (C7)", () => {
  const template = "<head>\n    <title>Horizon Compact</title>\n  </head>";
  const scenarioIds = realIndex.scenarios.map((s) => s.scenario_id);
  const caseLabels = realCasesIndex.cases.map((c) => c.label);
  const routes = allRoutes(scenarioIds, caseLabels);
  const tags = (html: string, key: string) =>
    (html.match(/<meta\b[^>]*>/g) ?? []).filter((tag) => new RegExp(`(property|name)="${key}"`).test(tag));

  it.each(routes.map((route) => [pathOf(route), route] as const))(
    "%s: each tag once, with the right slug, an absolute address, and the page's own words",
    (path, route) => {
      const meta = pageMeta(route, explorerHis.pages);
      const html = renderPage(template, path, meta, {
        slug: cardSlug(route),
        alt: explorerCardLabels.cardAlt[route.kind]!,
      });
      const content = (key: string) => {
        expect(tags(html, key), key).toHaveLength(1);
        return /content="([^"]*)"/.exec(tags(html, key)[0]!)![1]!;
      };
      expect(content("og:type")).toBe("website");
      expect(content("og:title")).toBe(meta.title);
      expect(content("og:description")).toBe(meta.description);
      expect(content("og:url")).toBe(`${SITE_ORIGIN}${path}`);
      expect(content("og:image")).toBe(`${SITE_ORIGIN}/cards/${cardSlug(route)}.png`);
      expect(content("og:image")).toMatch(/^https:\/\/horizon-compact\.vercel\.app\/cards\/[a-z0-9-]+\.png$/);
      expect(content("og:image:width")).toBe(String(CARD_WIDTH));
      expect(content("og:image:height")).toBe(String(CARD_HEIGHT));
      expect(content("og:image:alt")).toBe(explorerCardLabels.cardAlt[route.kind]);
      expect(content("twitter:card")).toBe("summary_large_image");
    },
  );

  it("gives each path its own card, and a name that is a safe file name", () => {
    const slugs = routes.map(cardSlug);
    expect(new Set(slugs).size).toBe(routes.length);
    for (const slug of slugs) expect(slug).toMatch(SAFE_SEGMENT);
    expect(slugs).toHaveLength(13);
  });

  it("reads a path back to its route (the checks use it), and refuses a path no page is written for", () => {
    for (const route of routes) expect(routeOfPath(pathOf(route))).toEqual(route);
    for (const path of ["/scenario/s1", "/nope/", "/scenario/", "/cases/a/b/", "//", "/studies/x/"]) {
      expect(routeOfPath(path), path).toBeNull();
    }
  });

  it("leaves the placeholder page without a card: no og: tag, no twitter: tag, no cards/ address", () => {
    const html = readFileSync(resolve(WEB_ROOT, "index.html"), "utf8");
    expect(html).not.toMatch(/og:|twitter:|cards\//);
  });
});
