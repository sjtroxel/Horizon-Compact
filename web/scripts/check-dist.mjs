// Checks the built files (Phase 1.5 IMPLEMENTATION doc sections 8 and 9; Phase 6 C3): the asset budget, and that
// nothing in the build asks for another host, runs inline or styles inline. Run after the build it checks and prints
// the measured sizes; exits 1 on the first group of failures.
//
//   node scripts/check-dist.mjs                  the placeholder page, in dist/ (what Deploy syncs)
//   node scripts/check-dist.mjs --mode explorer  the explorer, in dist-explorer/ (never synced)
//
// Placeholder mode also fails if anything of the explorer reached dist/: a copy of a data file, an official run id
// or sweep id, any path with "explorer" in it, a cards/ folder or an og:image tag. The public page must not change
// until Phase 6.5's go-live. Explorer mode checks each page's link-preview tags and the share cards they name (C7).
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { extname, join } from "node:path";
import { gzipSync } from "node:zlib";
import { CARD_HEIGHT, CARD_WIDTH, cardSlug, routeOfPath } from "../src/explorer/page-meta.mjs";
import { VIEW_MODULES } from "../src/explorer/view-modules.mjs";
import { entryKeyOf, pathFiles, reachedFromEntry } from "./dist-closure.mjs";
import { findDataCopies, findLeaks, loadDataHashes, loadOfficialIds, walk } from "./leaks.mjs";

const SITE_ORIGIN = "https://horizon-compact.vercel.app";
const JS_BUDGET = 100 * 1024; // gzipped: all JavaScript in placeholder mode; what one path loads in explorer mode
const FONT_BUDGET = 150 * 1024; // all font files
const EXPECTED_RUN_IDS = 2290; // the official runs of the grid and the thinking sub-study (Phase 6 doc section 5.3)
const EXPECTED_SWEEP_IDS = 13; // two grids, the thinking sub-study, ten case sweeps

const args = process.argv.slice(2);
const modeIndex = args.indexOf("--mode");
const mode = modeIndex === -1 ? "placeholder" : args[modeIndex + 1];
if (mode !== "placeholder" && mode !== "explorer") {
  console.error(`check-dist: unknown mode "${mode}"; use no flag, or --mode explorer`);
  process.exit(2);
}
const explorer = mode === "explorer";

const WEB = new URL("../", import.meta.url).pathname;
const DIST = join(WEB, explorer ? "dist-explorer/" : "dist/");
const failures = [];
const fail = (message) => failures.push(message);

const all = walk(DIST);
const rel = (path) => path.slice(DIST.length);
// In explorer mode the copied data lives under data/ and is not code: the budgets and the page rules look at the rest.
const DATA = join(DIST, "data") + "/";
const files = explorer ? all.filter((f) => !f.startsWith(DATA)) : all;

// JavaScript, gzipped, in all. The placeholder page is one bundle, so its total is its budget. The explorer is split by
// path (Phase 6 doc section 17): its total is only reported, and the budget is checked for what each path loads, below.
const js = files.filter((f) => extname(f) === ".js");
const jsGzip = js.reduce((sum, f) => sum + gzipSync(readFileSync(f)).length, 0);
if (!explorer && jsGzip > JS_BUDGET)
  fail(`JavaScript is ${jsGzip} bytes gzipped, over the ${JS_BUDGET} budget`);

// Fonts: .woff2 only, under budget.
const fontExtensions = new Set([".woff", ".woff2", ".ttf", ".otf", ".eot"]);
const fonts = files.filter((f) => fontExtensions.has(extname(f)));
for (const f of fonts) if (extname(f) !== ".woff2") fail(`font file that is not WOFF2: ${rel(f)}`);
const fontBytes = fonts.reduce((sum, f) => sum + statSync(f).size, 0);
if (fontBytes > FONT_BUDGET) fail(`fonts are ${fontBytes} bytes, over the ${FONT_BUDGET} budget`);

// HTML: no inline script, no style element, no style attribute, nothing that points at a host.
const htmlFiles = files.filter((f) => extname(f) === ".html");
const isHost = (value) => /^(?:[a-z][a-z0-9+.-]*:)?\/\//i.test(value) || /^[a-z][a-z0-9+.-]*:/i.test(value);

