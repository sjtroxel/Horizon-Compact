import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { realIndex, WEB_ROOT } from "./fixtures";
import { PREREG_TAG, scenarioTextPath, scenarioTextUrl } from "./links";

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
