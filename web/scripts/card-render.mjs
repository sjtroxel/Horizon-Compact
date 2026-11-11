// What the share cards need from resvg (Phase 6 IMPLEMENTATION doc section 10, C7): the width of a line of text, the PNG
// of an SVG, and a check that each family and weight a card uses is one of the committed TTFs. Plain Node, so the build
// script and the tests use the same code. System fonts are off and only the committed files are loaded: a missing font
// is then a visible failure, not a silent change of face.
//
// resvg does not fail on a family it cannot find: it draws with the first font it loaded. So "every face resolves" is
// checked by drawing a probe string with the fonts loaded in one order and then in the reverse order. A face that
// resolved is the same face both times and has the same width; a face that did not resolve is the fallback, which is the
// first font loaded, and so changes with the order.
import { readdirSync } from "node:fs";
import { join } from "node:path";
import { Resvg } from "@resvg/resvg-js";

// `import.meta.dirname`, not `import.meta.url`: the tests run under jsdom, where the URL is not a file: URL.
export const FONT_DIR = `${join(import.meta.dirname, "..", "fonts-ttf")}/`;

/** Every committed TTF, by path: the four faces the cards use. */
export function fontFiles() {
  return readdirSync(FONT_DIR)
    .filter((name) => name.endsWith(".ttf"))
    .sort()
    .map((name) => `${FONT_DIR}${name}`);
}

function options(files, width) {
  return {
    font: { loadSystemFonts: false, fontFiles: files },
    fitTo: { mode: "width", value: width },
  };
}

/**
 * The measure function layoutCard wants: the width in pixels of one line of text in a style. `svgOf` builds the one-line
 * SVG (cards.ts's `measureSvg`). A line resvg draws nothing for (no font loaded) measures as 0.
 */
export function makeMeasure(svgOf, files = fontFiles()) {
  const kept = new Map();
  return (text, style) => {
    const key = `${style}|${text}`;
    const known = kept.get(key);
    if (known !== undefined) return known;
    const box = new Resvg(svgOf(text, style), options(files, 2400)).getBBox();
    const width = box === undefined ? 0 : box.width;
    kept.set(key, width);
    return width;
  };
}

/** The card's PNG. `width` is the card's own width, so the image is not scaled. */
export function rasterize(svg, width, files = fontFiles()) {
  return new Resvg(svg, options(files, width)).render().asPng();
}

const PROBE = "Hamburgefonstiv 0123456789 quick brown fox";

function probeWidth(family, weight, files) {
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="200">' +
    `<text x="0" y="100" font-family="'${family}'" font-weight="${weight}" font-size="40">${PROBE}</text></svg>`;
  const box = new Resvg(svg, options(files, 2400)).getBBox();
  return box === undefined ? 0 : box.width;
}

/** Throws unless each face in `faces` ([{ family, weight }]) draws with a font of its own, not the fallback. */
export function assertFonts(faces, files = fontFiles()) {
  const reversed = [...files].reverse();
  const nothing = "A family that does not exist";
  if (files.length < 2 || probeWidth(nothing, 400, files) === probeWidth(nothing, 400, reversed)) {
    throw new Error("card-render: the fonts in fonts-ttf/ cannot tell a missing face from a found one");
  }
  const widths = new Map();
  for (const { family, weight } of faces) {
    const forward = probeWidth(family, weight, files);
    if (forward === 0 || forward !== probeWidth(family, weight, reversed)) {
      throw new Error(`card-render: "${family}" at weight ${weight} is not among the TTFs in fonts-ttf/`);
    }
    widths.set(`${family}|${weight}`, forward);
  }
  return widths;
}
