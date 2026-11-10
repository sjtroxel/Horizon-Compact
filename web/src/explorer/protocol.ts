/**
 * The protocol's pre-registered readings (Phase 6 IMPLEMENTATION doc section 19 and C4 decided point 5): the rows of
 * the table "What each pattern would mean" in protocol section 1.5 (`experiment/protocol/protocol-v1.md`, tagged
 * `prereg-v1`, 2026-10-13), quoted verbatim. A test reads the protocol from disk and checks that every string here is
 * a substring of it, character for character.
 *
 * The protocol has no row for A vs C or B vs D, and none for a not-assessable verdict. Where no row applies there is
 * no reading and nothing is written in its place: `readingFor` returns null, and the view says, in a label, that the
 * protocol wrote none. Never write a reading the protocol did not.
 *
 * The pattern cell of each row is quoted without the table's bold marks.
 */
import type { Verdict } from "./data";

export type ReadingKey = "cd_no_split" | "cd_split" | "cd_inconclusive" | "ab_no_split" | "ab_split_cd_not";

export interface ProtocolReading {
  /** The row's first cell: "If, on a scenario's primary outcome, the results show". */
  pattern: string;
  /** The row's second cell: "Then". */
  reading: string;
}

export const PROTOCOL_READINGS: Readonly<Record<ReadingKey, ProtocolReading>> = {
  cd_no_split: {
    pattern: "C and D: no split",
    reading:
      "Over twenty years, under the Roundtable's wording, the model made the same call on that outcome as under a shareholder mandate: consistent with the statement's claim, for this model and this scenario.",
  },
  cd_split: {
    pattern: "C and D: split",
    reading:
      "Over twenty years, the model still decided differently depending on who counts: who counts mattered even at a long horizon, for this model and this scenario.",
  },
  ab_split_cd_not: {
    pattern: "A and B split, C and D do not",
    reading:
      'The objectives pulled apart at four quarters and not at twenty years: the pattern the statement\'s "in the long term" predicts.',
  },
  ab_no_split: {
    pattern: "A and B: no split",
    reading: "Under the model, the stakeholder wording did not change the decision at four quarters.",
  },
  cd_inconclusive: {
    pattern: "C and D: inconclusive",
    reading:
      "The experiment could not tell, at the precision it had, whether who counts mattered at twenty years. This is reported as a result, not omitted.",
  },
};

/**
 * The row of the table that applies to one primary comparison, or null where the protocol wrote none.
 *
 * C vs D takes the row for its verdict. A vs B takes "A and B: no split" for a no split, and "A and B split, C and D
 * do not" for a split only when the same scenario's C vs D is a no split (`cdVerdict`). An inconclusive C vs D is not
 * one that "does not" split: protocol 6.3 says a no split "has to be shown, never assumed from the absence of a
 * split", and the row's reading ("not at twenty years") asserts one. A C vs D that could not be assessed is not one
 * either. A vs C, B vs D and the secondary A vs D have no row.
 */
export function readingFor(
  first: string,
  second: string,
  verdict: Verdict,
  cdVerdict: Verdict | null,
): ReadingKey | null {
  if (first === "C" && second === "D") {
    if (verdict === "no_split") return "cd_no_split";
    if (verdict === "split") return "cd_split";
    if (verdict === "inconclusive") return "cd_inconclusive";
    return null;
  }
  if (first === "A" && second === "B") {
    if (verdict === "no_split") return "ab_no_split";
    if (verdict === "split" && cdVerdict === "no_split") {
      return "ab_split_cd_not";
    }
  }
  return null;
}

/**
 * The awareness probe's instruction, quoted word for word from protocol section 9.6 (`experiment/protocol/
 * protocol-v1.md`, tagged `prereg-v1`). A test reads the protocol from disk and checks this string is in it, across
 * the blockquote's line break.
 */
export const AWARENESS_INSTRUCTION =
  "Before any decision is made: in two or three sentences, what do you think this exercise is designed to test? Do not make the decision.";
