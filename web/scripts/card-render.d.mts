export const FONT_DIR: string;
export function fontFiles(): string[];
export function makeMeasure<S extends string>(
  svgOf: (text: string, style: S) => string,
  files?: string[],
): (text: string, style: S) => number;
export function rasterize(svg: string, width: number, files?: string[]): Buffer;
export function assertFonts(
  faces: ReadonlyArray<{ family: string; weight: number }>,
  files?: string[],
): Map<string, number>;
