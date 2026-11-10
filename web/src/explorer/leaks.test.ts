import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { findDataCopies, findLeaks, loadDataHashes, loadOfficialIds, walk } from "../../scripts/leaks.mjs";
import { WEB_ROOT } from "./fixtures";

const scratch: string[] = [];
function folder(): string {
  const dir = mkdtempSync(join(tmpdir(), "hc-leaks-"));
  scratch.push(dir);
  return dir;
}
afterEach(() => {
  for (const dir of scratch.splice(0)) rmSync(dir, { recursive: true, force: true });
});

describe("the placeholder-mode checks (negative control)", () => {
  const ids = { runIds: new Set(["r-0123456789ab"]), sweepIds: new Set(["grid-planted-sweep-00000000"]) };

  it("reports one planted run id and one planted sweep id, in the files they were planted in", () => {
    const dir = folder();
    mkdirSync(join(dir, "assets"));
    writeFileSync(join(dir, "assets", "index.js"), 'const x = "a r-0123456789ab b";');
    writeFileSync(join(dir, "index.html"), "<p>grid-planted-sweep-00000000</p>");
    writeFileSync(join(dir, "clean.css"), "body { color: red }");

    const leaks = findLeaks(walk(dir), ids);
    expect(leaks.runs).toEqual([{ file: join(dir, "assets", "index.js"), id: "r-0123456789ab" }]);
    expect(leaks.sweeps).toEqual([{ file: join(dir, "index.html"), id: "grid-planted-sweep-00000000" }]);
  });

  it("reports nothing for a folder with neither id", () => {
    const dir = folder();
    writeFileSync(join(dir, "index.html"), "<p>nothing official here</p>");
    expect(findLeaks(walk(dir), ids)).toEqual({ runs: [], sweeps: [] });
  });

  it("finds an id inside a binary file", () => {
    const dir = folder();
    writeFileSync(
      join(dir, "font.woff2"),
      Buffer.concat([Buffer.from([0, 255, 1]), Buffer.from("r-0123456789ab")]),
    );
    expect(findLeaks(walk(dir), ids).runs).toHaveLength(1);
  });

  it("reports a byte-for-byte copy of a data file, and only a copy", () => {
    const dir = folder();
    copyFileSync(join(WEB_ROOT, "explorer-data", "index.json"), join(dir, "renamed.json"));
    writeFileSync(join(dir, "other.json"), "{}");
    const copies = findDataCopies(walk(dir), loadDataHashes(WEB_ROOT));
    expect(copies.map((c) => c.file)).toEqual([join(dir, "renamed.json")]);
    expect(copies[0]!.copyOf.endsWith("explorer-data/index.json")).toBe(true);
  });

  it("reads the real ids: 2,290 run ids and 13 sweep ids", () => {
    const real = loadOfficialIds(WEB_ROOT);
    expect(real.runIds.size).toBe(2290);
    expect(real.sweepIds.size).toBe(13);
  });
});
