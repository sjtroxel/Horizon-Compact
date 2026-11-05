import { describe, expect, it } from "vitest";
import raw from "./data/placeholder.json";
import { AXIS_MAX, STATUSES, TICKS, data, money, parseSiteData, percent } from "./data";

function changed(path: string[], value: unknown): unknown {
  const copy = structuredClone(raw) as Record<string, unknown>;
  let node: Record<string, unknown> = copy;
  for (const key of path.slice(0, -1)) node = node[key] as Record<string, unknown>;
  node[path[path.length - 1]!] = value;
  return copy;
}

describe("the data check", () => {
  it("accepts the committed placeholder file", () => {
    expect(parseSiteData(raw).sweep.role).toBe("development");
    expect(data.runs).toHaveLength(15);
  });

  it.each([
    ["schema", ["schema"], "horizon-compact/results"],
    ["schema_version", ["schema_version"], 2],
    ["kind", ["kind"], "result"],
    ["content", ["content"], "official"],
    ["sweep.role", ["sweep", "role"], "official"],
    ["sweep.experiment", ["sweep", "experiment"], "company"],
  ])("throws on a wrong %s", (_name, path, value) => {
    expect(() => parseSiteData(changed(path, value))).toThrow(/site data/);
  });

  it("throws on a shape the page could not draw", () => {
    expect(() => parseSiteData(null)).toThrow();
    expect(() => parseSiteData(changed(["runs"], []))).toThrow(/runs/);
    expect(() => parseSiteData(changed(["cells"], []))).toThrow(/cells/);
  });
});

describe("the display helpers", () => {
  it("writes money in whole dollars with a thousands separator", () => {
    expect(money(0)).toBe("$0");
    expect(money(1000)).toBe("$1,000");
    expect(money(933.3333)).toBe("$933");
  });

  it("puts $0 at the left edge and the largest cap at the right on one shared axis", () => {
    expect(AXIS_MAX).toBe(1000);
    expect(TICKS).toEqual([0, 250, 500, 750, 1000]);
    expect(percent(0)).toBe("0.000%");
    expect(percent(1000)).toBe("100.000%");
  });

  it("lists the twelve statuses, valid first", () => {
    expect(STATUSES).toHaveLength(12);
    expect(STATUSES[0]).toBe("valid");
  });
});
