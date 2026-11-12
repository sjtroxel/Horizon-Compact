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

// ---------------------------------------------------------------------------------------------------------------------
// The bands (step 11, the Phase 6 IMPLEMENTATION doc section 31): the header's dark band and the title's light band.

/** WCAG 2.x contrast ratio of two hex colors. */
function relativeLuminance(hex: string): number {
  const [r, g, b] = linear(hex);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
export function contrast(a: string, b: string): number {
  const [x, y] = [relativeLuminance(a), relativeLuminance(b)].sort((p, q) => q - p);
  return (x! + 0.05) / (y! + 0.05);
}

const BANDS = {
  light: {
    "--band": "#17202f",
    "--band-ink": "#f6f2e9",
    "--band-ink2": "#d3cdbd",
    "--band-mark": "#f0cf8f",
    "--band-line": "#7b8498",
    "--titleband": "#ece5d2",
  },
  dark: {
    "--band": "#1b2536",
    "--band-ink": "#eee8da",
    "--band-ink2": "#c6bfae",
    "--band-mark": "#e9c98f",
    "--band-line": "#7b8aa3",
    "--titleband": "#141c2a",
  },
} as const;

describe("the header band and the title band", () => {
  it("are in explorer.css exactly as section 31 records them, in both modes", () => {
    for (const [name, value] of Object.entries(BANDS.light)) expect(light(css)[name], name).toBe(value);
    for (const [name, value] of Object.entries(BANDS.dark)) expect(dark(css)[name], name).toBe(value);
  });

  it("leave the surface, the ink and palette A where they were", () => {
    expect(light(siteCss)["--surface"]).toBe("#f6f2e9");
    expect(light(siteCss)["--ink"]).toBe("#141a26");
    expect(dark(siteCss)["--surface"]).toBe("#0f1520");
    expect(dark(siteCss)["--ink"]).toBe("#eee8da");
  });

  /** Each color a person reads or must see, on the band it sits on: WCAG AA is 4.5 for text and 3 for a focus ring, the
   * current-page mark and a control's outline. */
  const pairs = (mode: "light" | "dark") => {
    const own = mode === "light" ? light(css) : dark(css);
    const site = mode === "light" ? light(siteCss) : dark(siteCss);
    const band = own["--band"]!;
    const title = own["--titleband"]!;
    return [
      // The header band: the name and the model switch's label and unpressed buttons, the navigation links, the pressed button.
      ["name, switch label and buttons (band-ink) on the band", own["--band-ink"]!, band, 4.5],
      ["navigation links (band-ink2) on the band", own["--band-ink2"]!, band, 4.5],
      ["pressed switch button: the band's color on band-ink", band, own["--band-ink"]!, 4.5],
      ["focus ring on the band (band-mark)", own["--band-mark"]!, band, 3],
      ["current-page mark on the band (band-mark)", own["--band-mark"]!, band, 3],
      ["switch button outline (band-line) on the band", own["--band-line"]!, band, 3],
      // The title band: the title, the line under it, the jump menu, and the title's focus ring.
      ["title (ink) on the title band", site["--ink"]!, title, 4.5],
      ["line under the title (ink2) on the title band", site["--ink2"]!, title, 4.5],
      ["jump-menu hover (accent) on the title band", site["--accent"]!, title, 4.5],
      ["title focus ring (series) on the title band", site["--series"]!, title, 3],
      // Body text that must stay readable on the surface: the quiet exploratory note and every secondary line.
      ["secondary text (ink2) on the surface", site["--ink2"]!, site["--surface"]!, 4.5],
      ["lead sentence (ink) on the wash", site["--ink"]!, own["--leadwash"]!, 4.5],
    ] as const;
  };

  for (const mode of ["light", "dark"] as const) {
    it(`meets WCAG AA for every text and focus color on each band, in ${mode}`, () => {
      for (const [what, foreground, background, minimum] of pairs(mode)) {
        const ratio = contrast(foreground, background);
        expect(ratio, `${mode}: ${what}: ${ratio.toFixed(2)}`).toBeGreaterThanOrEqual(minimum);
      }
    });
  }

  it("can see a contrast fail: the same computation rejects a pair known to be too close", () => {
    expect(contrast("#8a8270", "#f6f2e9")).toBeLessThan(4.5); // the site's muted gray on the surface
    expect(contrast("#ffffff", "#000000")).toBeCloseTo(21, 5);
  });
});

// ---------------------------------------------------------------------------------------------------------------------
// The type rule (step 11): Source Sans 3 throughout, one scale, nothing a reader must understand under 15 px.

describe("the explorer's type", () => {
  // The rules, without the comments that explain them (a comment may name the thing a rule forbids).
  const code = css.replace(/\/\*[\s\S]*?\*\//g, "");
  const px = (rem: string) => Number.parseFloat(rem) * 16;
  const tokens = light(css);

  it("sets every word in Source Sans 3: the explorer's root names the sans face and nothing in explorer.css uses the serif", () => {
    expect(code).not.toMatch(/var\(--serif\)/);
    expect(code).not.toMatch(/newsreader/i);
    expect(code).toMatch(/\.explorer\s*\{[^}]*font-family:\s*var\(--sans\)/);
    expect(code).not.toMatch(/font-family:\s*"?(Newsreader|Georgia|serif)/i);
  });

  it("has one scale: the page title, section title, finding sentence, body, chart title, chart labels, note line and axis words", () => {
    for (const name of [
      "--x-title",
      "--x-section",
      "--x-finding",
      "--x-body",
      "--x-chart-title",
      "--x-label",
      "--x-note",
      "--x-axis",
    ]) {
      expect(tokens[name], name).toBeTruthy();
    }
    // Body 17 to 18 px; nothing a reader must understand is under 15 px; only the note line and the axis words are 13 to 14.
    expect(px(tokens["--x-body"]!)).toBeGreaterThanOrEqual(17);
    expect(px(tokens["--x-body"]!)).toBeLessThanOrEqual(18);
    for (const name of ["--x-section", "--x-finding", "--x-chart-title", "--x-label"]) {
      expect(px(tokens[name]!), name).toBeGreaterThanOrEqual(15);
    }
    expect(px(tokens["--x-note"]!)).toBeGreaterThanOrEqual(13);
    expect(px(tokens["--x-note"]!)).toBeLessThanOrEqual(14);
    expect(px(tokens["--x-axis"]!)).toBeGreaterThanOrEqual(13);
    expect(px(tokens["--x-axis"]!)).toBeLessThanOrEqual(14);
  });

  /** Every `font-size` declaration, with the selector of its rule. */
  const sizes = [...code.matchAll(/font-size:\s*([^;]+);/g)].map((match) => {
    const open = code.lastIndexOf("{", match.index);
    const before = Math.max(code.lastIndexOf("}", open), code.lastIndexOf("{", open - 1));
    return {
      selector: code
        .slice(before + 1, open)
        .trim()
        .replace(/\s+/g, " "),
      value: match[1]!.trim(),
    };
  });

  it("sizes every explorer text from the scale: no literal size under 15 px outside the id and hash mono text", () => {
    expect(sizes.length).toBeGreaterThan(40);
    for (const { selector, value } of sizes) {
      if (value.startsWith("var(--x-") || value === "inherit") continue;
      if (/^(\.memo-meta \.mono|\.mono)\b/.test(selector)) continue; // an id or a hash, in the mono face
      const rem = /^([\d.]+)rem$/.exec(value);
      expect(rem !== null && px(value) >= 15, `${selector} { font-size: ${value} }`).toBe(true);
    }
  });

  it("uses the 13 to 14 px sizes only for a note line, a table's note line and the axes", () => {
    const allowed =
      /(figcaption|\.table-note|\.axis-|\.tick|\.lever-axis|\.axis-ends|\.lever-axis|text\.|\.view \.axis-caption)/;
    for (const { selector, value } of sizes) {
      if (value === "var(--x-note)" || value === "var(--x-axis)") {
        expect(allowed.test(selector), `${selector} { font-size: ${value} }`).toBe(true);
      }
    }
  });

  it("keeps the explanations at body size: the chart keys, the exploratory label and a note are not set as notes", () => {
    const sizeOf = (selector: string) => sizes.find((s) => s.selector === selector)?.value;
    expect(sizeOf(".chart-key")).toBe("var(--x-body)");
    expect(sizeOf(".view .exploratory-label")).toBe("var(--x-body)");
    expect(sizeOf(".about-body p")).toBeUndefined(); // it inherits the body size
    expect(sizeOf(".x-note")).toBe("var(--x-label)");
  });
});
