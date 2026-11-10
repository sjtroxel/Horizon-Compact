/**
 * The result-sentence templates (Phase 6 IMPLEMENTATION doc sections 11 and 12, C4 decided point 3).
 *
 * CLAUDE-DRAFTED AND UNAPPROVED. Every template below is Claude's wording, from page 6 of the throwaway previews;
 * he approves each word for word at section 14 step 8 (section 11). `not_assessable` is new in C4 and has no
 * preview behind it.
 *
 * Every result sentence the explorer shows is the output of one of these functions, with its template id on the
 * element (`data-template`). A test renders every scenario view for both models and rejects any result sentence that
 * is not a template's output. The sentences are filled only from fields of the comparison and from the goals' plain
 * names: no number is computed (the points are `wholePointsDown` of the file's `difference`, a display format).
 *
 * A "no split" sentence never says the decisions were the same: protocol 1.5, "no split never means the same
 * decisions". It is about the one named outcome.
 */
import type { Comparison, Verdict } from "./data";
import { wholePointsDown } from "./format";

export type TemplateId = Verdict;

export const TEMPLATE_IDS: readonly TemplateId[] = ["split", "no_split", "inconclusive", "not_assessable"];

export interface Sentence {
  id: TemplateId;
  text: string;
}

const quote = (name: string) => `“${name}”`;

/** "w1", "w1 and w2", "w1, w2 and w3" */
function listed(ids: readonly string[]): string {
  if (ids.length <= 1) return ids.join("");
  return `${ids.slice(0, -1).join(", ")} and ${ids[ids.length - 1]}`;
}

/** The fields of a comparison a sentence reads. */
export type SentenceInput = Pick<
  Comparison,
  "first" | "second" | "final_verdict" | "difference" | "downgrade_reason" | "dropped_wordings"
>;

/**
 * The sentence for one comparison. `names` maps a goal's letter to its plain name, and `outcome` is the scenario's
 * outcome phrase (`explorerLabels.outcomePhrases`).
 */
export function resultSentence(
  comparison: SentenceInput,
  names: Readonly<Record<string, string>>,
  outcome: string,
): Sentence {
  const x = quote(names[comparison.first] ?? comparison.first);
  const y = quote(names[comparison.second] ?? comparison.second);
  switch (comparison.final_verdict) {
    case "split": {
      // The difference is the first goal's value minus the second's: a negative one means lower under the first.
      const direction = (comparison.difference ?? 0) < 0 ? "lower" : "higher";
      const points = wholePointsDown(comparison.difference ?? 0);
      return {
        id: "split",
        text: `${x} and ${y} came out different: ${outcome} was about ${points} points ${direction} under ${x}.`,
      };
    }
    case "no_split":
      return {
        id: "no_split",
        text: `${x} and ${y} came out about the same on ${outcome}. That is about this one measure, not every choice they made.`,
      };
    case "inconclusive":
      return {
        id: "inconclusive",
        text: `The runs can’t tell whether ${x} and ${y} differ on ${outcome}.`,
      };
    case "not_assessable": {
      const reason = comparison.downgrade_reason === null ? "" : ` (${comparison.downgrade_reason})`;
      const dropped = comparison.dropped_wordings.map((w) => w.wording_id);
      const tail = dropped.length === 0 ? "" : ` Wordings dropped: ${listed(dropped)}.`;
      return {
        id: "not_assessable",
        text: `Too many runs failed in every wording to compare ${x} and ${y} on ${outcome}${reason}.${tail}`,
      };
    }
  }
}
