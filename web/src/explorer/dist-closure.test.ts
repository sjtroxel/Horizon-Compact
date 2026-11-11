import { describe, expect, it } from "vitest";
import { entryKeyOf, pathFiles, reachedFromEntry, staticClosure } from "../../scripts/dist-closure.mjs";
import type { Manifest } from "../../scripts/dist-closure.mjs";

// A small manifest in Vite's shape. The entry imports the shared chunk `_react`; two views each import `_charts`
// (shared between them) and the second also imports `_only-b`; the entry reaches a third view only dynamically.
const manifest: Manifest = {
  "explorer.html": {
    file: "assets/entry.js",
    isEntry: true,
    imports: ["_react"],
    dynamicImports: ["src/A.tsx", "src/B.tsx", "src/C.tsx"],
  },
  _react: { file: "assets/react.js" },
  _charts: { file: "assets/charts.js", imports: ["_react"] },
  "_only-b": { file: "assets/only-b.js" },
  "src/A.tsx": { file: "assets/a.js", isDynamicEntry: true, imports: ["_charts"] },
  "src/B.tsx": { file: "assets/b.js", isDynamicEntry: true, imports: ["_charts", "_only-b"] },
  // C is imported statically by the entry's chunk `_react` below in the "not split" case; here it is dynamic only.
  "src/C.tsx": { file: "assets/c.js", isDynamicEntry: true, dynamicImports: ["src/A.tsx"] },
};

describe("dist-closure: the JavaScript one path loads", () => {
  it("is the entry's chunk and its static imports plus the view's chunk and its static imports", () => {
    expect(pathFiles(manifest, "explorer.html", "src/A.tsx")).toEqual([
      "assets/a.js",
      "assets/charts.js",
      "assets/entry.js",
      "assets/react.js",
    ]);
    expect(pathFiles(manifest, "explorer.html", "src/B.tsx")).toEqual([
      "assets/b.js",
      "assets/charts.js",
      "assets/entry.js",
      "assets/only-b.js",
      "assets/react.js",
    ]);
  });

  it("counts a chunk two routes share once, and a chunk the entry and the view both import once", () => {
    const files = pathFiles(manifest, "explorer.html", "src/A.tsx");
    expect(files.filter((file) => file === "assets/react.js")).toHaveLength(1); // the entry's and _charts' import
    expect(new Set(files).size).toBe(files.length);
  });

  it("does not follow a dynamic import: a view's other views are not loaded with it", () => {
    // C imports A dynamically only, and the entry names A, B and C as dynamic imports: none comes with the entry.
    expect(pathFiles(manifest, "explorer.html", "src/C.tsx")).toEqual([
      "assets/c.js",
      "assets/entry.js",
      "assets/react.js",
    ]);
    expect(staticClosure(manifest, ["explorer.html"])).toEqual(new Set(["explorer.html", "_react"]));
  });

  it("walks a cycle once and finishes", () => {
    const cyclic: Manifest = {
      entry: { file: "e.js", isEntry: true, imports: ["x"] },
      x: { file: "x.js", imports: ["y"] },
      y: { file: "y.js", imports: ["x", "entry"] },
    };
    expect(staticClosure(cyclic, ["entry"])).toEqual(new Set(["entry", "x", "y"]));
    expect(pathFiles(cyclic, "entry", "y")).toEqual(["e.js", "x.js", "y.js"]);
  });

  it("fails on a key the manifest does not have, whether it is a view or an import", () => {
    expect(() => pathFiles(manifest, "explorer.html", "src/Missing.tsx")).toThrow(
      /no entry for "src\/Missing.tsx"/,
    );
    const broken: Manifest = { entry: { file: "e.js", isEntry: true, imports: ["gone"] } };
    expect(() => staticClosure(broken, ["entry"])).toThrow(/no entry for "gone"/);
  });

  it("drops a file that is not JavaScript (a chunk entry is the .js file; stylesheets are listed apart)", () => {
    const withCss: Manifest = {
      entry: { file: "e.js", isEntry: true, imports: ["style"] },
      style: { file: "assets/style.css" },
      view: { file: "v.js", isDynamicEntry: true },
    };
    expect(pathFiles(withCss, "entry", "view")).toEqual(["e.js", "v.js"]);
  });

  it("says whether the entry reaches a module by static imports (a view that was not split)", () => {
    expect(reachedFromEntry(manifest, "explorer.html", "src/A.tsx")).toBe(false);
    const notSplit: Manifest = {
      ...manifest,
      "explorer.html": { ...manifest["explorer.html"]!, imports: ["_react", "src/A.tsx"] },
    };
    expect(reachedFromEntry(notSplit, "explorer.html", "src/A.tsx")).toBe(true);
    // Transitively, too: the entry imports a shared chunk that imports the view.
    const throughShared: Manifest = {
      ...manifest,
      _react: { file: "assets/react.js", imports: ["src/B.tsx"] },
    };
    expect(reachedFromEntry(throughShared, "explorer.html", "src/B.tsx")).toBe(true);
  });

  it("finds the one entry, and refuses a manifest with none or two", () => {
    expect(entryKeyOf(manifest)).toBe("explorer.html");
    expect(() => entryKeyOf({ a: { file: "a.js" } })).toThrow(/0 entries/);
    expect(() =>
      entryKeyOf({ a: { file: "a.js", isEntry: true }, b: { file: "b.js", isEntry: true } }),
    ).toThrow(/2 entries/);
  });
});
