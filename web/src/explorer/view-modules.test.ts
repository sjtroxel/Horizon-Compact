import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { WEB_ROOT } from "./fixtures";
import { allRoutes } from "./page-meta.mjs";
import { VIEW_MODULES } from "./view-modules.mjs";

describe("view-modules.mjs and views.tsx say the same", () => {
  const source = readFileSync(resolve(WEB_ROOT, "src/explorer/views.tsx"), "utf8");
  const imported = [...source.matchAll(/\bimport\(\s*["']\.\/([^"']+)["']\s*\)/g)].map((m) => m[1]!);

  it("lazy-loads exactly the files the map names, no more and no fewer", () => {
    const mapped = new Set(Object.values(VIEW_MODULES).map((path) => path.replace(/^src\/explorer\//, "")));
    expect(imported.length).toBeGreaterThan(0);
    // The specifiers have no extension; the map's paths do.
    expect(new Set(imported.map((s) => s.replace(/\.tsx?$/, "")))).toEqual(
      new Set([...mapped].map((p) => p.replace(/\.tsx?$/, ""))),
    );
  });

  it("holds an existing source file for every route kind a page is written for, and none for not_found", () => {
    const kinds = new Set(allRoutes(["s1"], ["pre-25"]).map((route) => route.kind));
    expect(Object.keys(VIEW_MODULES).sort()).toEqual([...kinds].sort());
    for (const path of Object.values(VIEW_MODULES)) {
      expect(() => readFileSync(resolve(WEB_ROOT, path), "utf8"), path).not.toThrow();
    }
  });

  it("imports no view statically from views.tsx (a static import would put the view in the entry chunk)", () => {
    for (const path of Object.values(VIEW_MODULES)) {
      const name = path.replace(/^src\/explorer\//, "").replace(/\.tsx$/, "");
      expect(source, name).not.toMatch(new RegExp(`from\\s*["']\\./${name}["']`));
    }
  });
});