// The path a page is served at: dist/index.html is "/", scenario/s1/index.html is "/scenario/s1/".
const pathOfPage = (file) => "/" + rel(file).replace(/index\.html$/, "");

// The link-preview tags of one explorer page (C7): each exactly once, each saying what the page says elsewhere, and the
// image named being the page's own card, which is checked to exist further down.
const namedCards = new Set(); // the card file names the pages name, so a file in cards/ that no page names is found
function checkPreviewTags(html, name, file) {
  const path = pathOfPage(file);
  const route = routeOfPath(path);
  if (route === null) {
    fail(`${name}: no route for the path ${path}`);
    return;
  }
  const tagValue = (attribute, key) => {
    const tags = (html.match(/<meta\b[^>]*>/gi) ?? []).filter((tag) =>
      new RegExp(`\\b${attribute}\\s*=\\s*"${key}"`, "i").test(tag),
    );
    if (tags.length !== 1) {
      fail(`${name} has ${tags.length} ${key} tags; it must have exactly 1`);
      return undefined;
    }
    return /\bcontent\s*=\s*"([^"]*)"/i.exec(tags[0])?.[1];
  };
  const title = /<title>([^<]+)<\/title>/.exec(html)?.[1];
  const description = /<meta\b[^>]*\bname\s*=\s*"description"[^>]*\bcontent\s*=\s*"([^"]*)"/i.exec(html)?.[1];
  const expectations = [
    ["property", "og:type", "website"],
    ["property", "og:title", title],
    ["property", "og:description", description],
    ["property", "og:url", `${SITE_ORIGIN}${path}`],
    ["property", "og:image", `${SITE_ORIGIN}/cards/${cardSlug(route)}.png`],
    ["property", "og:image:width", String(CARD_WIDTH)],
    ["property", "og:image:height", String(CARD_HEIGHT)],
    ["name", "twitter:card", "summary_large_image"],
  ];
  for (const [attribute, key, expected] of expectations) {
    const value = tagValue(attribute, key);
    if (value !== undefined && value !== expected)
      fail(`${name} ${key} is "${value}", expected "${expected}"`);
  }
  const alt = tagValue("property", "og:image:alt");
  if (alt !== undefined && alt === "") fail(`${name} has an empty og:image:alt`);
  namedCards.add(`${cardSlug(route)}.png`);
}

