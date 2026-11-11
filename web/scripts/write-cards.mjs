// After `write-paths.mjs` in `build:explorer` (Phase 6 IMPLEMENTATION doc section 10, C7): draws one PNG share card for
// every route, 1200 by 630, into dist-explorer/cards/<slug>.png. The routes are the very list write-paths writes a page
// for (allRoutes over the same two indexes), so the two cannot drift apart. The card's words come from cards.ts, which
// reads the same data files and the same copy as the views; this script measures, lays out, draws and writes.
//
// The fonts are the committed TTFs in web/fonts-ttf/, with system fonts off (card-render.mjs). They are read from there
// and never copied into a build folder: check-dist fails on a .ttf in a build.
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { CARD_WIDTH, SAFE_SEGMENT, allRoutes, cardSlug } from "../src/explorer/page-meta.mjs";
import { assertFonts, makeMeasure, rasterize } from "./card-render.mjs";
import { loadTs } from "./load-ts.mjs";

/**
 * Writes the cards into `outDir` (cleared first, so a card for a route that no longer exists cannot linger). Returns one
 * entry per card: the route, the slug and the PNG's size.
 */
export async function writeCards(webRoot, outDir = join(webRoot, "dist-explorer", "cards")) {
  const cards = await loadTs(webRoot, "src/explorer/cards.ts");
  const dataRoot = join(webRoot, "explorer-data");
  const files = cards.collectCardFiles((relative) =>
    JSON.parse(readFileSync(join(dataRoot, relative), "utf8")),
  );
  const index = files["index.json"];
  const casesIndex = files[index.files.cases];
  const scenarioIds = index.scenarios.map((s) => s.scenario_id);
  const caseLabels = casesIndex.cases.map((c) => c.label);

  assertFonts(cards.FONT_FACES);
  const measure = makeMeasure(cards.measureSvg);

  rmSync(outDir, { recursive: true, force: true });
  mkdirSync(outDir, { recursive: true });
  const written = [];
  const slugs = new Set();
  for (const route of allRoutes(scenarioIds, caseLabels)) {
    const slug = cardSlug(route);
    if (!SAFE_SEGMENT.test(slug) || slugs.has(slug))
      throw new Error(`write-cards: "${slug}" is not a safe, unique name`);
    slugs.add(slug);
    const card = cards.buildCard(route, files);
    const layout = cards.layoutCard(card, measure);
    cards.assertFits(card, layout);
    const png = rasterize(cards.cardSvg(layout), CARD_WIDTH);
    writeFileSync(join(outDir, `${slug}.png`), png);
    written.push({ route, slug, bytes: png.length });
  }
  return written;
}

// Run as a script, not when a test imports writeCards.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const webRoot = fileURLToPath(new URL("../", import.meta.url));
  const started = performance.now();
  const written = await writeCards(webRoot);
  let total = 0;
  for (const { bytes } of written) total = total + bytes;
  console.log(
    `write-cards: wrote ${written.length} cards, ${total} bytes, in ${(performance.now() - started).toFixed(0)} ms`,
  );
  for (const { slug, bytes } of written) console.log(`  cards/${slug}.png ${bytes}`);
}
