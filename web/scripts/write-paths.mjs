// After `vite build --mode explorer`: writes one HTML file per path (Phase 6 IMPLEMENTATION doc section 6, C3 decision
// 3) from the explorer's single built page, each with its own title, description and canonical address, then deletes
// the built page. All share one bundle. The paths come from the data: the scenario ids from the index and the case
// labels from the cases index, never from a list written here. The titles and descriptions are his words, in
// src/explorer/his.json (placeholders until he writes them).
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { SITE_ORIGIN, allRoutes, pageMeta, pathOf } from "../src/explorer/page-meta.mjs";

const escapeHtml = (text) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** A path segment that is safe to make a folder from: the ids come from data, and a folder is written for each. */
const SAFE_SEGMENT = /^[a-z0-9][a-z0-9-]*$/;

/**
 * One page's HTML from the built template: its title, a description, the canonical link and `noindex` (removed at
 * Phase 6.5's go-live). The built page's script, stylesheet, preload and icon tags are kept as they are.
 */
export function renderPage(template, path, { title, description }) {
  if (!/<title>[^<]*<\/title>/.test(template)) throw new Error("write-paths: the built page has no <title>");
  const head =
    `<title>${escapeHtml(title)}</title>\n` +
    `    <meta name="description" content="${escapeHtml(description)}" />\n` +
    `    <link rel="canonical" href="${SITE_ORIGIN}${path}" />`;
  return template.replace(/<title>[^<]*<\/title>/, () => head);
}

function writePaths(webRoot) {
  const dist = join(webRoot, "dist-explorer");
  const templatePath = join(dist, "explorer.html");
  const template = readFileSync(templatePath, "utf8");
  const index = JSON.parse(readFileSync(join(webRoot, "explorer-data", "index.json"), "utf8"));
  const casesIndex = JSON.parse(readFileSync(join(webRoot, "explorer-data", index.files.cases), "utf8"));
  const pages = JSON.parse(readFileSync(join(webRoot, "src", "explorer", "his.json"), "utf8")).pages;

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
    writeFileSync(join(folder, "index.html"), renderPage(template, path, pageMeta(route, pages)));
    written.push(path);
  }
  rmSync(templatePath);
  return written;
}

// Run as a script, not when a test imports renderPage.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const webRoot = fileURLToPath(new URL("../", import.meta.url));
  const written = writePaths(webRoot);
  console.log(`write-paths: wrote ${written.length} HTML files`);
  for (const path of written) console.log(`  ${path}`);
}