function checkPage(file) {
  const name = rel(file);
  const html = readFileSync(file, "utf8");
  for (const tag of html.match(/<script\b[^>]*>/gi) ?? []) {
    if (!/\bsrc=/.test(tag)) fail(`inline <script> in ${name}: ${tag}`);
  }
  if (/<style\b/i.test(html)) fail(`<style> element in ${name}`);
  if (/\sstyle\s*=/i.test(html)) fail(`style attribute in ${name}`);
  if (/<script\b[^>]*>[^<]+<\/script>/i.test(html)) fail(`script with a body in ${name}`);

  // An explorer page also names itself: its canonical link is its own address on the site, and only that. The tag is
  // checked here and left out of the rule below, which allows no other host.
  let rest = html;
  if (explorer) {
    const canonical = html.match(/<link\b[^>]*\brel\s*=\s*"canonical"[^>]*>/gi) ?? [];
    const own = `${SITE_ORIGIN}${pathOfPage(file)}`;
    if (canonical.length !== 1 || !canonical[0].includes(`href="${own}"`)) {
      fail(`${name} must have one canonical link, to ${own}`);
    }
    for (const tag of canonical) rest = rest.replace(tag, "");
    if (!/<title>[^<]+<\/title>/.test(html)) fail(`${name} has no title`);
    if (!/<meta\b[^>]*\bname\s*=\s*"description"[^>]*\bcontent\s*=\s*"[^"]+"/i.test(html)) {
      fail(`${name} has no description`);
    }
    if (!/<meta\b[^>]*\bname\s*=\s*"robots"[^>]*\bcontent\s*=\s*"noindex"/i.test(html)) {
      fail(`${name} is not noindex`);
    }
    checkPreviewTags(html, name, file);
  } else if (/\b(og|twitter):[a-z:]+/i.test(html)) {
    fail(`${name} has link-preview tags: the placeholder page must not (Phase 6 doc section 10)`);
  }
  for (const match of rest.matchAll(/\b(src|href)\s*=\s*"([^"]*)"/gi)) {
    const [, attribute, value] = match;
    const allowed = value === "/favicon.svg" || (value.startsWith("/assets/") && !isHost(value));
    if (!allowed) fail(`${name} ${attribute}="${value}" is not the favicon or a built asset`);
  }

  // Preloads: exactly two, the name's face (Big Shoulders Display 800) and the prose face (Newsreader 400), each as a
  // font with `crossorigin` (without it the browser fetches the font twice), each naming a file that is in the build.
  const preloads = (html.match(/<link\b[^>]*>/gi) ?? []).filter((tag) => /\brel\s*=\s*"preload"/i.test(tag));
  const wanted = [
    /\/big-shoulders-display-latin-800-normal-[^/"]*\.woff2$/,
    /\/newsreader-latin-400-normal-[^/"]*\.woff2$/,
  ];
  if (preloads.length !== wanted.length) {
    fail(`${name} has ${preloads.length} preload link(s); it must have exactly ${wanted.length}`);
  }
  const preloaded = [];
  for (const tag of preloads) {
    const href = /\bhref\s*=\s*"([^"]*)"/i.exec(tag)?.[1] ?? "";
    preloaded.push(href);
    if (!/\bas\s*=\s*"font"/i.test(tag)) fail(`${name} preload ${href} is not as="font"`);
    if (!/\btype\s*=\s*"font\/woff2"/i.test(tag)) fail(`${name} preload ${href} is not type="font/woff2"`);
    if (!/\scrossorigin(?=[\s>=/])/i.test(tag)) fail(`${name} preload ${href} has no crossorigin attribute`);
    if (!href.startsWith("/assets/") || !all.includes(join(DIST, href))) {
      fail(`${name} preload ${href} does not name a file in the build's assets`);
    }
  }
  for (const pattern of wanted) {
    if (!preloaded.some((href) => pattern.test(href))) fail(`${name} has no preload for ${pattern}`);
  }
}

if (explorer) {
  if (htmlFiles.length === 0) fail("no HTML file in dist-explorer/ (did write-paths run?)");
  for (const file of htmlFiles) checkPage(file);
  if (all.some((f) => rel(f) === "explorer.html"))
    fail("explorer.html is still in dist-explorer/ (write-paths deletes it)");
  if (!htmlFiles.some((f) => rel(f) === "index.html"))
    fail("dist-explorer/ has no index.html for the path /");
} else {
  const index = htmlFiles.filter((f) => rel(f) === "index.html");
  if (index.length !== 1 || htmlFiles.length !== 1) {
    fail(
      `dist/ must hold exactly one HTML file, index.html; it holds ${htmlFiles.map(rel).join(", ") || "none"}`,
    );
  }
  for (const file of index) checkPage(file);
}

// CSS: every url() is relative to the build; no @import.
const css = files.filter((f) => extname(f) === ".css");
for (const f of css) {
  const text = readFileSync(f, "utf8");
  for (const match of text.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/gi)) {
    if (isHost(match[1])) fail(`${rel(f)} has url(${match[1]}), which is another host or a data: URI`);
  }
  if (/@import/i.test(text)) fail(`${rel(f)} has an @import`);
}

// What the official data is, read from the committed files (the same functions the Vitest negative control runs).
const ids = loadOfficialIds(WEB);
if (ids.runIds.size !== EXPECTED_RUN_IDS) {
  fail(`read ${ids.runIds.size} official run ids from explorer-memos/, expected ${EXPECTED_RUN_IDS}`);
}
if (ids.sweepIds.size !== EXPECTED_SWEEP_IDS) {
  fail(`read ${ids.sweepIds.size} official sweep ids from explorer-data/, expected ${EXPECTED_SWEEP_IDS}`);
}

