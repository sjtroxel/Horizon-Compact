import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { realIndex, WEB_ROOT } from "./fixtures";
import {
  AWARENESS_ANCHOR,
  PREREG_TAG,
  SELECTION_LOGS,
  THINKING_ANCHOR,
  protocolUrl,
  scenarioTextPath,
  scenarioTextUrl,
  selectionLogUrl,
} from "./links";

describe("the link to the scenario text", () => {
  it("points at the file the harness renders the prompt from, on GitHub, at the pre-registered tag", () => {
    expect(scenarioTextUrl("s1")).toBe(
      "https://github.com/sjtroxel/horizon-compact/blob/prereg-v1/experiment/company/scenarios/s1.toml",
    );
    expect(PREREG_TAG).toBe("prereg-v1");
  });

  it("names a file that exists in the repository for every scenario in the data", () => {
    // That the same paths exist at the tag was checked with `git ls-tree prereg-v1` when this was written
    // (Phase 6 IMPLEMENTATION doc section 26); a test cannot assume the tag is fetched, so this checks the tree.
    for (const scenario of realIndex.scenarios) {
      const path = resolve(WEB_ROOT, "..", scenarioTextPath(scenario.scenario_id));
      expect(existsSync(path), path).toBe(true);
    }
  });
});

describe("the links of the studies and the cases (C5)", () => {
  it("point at the protocol at the pre-registered tag, with the heading anchors of 9.5 and 9.6", () => {
    expect(protocolUrl()).toBe(
      "https://github.com/sjtroxel/horizon-compact/blob/prereg-v1/experiment/protocol/protocol-v1.md",
    );
    expect(protocolUrl(THINKING_ANCHOR)).toMatch(/#95-thinking$/);
    expect(protocolUrl(AWARENESS_ANCHOR)).toMatch(/#96-the-awareness-probe$/);
  });

  it("name the heading each anchor stands for, in the protocol on disk (GitHub's slug: lower case, dashes)", () => {
    const protocol = readFileSync(resolve(WEB_ROOT, "../experiment/protocol/protocol-v1.md"), "utf8");
    const slug = (heading: string) =>
      heading
        .toLowerCase()
        .replace(/[^a-z0-9 -]/g, "")
        .replace(/ /g, "-");
    const slugs = protocol
      .split("\n")
      .filter((line) => line.startsWith("### "))
      .map((line) => slug(line.slice(4)));
    expect(slugs).toContain(THINKING_ANCHOR);
    expect(slugs).toContain(AWARENESS_ANCHOR);
  });

  it("point at the two public selection logs, which exist in the repository", () => {
    expect(SELECTION_LOGS.map((l) => l.id)).toEqual(["preregistered", "exploratory"]);
    for (const log of SELECTION_LOGS) {
      expect(existsSync(resolve(WEB_ROOT, "..", log.path)), log.path).toBe(true);
      expect(selectionLogUrl(log.path)).toBe(
        `https://github.com/sjtroxel/horizon-compact/blob/main/${log.path}`,
      );
    }
  });
});
