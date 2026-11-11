// After `vite build --mode explorer`: writes one HTML file per path (Phase 6 IMPLEMENTATION doc section 6, C3 decision
// 3) from the explorer's single built page, each with its own title, description and canonical address, then deletes
// the built page. All share one bundle. The paths come from the data: the scenario ids from the index and the case
// labels from the cases index, never from a list written here. The titles and descriptions are his words, in
// src/explorer/his.json. Each page also carries the link-preview tags for its share card (C7, write-cards.mjs draws
// the card): og: and twitter: tags naming cards/<slug>.png, with the image's alternative text from the labels.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  CARD_HEIGHT,
  CARD_WIDTH,
  SAFE_SEGMENT,
  SITE_ORIGIN,
  allRoutes,
  cardSlug,
  pageMeta,
  pathOf,
} from "../src/explorer/page-meta.mjs";
import { loadTs } from "./load-ts.mjs";

const escapeHtml = (text) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/**
 * One page's HTML from the built template: its title, a description, the canonical link, the link-preview tags for its
 * card (`card` is `{ slug, alt }`: the file's name and the image's alternative text) and `noindex` (removed at Phase
 * 6.5's go-live). The built page's script, stylesheet, preload and icon tags are kept as they are.
 */
export function renderPage(template, path, { title, description }, card) {
  if (!/<title>[^<]*<\/title>/.test(template)) throw new Error("write-paths: the built page has no <title>");
  if (card === undefined || !SAFE_SEGMENT.test(card.slug) || card.alt === "" || card.alt === undefined) {
    throw new Error(`write-paths: ${path} has no card slug and alternative text`);
  }
  const meta = (attribute, name, content) =>
    `    <meta ${attribute}="${name}" content="${escapeHtml(content)}" />`;
  const head = [
    `<title>${escapeHtml(title)}</title>`,
    meta("name", "description", description),
    `    <link rel="canonical" href="${SITE_ORIGIN}${path}" />`,
    meta("property", "og:type", "website"),
    meta("property", "og:title", title),
    meta("property", "og:description", description),
    meta("property", "og:url", `${SITE_ORIGIN}${path}`),
    meta("property", "og:image", `${SITE_ORIGIN}/cards/${card.slug}.png`),
    meta("property", "og:image:width", String(CARD_WIDTH)),
    meta("property", "og:image:height", String(CARD_HEIGHT)),
    meta("property", "og:image:alt", card.alt),
    meta("name", "twitter:card", "summary_large_image"),
  ].join("\n");
  return template.replace(/<title>[^<]*<\/title>/, () => head);
}

async function writePaths(webRoot) {
  const dist = join(webRoot, "dist-explorer");
  const templatePath = join(dist, "explorer.html");
  const template = readFileSync(templatePath, "utf8");
  const index = JSON.parse(readFileSync(join(webRoot, "explorer-data", "index.json"), "utf8"));
  const casesIndex = JSON.parse(readFileSync(join(webRoot, "explorer-data", index.files.cases), "utf8"));
  const pages = JSON.parse(readFileSync(join(webRoot, "src", "explorer", "his.json"), "utf8")).pages;
  // The image's alternative text is a label (copy.ts), which a plain Node script reads through Vite's module runner.
  const { explorerCardLabels } = await loadTs(webRoot, "src/explorer/copy.ts");

  const scenarioIds = index.scenarios.map((s) => s.scenario_id);
  const caseLabels = casesIndex.cases.map((c) => c.label);
  for (const segment of [...scenarioIds, ...caseLabels]) {
    if (!SAFE_SEGMENT.test(segment)) throw new Error(`write-paths: "${segment}" is not a safe path segment`);
  }

  const written = [];
  for (const route of allRoutes(scenarioIds, caseLabels)) {
    const path = pathOf(route);
    const folder = join(dist, ...path.split("/").filter(Boolean));
    mkdirSync(folder, { recursive: true });
    const card = { slug: cardSlug(route), alt: explorerCardLabels.cardAlt[route.kind] };
    writeFileSync(join(folder, "index.html"), renderPage(template, path, pageMeta(route, pages), card));
    written.push(path);
  }
  rmSync(templatePath);
  return written;
}

// Run as a script, not when a test imports renderPage.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const webRoot = fileURLToPath(new URL("../", import.meta.url));
  const written = await writePaths(webRoot);
  console.log(`write-paths: wrote ${written.length} HTML files`);
  for (const path of written) console.log(`  ${path}`);
}