const summary = [];
if (explorer) {
  // The run ids are fetched by the views and never bundled: none outside data/.
  const leaks = findLeaks(files, { runIds: ids.runIds, sweepIds: new Set() });
  for (const { file, id } of leaks.runs) fail(`${rel(file)} holds the official run id ${id}`);

  // data/ is exactly the two data folders, byte for byte.
  const expected = new Map();
  for (const [folder, to] of [
    ["explorer-data", "data"],
    ["explorer-memos", "data/memos"],
  ]) {
    for (const file of walk(join(WEB, folder)))
      expected.set(`${to}/${file.slice(join(WEB, folder).length + 1)}`, file);
  }
  const present = new Map(all.filter((f) => f.startsWith(DATA)).map((f) => [rel(f), f]));
  for (const name of expected.keys()) if (!present.has(name)) fail(`dist-explorer/${name} is missing`);
  for (const name of present.keys())
    if (!expected.has(name)) fail(`dist-explorer/${name} is not a data file`);
  for (const [name, source] of expected) {
    const built = present.get(name);
    if (built !== undefined && !readFileSync(built).equals(readFileSync(source))) {
      fail(`dist-explorer/${name} differs from its source, ${source.slice(WEB.length)}`);
    }
  }
  // The share cards (C7): each is named by its page, each is a 1200 by 630 PNG (read from the IHDR chunk, which follows the
  // 8-byte signature: a 4-byte length, "IHDR", then the width and height as 32-bit big-endian numbers), and none is
  // left over. Their size is reported on a line of its own and is not part of the JavaScript budget.
  const CARDS = join(DIST, "cards") + "/";
  const cardFiles = all.filter((f) => f.startsWith(CARDS));
  let cardBytes = 0;
  for (const file of cardFiles) {
    const name = rel(file).slice("cards/".length);
    const bytes = readFileSync(file);
    cardBytes = cardBytes + bytes.length;
    if (name.includes("/") || extname(name) !== ".png") fail(`cards/${name} is not a PNG directly in cards/`);
    else if (!namedCards.has(name)) fail(`cards/${name} is named by no page`);
    const isPng =
      bytes.length >= 24 &&
      bytes.subarray(1, 4).toString("latin1") === "PNG" &&
      bytes.subarray(12, 16).toString("latin1") === "IHDR";
    if (!isPng) fail(`cards/${name} is not a PNG with an IHDR chunk`);
    else if (bytes.readUInt32BE(16) !== CARD_WIDTH || bytes.readUInt32BE(20) !== CARD_HEIGHT) {
      fail(
        `cards/${name} is ${bytes.readUInt32BE(16)} by ${bytes.readUInt32BE(20)}, not ${CARD_WIDTH} by ${CARD_HEIGHT}`,
      );
    }
  }
  for (const name of namedCards) {
    if (!existsSync(join(CARDS, name)))
      fail(`a page names cards/${name} as its og:image, and the file is missing`);
  }
  summary.push(`HTML files: ${htmlFiles.length}, one per path`);
  summary.push(
    `cards/: ${cardFiles.length} files, ${cardBytes} bytes (${(cardBytes / 1024).toFixed(1)} KB), ${CARD_WIDTH} by ${CARD_HEIGHT}, one per path; not in the JavaScript budget, and no budget of their own`,
  );
  summary.push(`data/: ${present.size} files, ${expected.size} expected, byte for byte`);
  summary.push(`official run ids read: ${ids.runIds.size}; looked for in every file outside data/`);
} else {
  for (const { file, copyOf } of findDataCopies(files, loadDataHashes(WEB))) {
    fail(`${rel(file)} is a byte-for-byte copy of ${copyOf.slice(WEB.length)}`);
  }
  const leaks = findLeaks(files, ids);
  for (const { file, id } of leaks.runs) fail(`${rel(file)} holds the official run id ${id}`);
  for (const { file, id } of leaks.sweeps) fail(`${rel(file)} holds the official sweep id ${id}`);
  for (const file of all)
    if (/explorer/i.test(rel(file))) fail(`${rel(file)}: a path with "explorer" in it in dist/`);
  if (existsSync(join(DIST, "cards"))) fail("dist/ has a cards/ folder: the share cards are the explorer's");
  for (const file of files) {
    if (/\bog:image\b/.test(readFileSync(file, "latin1"))) fail(`${rel(file)} mentions og:image`);
  }
  summary.push(`official run ids read: ${ids.runIds.size}; looked for in every file`);
  summary.push(`official sweep ids read: ${ids.sweepIds.size}; looked for in every file`);
}

