// Phase 6.5 step 9 (doc §6 item 1): the video's source pack. Every explorer page printed to PDF from the local preview,
// light scheme, reduced motion, every <details> opened so the precise views are in the pack. Nothing else goes in.
// Browser plumbing copied from scratch/p65-s5-shoot.mjs.
// Usage: node scratch/p65-s9-pack.mjs <chrome> <base> <outDir>
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";

const [bin, base, outDir] = process.argv.slice(2);
mkdirSync(outDir, { recursive: true });
const chrome = spawn(bin, ["--headless=new", "--no-sandbox", "--hide-scrollbars", "--remote-debugging-port=9348", "about:blank"], {
  stdio: "ignore",
});
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) {
  try {
    targets = await (await fetch("http://127.0.0.1:9348/json")).json();
    if (targets.find((t) => t.type === "page")) break;
  } catch {}
  await sleep(200);
}
const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r));
let id = 0;
const pending = new Map();
ws.addEventListener("message", (m) => {
  const msg = JSON.parse(m.data);
  if (msg.id && pending.has(msg.id)) {
    pending.get(msg.id)(msg);
    pending.delete(msg.id);
  }
});
const send = (method, params = {}) =>
  new Promise((r) => {
    const n = ++id;
    pending.set(n, r);
    ws.send(JSON.stringify({ id: n, method, params }));
  });
const evalJs = async (e) => (await send("Runtime.evaluate", { expression: e, returnByValue: true })).result?.result?.value;
await send("Runtime.enable");
await send("Page.enable");
await send("Network.setCacheDisabled", { cacheDisabled: true });

const index = JSON.parse(readFileSync(new URL("../web/dist-explorer/data/index.json", import.meta.url), "utf8"));
const cases = JSON.parse(readFileSync(new URL(`../web/dist-explorer/data/${index.files.cases}`, import.meta.url), "utf8"));
const paths = [
  "/methods/",
  "/",
  ...index.scenarios.map((s) => `/scenario/${s.scenario_id}/`),
  "/cases/",
  ...cases.cases.map((c) => `/cases/${c.label}/`),
  "/studies/",
  "/memos/",
];
const slug = (p) => (p === "/" ? "story" : p.replace(/^\/|\/$/g, "").replace(/\//g, "-"));

await send("Emulation.setEmulatedMedia", {
  media: "screen",
  features: [
    { name: "prefers-color-scheme", value: "light" },
    { name: "prefers-reduced-motion", value: "reduce" },
  ],
});
const manifest = [];
let n = 0;
for (const p of paths) {
  n++;
  await send("Page.navigate", { url: base + p });
  // Wait for the page's data to load: the main element has text and no loading marker for a moment.
  let last = "";
  for (let i = 0; i < 60; i++) {
    await sleep(250);
    const t = await evalJs("document.querySelector('main')?.innerText ?? ''");
    if (t.length > 200 && t === last) break;
    last = t;
  }
  await evalJs("document.querySelectorAll('details').forEach(d => d.open = true)");
  await sleep(500);
  const title = await evalJs("document.title");
  const res = await send("Page.printToPDF", {
    printBackground: true,
    preferCSSPageSize: false,
    paperWidth: 8.5,
    paperHeight: 11,
    marginTop: 0.4,
    marginBottom: 0.4,
    marginLeft: 0.4,
    marginRight: 0.4,
  });
  const buf = Buffer.from(res.result.data, "base64");
  const name = `${String(n).padStart(2, "0")}-${slug(p)}.pdf`;
  writeFileSync(`${outDir}/${name}`, buf);
  manifest.push({ file: name, path: p, title, bytes: buf.length, sha256: createHash("sha256").update(buf).digest("hex") });
  console.log(name, p, buf.length, title);
}
writeFileSync(`${outDir}/manifest.json`, JSON.stringify(manifest, null, 2) + "\n");
ws.close();
chrome.kill();
