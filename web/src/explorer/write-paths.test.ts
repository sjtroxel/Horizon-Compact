import { describe, expect, it } from "vitest";
import { renderPage } from "../../scripts/write-paths.mjs";

describe("write-paths: one page's HTML", () => {
  const template =
    '<head>\n    <meta name="robots" content="noindex" />\n    <title>Horizon Compact</title>\n    <link rel="icon" href="/favicon.svg" />\n  </head>';

  it("sets the title, description and canonical address, and keeps the rest", () => {
    const html = renderPage(template, "/scenario/s1/", {
      title: "A title (s1)",
      description: "A description.",
    });
    expect(html).toContain("<title>A title (s1)</title>");
    expect(html).toContain('<meta name="description" content="A description." />');
    expect(html).toContain('<link rel="canonical" href="https://horizon-compact.vercel.app/scenario/s1/" />');
    expect(html).toContain('<meta name="robots" content="noindex" />');
    expect(html).toContain('<link rel="icon" href="/favicon.svg" />');
  });

  it("escapes what it is given", () => {
    const html = renderPage(template, "/", { title: 'A <b> & "c"', description: 'x" onload="y' });
    expect(html).toContain("<title>A &lt;b&gt; &amp; &quot;c&quot;</title>");
    expect(html).toContain('content="x&quot; onload=&quot;y"');
    expect(html).not.toContain("<b>");
  });

  it("refuses a page with no title to replace", () => {
    expect(() => renderPage("<head></head>", "/", { title: "t", description: "d" })).toThrow(/no <title>/);
  });
});
