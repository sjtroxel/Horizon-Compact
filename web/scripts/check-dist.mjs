// Checks the built files in dist/ (Phase 1.5 IMPLEMENTATION doc sections 8 and 9): the asset budget, and that
// nothing in the build asks for another host, runs inline or styles inline. Run after `vite build`; prints the
// measured sizes and exits 1 on the first group of failures.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join } from "node:path";
import { gzipSync } from "node:zlib";

const DIST = new URL("../dist/", import.meta.url).pathname;
const JS_BUDGET = 100 * 1024; // gzipped, all JavaScript
const FONT_BUDGET = 150 * 1024; // all font files
const failures = [];
const fail = (message) => failures.push(message);

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}

const files = walk(DIST);
const rel = (path) => path.slice(DIST.length);

// JavaScript, gzipped, in all.
const js = files.filter((f) => extname(f) === ".js");
const jsGzip = js.reduce((sum, f) => sum + gzipSync(readFileSync(f)).length, 0);
if (jsGzip > JS_BUDGET) fail(`JavaScript is ${jsGzip} bytes gzipped, over the ${JS_BUDGET} budget`);

// Fonts: .woff2 only, under budget.
const fontExtensions = new Set([".woff", ".woff2", ".ttf", ".otf", ".eot"]);
const fonts = files.filter((f) => fontExtensions.has(extname(f)));
for (const f of fonts) if (extname(f) !== ".woff2") fail(`font file that is not WOFF2: ${rel(f)}`);
const fontBytes = fonts.reduce((sum, f) => sum + statSync(f).size, 0);
if (fontBytes > FONT_BUDGET) fail(`fonts are ${fontBytes} bytes, over the ${FONT_BUDGET} budget`);

// index.html: no inline script, no style element, no style attribute, nothing that points at a host.
const html = readFileSync(join(DIST, "index.html"), "utf8");
for (const tag of html.match(/<script\b[^>]*>/gi) ?? []) {
  if (!/\bsrc=/.test(tag)) fail(`inline <script> in index.html: ${tag}`);
}
if (/<style\b/i.test(html)) fail("<style> element in index.html");
if (/\sstyle\s*=/i.test(html)) fail("style attribute in index.html");
if (/<script\b[^>]*>[^<]+<\/script>/i.test(html)) fail("script with a body in index.html");

const isHost = (value) => /^(?:[a-z][a-z0-9+.-]*:)?\/\//i.test(value) || /^[a-z][a-z0-9+.-]*:/i.test(value);
for (const match of html.matchAll(/\b(src|href)\s*=\s*"([^"]*)"/gi)) {
  const [, attribute, value] = match;
  const allowed = value === "/favicon.svg" || (value.startsWith("/assets/") && !isHost(value));
  if (!allowed) fail(`index.html ${attribute}="${value}" is not the favicon or a built asset`);
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

const kb = (bytes) => `${(bytes / 1024).toFixed(1)} KB`;
console.log(`dist: ${files.length} files`);
console.log(`JavaScript, gzipped, in all: ${jsGzip} bytes (${kb(jsGzip)}); budget ${kb(JS_BUDGET)}`);
console.log(
  `fonts: ${fonts.length} files, ${fontBytes} bytes (${kb(fontBytes)}); budget ${kb(FONT_BUDGET)}; WOFF2 only`,
);

if (failures.length > 0) {
  console.error(`check-dist: ${failures.length} failure(s)`);
  for (const message of failures) console.error(`  - ${message}`);
  process.exit(1);
}
console.log("check-dist: ok");