const kb = (bytes) => `${(bytes / 1024).toFixed(1)} KB`;

// The JavaScript each path loads (explorer mode): the entry chunk and its static imports, and the path's view chunk and
// its static imports, read from Vite's manifest. Each distinct file counts once. Never a dynamic import.
const perKind = new Map(); // route kind -> { path, bytes } of its largest path
const gzipOf = new Map();
const gzipBytes = (file) => {
  if (!gzipOf.has(file)) gzipOf.set(file, gzipSync(readFileSync(join(DIST, file))).length);
  return gzipOf.get(file);
};

/** The route kind a page's path is: "/" is the story, "/scenario/s1/" a scenario, "/cases/pre-25/" a case. */
function kindOfPath(path) {
  const [first, second] = path.split("/").filter(Boolean);
  if (first === undefined) return "story";
  if (first === "cases") return second === undefined ? "cases" : "case";
  return first === "scenario" || first === "studies" || first === "memos" ? first : null;
}

function checkPathBudgets() {
  const manifestPath = join(DIST, ".vite", "manifest.json");
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  } catch {
    fail(`${rel(manifestPath)} is missing or not JSON (the explorer build writes it: build.manifest)`);
    return;
  }
  let entryKey;
  try {
    entryKey = entryKeyOf(manifest);
  } catch (error) {
    fail(error.message);
    return;
  }
  for (const [kind, source] of Object.entries(VIEW_MODULES)) {
    if (manifest[source] === undefined) fail(`the ${kind} view, ${source}, has no chunk in the manifest`);
    else if (reachedFromEntry(manifest, entryKey, source))
      fail(`the ${kind} view, ${source}, is reachable from the entry by static imports: it was not split`);
  }
  for (const file of htmlFiles) {
    const path = pathOfPage(file);
    const kind = kindOfPath(path);
    const source = kind === null ? undefined : VIEW_MODULES[kind];
    if (source === undefined || manifest[source] === undefined) {
      fail(`${path}: no view chunk to add up (route kind ${kind})`);
      continue;
    }
    const loaded = pathFiles(manifest, entryKey, source);
    const bytes = loaded.reduce((sum, name) => sum + gzipBytes(name), 0);
    if (bytes > JS_BUDGET)
      fail(`${path} loads ${bytes} bytes of JavaScript gzipped, over the ${JS_BUDGET} budget`);
    if (perKind.get(kind) === undefined || bytes > perKind.get(kind).bytes)
      perKind.set(kind, { path, bytes });
  }
}
if (explorer) checkPathBudgets();
console.log(
  `${explorer ? "dist-explorer" : "dist"}: ${all.length} files${explorer ? ` (${files.length} outside data/)` : ""}`,
);
console.log(
  explorer
    ? `JavaScript, gzipped, all chunks together: ${jsGzip} bytes (${kb(jsGzip)}); a total, not a budget`
    : `JavaScript, gzipped, in all: ${jsGzip} bytes (${kb(jsGzip)}); budget ${kb(JS_BUDGET)}`,
);
for (const [kind, { path, bytes }] of perKind) {
  console.log(
    `JavaScript a ${kind} path loads, largest ${path}: ${bytes} bytes (${kb(bytes)}); budget ${kb(JS_BUDGET)}`,
  );
}
console.log(
  `fonts: ${fonts.length} files, ${fontBytes} bytes (${kb(fontBytes)}); budget ${kb(FONT_BUDGET)}; WOFF2 only`,
);
for (const line of summary) console.log(line);

if (failures.length > 0) {
  console.error(`check-dist: ${failures.length} failure(s)`);
  for (const message of failures) console.error(`  - ${message}`);
  process.exit(1);
}
console.log("check-dist: ok");
