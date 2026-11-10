// Test helpers only (nothing in the bundle imports this file): the real committed data, served to the loaders as if
// by the site's own origin.
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createDataApi } from "./data";
import type { CasesIndex, DataApi, DataIndex, GridFile } from "./data";

// `import.meta.url` is not a file: URL under the jsdom environment, so the folder comes from `dirname`.
export const WEB_ROOT = `${resolve(import.meta.dirname, "../..")}/`;

export function readData<T>(relative: string): T {
  return JSON.parse(readFileSync(`${WEB_ROOT}explorer-data/${relative}`, "utf8")) as T;
}

export const realIndex = readData<DataIndex>("index.json");
export const realCasesIndex = readData<CasesIndex>("cases/index.json");

/** A fetch function that answers `/data/...` from the committed files, and 404 for anything else. */
export function fileFetcher(requested: string[] = []): (path: string) => Promise<Response> {
  return async (path) => {
    requested.push(path);
    const file = path.startsWith("/data/memos/")
      ? `${WEB_ROOT}explorer-memos/${path.slice("/data/memos/".length)}`
      : path.startsWith("/data/")
        ? `${WEB_ROOT}explorer-data/${path.slice("/data/".length)}`
        : null;
    if (file === null || !existsSync(file)) return { ok: false, status: 404 } as Response;
    const text = readFileSync(file, "utf8");
    return { ok: true, status: 200, json: async () => JSON.parse(text) as unknown } as Response;
  };
}

/** The loaders over the real files. */
export function realApi(requested: string[] = []): DataApi {
  return createDataApi(fileFetcher(requested));
}

/** Every grid file and every thinking sub-study file the real index lists, as the builder wrote them. */
export function allGridFiles(): Array<{ label: string; file: GridFile }> {
  const found: Array<{ label: string; file: GridFile }> = [];
  for (const [kind, block] of [
    ["grid", realIndex.files.grid],
    ["thinking", realIndex.files.thinking],
  ] as const) {
    for (const [model, byScenario] of Object.entries(block)) {
      for (const [scenario, relative] of Object.entries(byScenario)) {
        found.push({ label: `${kind} ${model} ${scenario}`, file: readData<GridFile>(relative) });
      }
    }
  }
  return found;
}

export const realGrids = allGridFiles();
