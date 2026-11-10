import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { WEB_ROOT } from "./fixtures";

/**
 * The palette test (Phase 6 IMPLEMENTATION doc section 24.1, not built in C3): explorer.css holds his pick, palette A
 * (amber and blue), and the lead's wash (section 24.2), and E's gray is checked against the four.
 */
const css = readFileSync(resolve(WEB_ROOT, "src/explorer/explorer.css"), "utf8");
const siteCss = readFileSync(resolve(WEB_ROOT, "src/styles.css"), "utf8");

/** The declarations of the first `:root` block after `from` (an index into `source`). */
function rootBlock(source: string, from: number): Record<string, string> {
  const open = source.indexOf(":root {", from);
  const close = source.indexOf("}", open);
  const found: Record<string, string> = {};
  for (const match of source.slice(open, close).matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)) {
    found[match[1]!] = match[2]!.trim();
  }
  return found;
}
const light = (source: string) => rootBlock(source, 0);
const dark = (source: string) => rootBlock(source, source.indexOf("prefers-color-scheme: dark"));

// Section 24.1's table (palette A) and section 24.2's wash.
const A = {
  light: {
    "--o-a": "#daa668",
    "--o-b": "#5fa1f3",
    "--o-c": "#81520a",
    "--o-d": "#07519d",
    "--leadwash": "#f7e6b5",
  },
  dark: {
    "--o-a": "#b68446",
    "--o-b": "#4f91e2",
    "--o-c": "#84550f",
    "--o-d": "#1d60ad",
    "--leadwash": "#3a301a",
  },
};

// OKLab, as the dataviz skill's validator (scripts/validate_palette.js) computes it: Delta E is the Euclidean distance
// in OKLab times 100, unsimulated vision. The validator's normal-vision floor is 15 ("a worst unsimulated pair below
// 15 FAILs the run", NORMAL_FLOOR in that script).
const NORMAL_FLOOR = 15;
function linear(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const c = v / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
}
function oklab(hex: string): [number, number, number] {
  const [r, g, b] = linear(hex);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}
function deltaE(a: string, b: string): number {
  const [x, y] = [oklab(a), oklab(b)];
  return 100 * Math.hypot(x[0] - y[0], x[1] - y[1], x[2] - y[2]);
}

describe("palette A and the lead's wash", () => {
  it("are in explorer.css exactly as sections 24.1 and 24.2 record them, in light", () => {
    const found = light(css);
    for (const [name, value] of Object.entries(A.light)) expect(found[name], name).toBe(value);
  });

  it("are in explorer.css exactly as sections 24.1 and 24.2 record them, in dark", () => {
    const found = dark(css);
    for (const [name, value] of Object.entries(A.dark)) expect(found[name], name).toBe(value);
  });

  it("keep E as the site's muted gray, in both modes", () => {
    expect(light(css)["--o-e"]).toBe("var(--muted)");
    expect(light(siteCss)["--muted"]).toBe("#8a8270");
    expect(dark(siteCss)["--muted"]).toBe("#7d8696");
  });
});

/**
 * FINDING (C4, reported in section 26): E's gray is NOT distinct from every one of the four by the validator's
 * normal-vision floor of 15. Section 24.1 says E "is outside the validated four by design" and that a test was to
 * check it "against each". This is that test. It pins what was measured, pair by pair, and fails if the palette
 * changes so that the list below is no longer true, without pretending the shortfall is not there. His pick stands;
 * what to do about it is his and Opus's call. Colors are never the only carrier of a goal (every row and panel names
 * its goal in text), which is what the skill requires where a pair is close.
 */
describe("E's gray against the four series colors, by the validator's normal-vision floor", () => {
  const BELOW_FLOOR = {
    light: ["C"],
    dark: ["A", "B"],
  } as const;
  for (const [mode, read] of [
    ["light", light],
    ["dark", dark],
  ] as const) {
    it(`measures E against A, B, C and D in ${mode}, and lists the pairs under ${NORMAL_FLOOR}`, () => {
      const muted = read(siteCss)["--muted"]!;
      const under: string[] = [];
      for (const id of ["A", "B", "C", "D"]) {
        const color = read(css)[`--o-${id.toLowerCase()}`]!;
        if (deltaE(color, muted) < NORMAL_FLOOR) under.push(id);
      }
      expect(under).toEqual(BELOW_FLOOR[mode]);
    });
  }

  it("pins the measured distances", () => {
    const distance = (mode: "light" | "dark", id: string) =>
      deltaE(
        (mode === "light" ? light(css) : dark(css))[`--o-${id.toLowerCase()}`]!,
        (mode === "light" ? light(siteCss) : dark(siteCss))["--muted"]!,
      );
    expect(distance("light", "A")).toBeCloseTo(16.87, 1);
    expect(distance("light", "B")).toBeCloseTo(19.03, 1);
    expect(distance("light", "C")).toBeCloseTo(14.79, 1);
    expect(distance("light", "D")).toBeCloseTo(23.75, 1);
    expect(distance("dark", "A")).toBeCloseTo(13.01, 1);
    expect(distance("dark", "B")).toBeCloseTo(11.77, 1);
    expect(distance("dark", "C")).toBeCloseTo(17.93, 1);
    expect(distance("dark", "D")).toBeCloseTo(17.07, 1);
  });
});
