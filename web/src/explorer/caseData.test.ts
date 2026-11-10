import { describe, expect, it } from "vitest";
import {
  NO_GOOD_MATCH,
  dependsOnReadingNote,
  everyReadingNoGoodMatch,
  hasOneLineNote,
  hasTieNote,
  labelUnderEveryReading,
  orderedReadings,
  showsNearest,
} from "./caseData";
import type { CaseFile } from "./data";
import { realCaseFiles } from "./fixtures";

const files = realCaseFiles.map((c) => c.file);
const haiku = realCaseFiles.filter((c) => c.model === "haiku-5-5");

describe("the predicate for 'every reading of every case is no good match'", () => {
  it("is true over today's ten case files, whose twenty readings all carry that label", () => {
    expect(files).toHaveLength(10);
    expect(files.flatMap((f) => f.readings)).toHaveLength(20);
    expect(everyReadingNoGoodMatch(files)).toBe(true);
    expect(NO_GOOD_MATCH).toBe("no_good_match");
  });

  it("is false when one reading differs, whichever it is", () => {
    for (const [i, j] of [
      [0, 0],
      [4, 1],
      [9, 1],
    ] as const) {
      const edited: CaseFile[] = structuredClone(files);
      edited[i]!.readings[j]!.label = "match";
      expect(everyReadingNoGoodMatch(edited), `${i}.${j}`).toBe(false);
    }
  });

  it("is false with no files, and with a file with no readings, so it never claims before the data has loaded", () => {
    expect(everyReadingNoGoodMatch([])).toBe(false);
    expect(everyReadingNoGoodMatch([{ readings: [] }])).toBe(false);
  });
});

describe("the matcher notes (KNOWN-GAPS OPEN 2026-10-31), as predicates over the files' own fields", () => {
  it("note 1 applies to exactly the readings whose five distances are equal: Haiku 5.5's primary reading, all five cases", () => {
    const equal = realCaseFiles.flatMap(({ label, model, file }) =>
      file.readings.filter(hasTieNote).map((r) => `${label} ${model} ${r.reading}`),
    );
    expect(equal.sort()).toEqual(
      ["closure-07", "closure-19", "pre-11", "pre-224", "pre-25"].map((l) => `${l} haiku-5-5 primary`),
    );
    for (const { file } of realCaseFiles) {
      for (const r of file.readings) {
        expect(hasTieNote(r)).toBe(r.all_distances_equal);
        // The flag is what the five distances say: every distance and interval the same.
        const first = r.distances[0]!;
        const same = r.distances.every(
          (d) => d.distance === first.distance && d.low === first.low && d.high === first.high,
        );
        expect(same, `${file.case} ${file.model_key} ${r.reading}`).toBe(r.all_distances_equal);
      }
    }
  });

  it("note 2 applies to exactly the readings with one observable line: closure-19's u1, for both models", () => {
    const one = realCaseFiles.flatMap(({ label, model, file }) =>
      file.readings.filter(hasOneLineNote).map((r) => `${label} ${model} ${r.reading}`),
    );
    expect(one.sort()).toEqual(["closure-19 gpt-oss-openrouter u1", "closure-19 haiku-5-5 u1"]);
    for (const { file } of realCaseFiles) {
      for (const r of file.readings) expect(hasOneLineNote(r)).toBe(r.observable_lines.length === 1);
    }
  });

  it("a nearest goal is shown exactly where not every distance is equal", () => {
    for (const { file } of realCaseFiles) {
      for (const r of file.readings) expect(showsNearest(r)).toBe(!r.all_distances_equal);
    }
    expect(showsNearest({ all_distances_equal: false, nearest: null })).toBe(false);
    expect(showsNearest({ all_distances_equal: true, nearest: "A" })).toBe(false);
  });

  it("depends_on_reading carries note 1 in exactly Haiku 5.5's five files, and is true in three of them", () => {
    expect(haiku).toHaveLength(5);
    for (const { model, file } of realCaseFiles) {
      expect(dependsOnReadingNote(file), `${file.case} ${model}`).toBe(model === "haiku-5-5");
    }
    expect(
      haiku
        .filter((c) => c.file.depends_on_reading)
        .map((c) => c.label)
        .sort(),
    ).toEqual(["closure-07", "closure-19", "pre-11"]);
    // The flag does not mean the label changes: the label is no good match under every reading of every file.
    for (const { file } of realCaseFiles) expect(labelUnderEveryReading(file)).toBe(NO_GOOD_MATCH);
  });

  it("the label under every reading is null where the readings differ", () => {
    const edited = structuredClone(files[0]!);
    edited.readings[1]!.label = "tie";
    expect(labelUnderEveryReading(edited)).toBeNull();
    expect(labelUnderEveryReading({ readings: [] })).toBeNull();
  });
});

describe("the readings' order", () => {
  it("puts the primary reading first, then the alternatives in the file's order", () => {
    const file = structuredClone(files[0]!);
    file.readings = [...file.readings].reverse();
    expect(file.readings[0]!.reading).not.toBe("primary");
    expect(orderedReadings(file).map((r) => r.reading)).toEqual(["primary", "u1"]);
    for (const f of files) expect(orderedReadings(f)[0]!.reading).toBe("primary");
  });
});
