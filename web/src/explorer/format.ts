/**
 * The only place the explorer turns a number from the data into something else (Phase 6 IMPLEMENTATION doc section 5,
 * C4's rule: reshape, never compute). Three kinds of thing are allowed here and nothing else:
 *
 *  1. Display formats: a share or rate as a percentage, a difference or an interval end as points (one point is
 *     0.01), `alpha` as the interval's confidence level. Each names its precision.
 *  2. Integer sums of run counts, for a total the file does not carry. No mean, rate, share, difference, interval,
 *     median or verdict is ever derived.
 *  3. Pixel positions: a value mapped to an axis, and a deterministic vertical jitter from a hash of the run id.
 *
 * Each output is pinned to its source field by format.test.ts.
 */
import type { Comparison, GridFile, ObjectiveRate } from "./data";

const MINUS = "−"; // a real minus sign, not a hyphen

/**
 * A share or a rate as a percentage. Precision: `digits` decimal places, one unless a caller says otherwise. The
 * shares in the data are exact fractions of a run count (one person on a scenario of 125 people is 0.8 of a point),
 * so a whole percent would round some of them away; an axis label asks for none.
 */
export function formatPercent(share: number, digits = 1): string {
  return `${(share * 100).toFixed(digits)}%`;
}

/** A share as a whole percentage ("62%"): the display format for a coded lever share, which the case page shows without decimals. */
export function formatWholePercent(share: number): string {
  return formatPercent(share, 0);
}

/**
 * A reason from a case file, shown under a status line that already says "withheld": without the file's own leading
 * "withheld: " (exactly that prefix, nothing else), so the word is not said twice. The rest of the reason is verbatim; a
 * reason without the prefix comes back unchanged.
 */
export function withoutWithheldPrefix(reason: string): string {
  const prefix = "withheld: ";
  return reason.startsWith(prefix) ? reason.slice(prefix.length) : reason;
}

/**
 * A difference or an interval end, in points (one point is 0.01), signed, to `digits` decimal places (one unless a
 * caller says otherwise). A value that rounds to zero carries no sign: "0.0", never "-0.0".
 */
export function formatPoints(difference: number, digits = 1): string {
  const text = Math.abs(difference * 100).toFixed(digits);
  if (Number(text) === 0) return text;
  return `${difference < 0 ? MINUS : "+"}${text}`;
}

/** A distance from the matcher (0 to 1) as it is in the file, to `digits` decimal places (three unless asked). */
export function formatDistance(distance: number, digits = 3): string {
  return distance.toFixed(digits);
}

/**
 * A comparison's difference and its interval as text, in points, or null when the file has none (a comparison that
 * is not assessable). Each end is `formatPoints` of the field.
 */
export function formatDifference(
  difference: number | null,
  low: number | null,
  high: number | null,
): string | null {
  if (difference === null || low === null || high === null) return null;
  return `${formatPoints(difference)} points, interval ${formatPoints(low)} to ${formatPoints(high)}`;
}

/**
 * The difference's absolute value in whole points, rounded down (his pick, section 24): used by the lead and the
 * plain sentences. The 1e-9 corrects float noise first, because 0.29999999999999993 is 30 points in the data and
 * would read 29 without it; protocol 6.3 allows the same tolerance on its own comparisons.
 */
export function wholePointsDown(difference: number): number {
  return Math.floor(Math.abs(difference) * 100 + 1e-9);
}

/**
 * The interval's confidence level from `alpha`, as a percentage to one decimal place: 0.003125 is "99.7%" (the
 * protocol's "99.7% in prose", section 6.4).
 */
export function confidenceLevel(alpha: number): string {
  return `${((1 - alpha) * 100).toFixed(1)}%`;
}

/**
 * Valid runs of a comparison's first and second objective: the sums of `valid_runs`' second and third entries over
 * its wordings. A comparison that is not assessable has none, and these are 0 and 0: a caller must not show them as a
 * count of runs compared.
 */
export function comparisonRuns(comparison: Pick<Comparison, "valid_runs">): {
  first: number;
  second: number;
} {
  let first = 0;
  let second = 0;
  for (const [, a, b] of comparison.valid_runs) {
    first += a;
    second += b;
  }
  return { first, second };
}

