import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { WEB_ROOT } from "./fixtures";

// The module-graph test (Phase 6 IMPLEMENTATION doc section 6, C3 decision 10): a static walk of what each entry
// imports. The placeholder entry must not reach the explorer in any way Rollup could follow, because a dynamic
// import or a mode branch would still put the explorer's chunk into dist/.

const SRC = join(WEB_ROOT, "src");
const EXTENSIONS = ["", ".ts", ".tsx", ".js", ".mjs", ".mts", ".json", ".css"];

/** Every module specifier a file names: static imports, re-exports, side-effect imports and `import("...")`. */
function specifiers(source: string): string[] {
  const found: string[] = [];
  const patterns = [
    /\bfrom\s*["']([^"']+)["']/g, // import x from "y", export * from "y"
    /\bimport\s*["']([^"']+)["']/g, // import "y"
    /\bimport\s*\(\s*["']([^"']+)["']\s*\)/g, // import("y")
    /\brequire\s*\(\s*["']([^"']+)["']\s*\)/g,
  ];
  for (const pattern of patterns) for (const match of source.matchAll(pattern)) found.push(match[1]!);
  return found;
}

function resolveRelative(from: string, specifier: string): string | null {
  const base = resolve(dirname(from), specifier);
  const candidates = [
    ...EXTENSIONS.map((ext) => `${base}${ext}`),
    ...EXTENSIONS.slice(1, 3).map((ext) => join(base, `index${ext}`)),
  ];
  return candidates.find((p) => existsSync(p) && statSync(p).isFile()) ?? null;
}

/** Everything reachable from `entry` through relative specifiers; bare package names are ignored. */
function reachable(entry: string): { files: Set<string>; unresolved: string[] } {
  const files = new Set<string>();
  const unresolved: string[] = [];
  const queue = [entry];
  while (queue.length > 0) {
    const file = queue.pop()!;
    if (files.has(file)) continue;
    files.add(file);
    if (/\.(css|json)$/.test(file)) continue; // not code that imports further
    for (const specifier of specifiers(readFileSync(file, "utf8"))) {
      if (!specifier.startsWith(".")) continue;
      const target = resolveRelative(file, specifier);
      if (target === null) unresolved.push(`${relative(WEB_ROOT, file)} -> ${specifier}`);
      else queue.push(target);
    }
  }
  return { files, unresolved };
}

const names = (files: Set<string>) => [...files].map((f) => relative(WEB_ROOT, f));

describe("the module graph", () => {
  const placeholder = reachable(join(SRC, "main.tsx"));
  const explorer = reachable(join(SRC, "explorer", "main.tsx"));

  it("walks the placeholder entry (a sanity check that the walk finds things)", () => {
    expect(placeholder.unresolved).toEqual([]);
    const found = names(placeholder.files);
    expect(found).toContain("src/App.tsx");
    expect(found).toContain("src/copy.ts");
    expect(found).toContain("src/data/placeholder.json");
  });

  it("reaches no explorer file, no explorer data and no explorer stylesheet from the placeholder entry", () => {
    for (const file of names(placeholder.files)) {
      expect(file, file).not.toMatch(/(^|\/)explorer(\/|[-.])/); // src/explorer/..., explorer.css, explorer-data, explorer-memos
    }
    expect(names(placeholder.files).filter((f) => f.startsWith("src/explorer/"))).toEqual([]);
  });

  it("has no dynamic import and no mode branch in anything the placeholder entry reaches", () => {
    for (const file of placeholder.files) {
      if (/\.(css|json)$/.test(file)) continue;
      const source = readFileSync(file, "utf8");
      expect(source, relative(WEB_ROOT, file)).not.toMatch(/\bimport\s*\(/);
      expect(source, relative(WEB_ROOT, file)).not.toContain("import.meta.env");
      expect(source, relative(WEB_ROOT, file)).not.toMatch(/explorer/i);
    }
  });

  it("walks the explorer entry and reaches its loaders", () => {
    expect(explorer.unresolved).toEqual([]);
    const found = names(explorer.files);
    expect(found).toContain("src/explorer/data.ts");
    expect(found).toContain("src/explorer/Shell.tsx");
    expect(found).toContain("src/explorer/explorer.css");
    expect(found).toContain("src/styles.css");
  });

  it("keeps the placeholder's run data out of the explorer's bundle", () => {
    const found = names(explorer.files);
    expect(found).not.toContain("src/data.ts");
    expect(found).not.toContain("src/data/placeholder.json");
  });

  it("reaches no share-card code from the explorer entry: the cards are drawn by the build, never by a page (C7)", () => {
    for (const file of names(explorer.files)) {
      expect(file, file).not.toMatch(/(^|\/)(cards|card-render|write-cards|load-ts)\.m?[tj]s$/);
      expect(file, file).not.toMatch(/fonts-ttf/);
    }
  });

  it("imports no data file into the explorer: the data is fetched, never bundled", () => {
    for (const file of names(explorer.files)) {
      expect(file, file).not.toMatch(/explorer-(data|memos)/);
    }
  });
});
