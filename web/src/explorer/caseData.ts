/**
 * Lookups and predicates over the real cases' files (Phase 6 IMPLEMENTATION doc sections 8 and 20, KNOWN-GAPS OPEN
 * 2026-10-31). They compare values the files carry and compute nothing: no count, rate or share is derived here.
 */
import type { CaseFile, CaseReading } from "./data";

/** The matcher's label for a reading whose nearest goal is farther than `d_star`. */
export const NO_GOOD_MATCH = "no_good_match";

/**
 * True when there is at least one reading and every reading of every file is labelled no good match (section 20:
 * "if and only if"). It is a predicate over the files' labels; no count is derived for it, and with no files, or a
 * file with no readings, it is false, so the sentence is never shown before the data has loaded.
 */
export function everyReadingNoGoodMatch(files: ReadonlyArray<Pick<CaseFile, "readings">>): boolean {
  const labels = files.flatMap((file) => file.readings.map((reading) => reading.label));
  return labels.length > 0 && labels.every((label) => label === NO_GOOD_MATCH);
}

/** A file's readings in the order shown: the primary reading, then each alternative in the file's order. */
export function orderedReadings(file: Pick<CaseFile, "readings">): CaseReading[] {
  const primary = file.readings.filter((reading) => reading.reading === "primary");
  return [...primary, ...file.readings.filter((reading) => reading.reading !== "primary")];
}

/**
 * Whether a reading shows a nearest goal and a gap: not where every distance is equal, because the nearest is then
 * the matcher's tie-break by letter and not a finding (note 1), and not where the file has none.
 */
export function showsNearest(reading: Pick<CaseReading, "all_distances_equal" | "nearest">): boolean {
  return !reading.all_distances_equal && reading.nearest !== null;
}

/** Note 1 applies to a reading where every distance is equal. */
export function hasTieNote(reading: Pick<CaseReading, "all_distances_equal">): boolean {
  return reading.all_distances_equal;
}

/** Note 2 applies to a reading with one observable line. */
export function hasOneLineNote(reading: Pick<CaseReading, "one_observable_line">): boolean {
  return reading.one_observable_line;
}

/**
 * `depends_on_reading` inherits note 1's tie-break when any reading of the file has every distance equal: the flag
 * compares the readings' nearest goals, and one of them is then arbitrary.
 */
export function dependsOnReadingNote(file: Pick<CaseFile, "readings">): boolean {
  return file.readings.some((reading) => reading.all_distances_equal);
}

/** The label every reading of the file shares, or null when they differ. */
export function labelUnderEveryReading(file: Pick<CaseFile, "readings">): string | null {
  const first = file.readings[0]?.label;
  if (first === undefined) return null;
  return file.readings.every((reading) => reading.label === first) ? first : null;
}