/** A scenario's attempted runs: the sum of `objective_rates[].attempted`. */
export function attemptedRuns(rates: readonly ObjectiveRate[]): number {
  let total = 0;
  for (const rate of rates) total += rate.attempted;
  return total;
}

/**
 * The valid and the attempted runs of one wording across the goals: integer sums of the descriptive cells' `runs` (the
 * cells with that wording and no choice) and of the cell statuses' `attempted`. For a figure that draws one wording of a
 * grid (the studies' grid, cut to w2), whose note line must state that wording's runs and not the whole file's.
 */
export function wordingRuns(
  file: Pick<GridFile, "cells" | "descriptive">,
  wording: string,
): { valid: number; attempted: number } {
  let valid = 0;
  for (const cell of file.descriptive.cells) {
    if (cell.wording_id === wording && cell.choice === null) valid += cell.runs;
  }
  let attempted = 0;
  for (const cell of file.cells) if (cell.wording_id === wording) attempted += cell.attempted;
  return { valid, attempted };
}

/** A value on an axis from `low` to `high`, as the percentage of the plot's width an SVG coordinate takes. */
export function axisPercent(value: number, low: number, high: number): string {
  return `${((value - low) / (high - low)) * 100}%`;
}

/**
 * The upper end of an axis that must hold every one of `values`: `floor` unless a value is higher. A lever's share of
 * a scenario's money is 0 to 1 on most scenarios; on s4 a lever can take many times the year's money, and its axis
 * runs to the data's own highest value, shared by every panel so the panels stay comparable.
 */
export function axisExtent(values: readonly number[], floor = 1): number {
  return Math.max(floor, ...values);
}

/** The width, as a percentage of the plot's width, of the stretch of the axis from `from` to `to`. */
export function axisSpan(from: number, to: number, low: number, high: number): string {
  return `${((to - from) / (high - low)) * 100}%`;
}

/**
 * Which side of an interval its words go on, by the room each side has on the axis: "right" of the high end, or "left"
 * of the low end, whichever has more axis left (ties go right). A pixel-position decision (rule 3 above): it chooses
 * where text is drawn and nothing is read from it.
 */
export function wordsSide(low: number, high: number, axisLow: number, axisHigh: number): "left" | "right" {
  return axisHigh - high >= low - axisLow ? "right" : "left";
}

/** How text sits on a point of an axis so it stays on the plot: from its start near the low end, to its end near the
 * high end, centred between. A pixel-position decision, as `wordsSide`. */
export function edgeAnchor(value: number, axisLow: number, axisHigh: number): "start" | "middle" | "end" {
  const at = (value - axisLow) / (axisHigh - axisLow);
  if (at < 0.08) return "start";
  if (at > 0.92) return "end";
  return "middle";
}

/**
 * A deterministic offset in pixels, from -amplitude/2 to +amplitude/2, from a hash of the run id (FNV-1a), so a dot
 * keeps its place from one render to the next and the same run sits in the same place in every chart.
 */
export function jitter(runId: string, amplitude: number): number {
  let hash = 0x811c9dc5;
  for (let i = 0; i < runId.length; i++) {
    hash ^= runId.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return (hash / 0xffffffff - 0.5) * amplitude;
}

/** The vertical position of a run's dot in a row `height` tall: the row's middle plus the run's jitter. */
export function dotY(height: number, runId: string, amplitude: number): number {
  return height / 2 + jitter(runId, amplitude);
}

/** The centre of the `index`th slot of a unit chart, `perRow` to a row, each slot `step` wide and tall. */
export function unitSlot(index: number, perRow: number, step: number): { x: number; y: number } {
  return { x: (index % perRow) * step + step / 2, y: Math.floor(index / perRow) * step + step / 2 };
}

/** The size of a unit chart's view box for `count` dots, `perRow` to a row: one row at least, so an empty group
 * keeps its place. */
export function unitBox(count: number, perRow: number, step: number): { width: number; height: number } {
  return { width: perRow * step, height: Math.max(1, Math.ceil(count / perRow)) * step };
}
