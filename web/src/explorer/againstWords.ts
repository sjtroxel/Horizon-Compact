/**
 * The words around the section for results against the thesis (Phase 6 IMPLEMENTATION doc section 19, "On the page").
 *
 * CLAUDE-DRAFTED, APPROVED (his, 2026-11-11, section 11's dated note). Drafted by Claude (Sonnet, C4) from section 19;
 * "the thesis" became "the starting expectation" at section 14 step 8, to match his title. His own words for the section, its title and its introductory sentence,
 * are `explorerHis.againstTitle` and `explorerHis.againstIntro`, not here. The citation `against_thesis.rule` is
 * shown as the data has it.
 */

export const againstWords = {
  /** The id the story's beat and every scenario view's link point to. */
  sectionId: "against-the-thesis",

  ruleHeading: "The rule that decides what is listed here",
  ruleParagraphs: [
    "A result is listed here by a rule, not by judgment. The starting expectation (the planning documents call it the thesis) is the one written down before the results existed: that a longer horizon, or a wider set of people who count, makes the model cut less.",
    "The rule reads each main comparison on its own, model by model, never pooled. It lists a comparison when its verdict is “no split”, or when its verdict is “split” and the goal expected to cut less cut more. The second goal of each pair is the one expected to cut less.",
    "Which way “cut more” runs on each scenario comes from the protocol’s own definition of its primary outcome, not from a choice made after the results.",
    "Not listed, and shown in full on the scenario views: a split in the expected direction, an inconclusive result and a result that could not be assessed, none of which is against anything. The secondary comparison (A vs D) and the thinking sub-study are not read.",
    "A scenario on which every primary comparison of a model is “no split” is listed whole. No threshold for “everything cuts” was written before the results, and one chosen now would be chosen after them.",
  ],
  sourcesHeading: "Where the rule’s terms come from, with their dates",
  sources: [
    "Planning document 00, section 4, principle 3 (2026-10-02): “If the long-horizon CEO also cuts payroll, that ships.”",
    "Planning document 00, section 5.1, “how the grid reads” (2026-10-03): a longer horizon or a wider set of people who count is expected to make the model cut less, and “everything cuts” is the result against the thesis.",
    "The protocol, section 1.5, tagged prereg-v1 (2026-10-13): the table of what each pattern would mean.",
  ],
  writtenLine: "The rule was written on 2026-11-09, after the results were revealed on 2026-10-15.",
  disclosure:
    "Disclosure: the rule was written after the reveal, and its drafter had seen every grid verdict before writing it. Its terms are all taken from documents dated before the results; its wording is not. No other rule was tried against the data. The list is whatever this rule yields, empty included.",
  citationLabel: "The rule’s citation, as the data has it:",

  entriesHeading: "What the rule lists",
  wholeHeading: "Scenarios listed whole",
  wholeLine: (scenario: string, model: string) =>
    `${model}, scenario ${scenario}: every primary comparison is “no split”.`,
  emptyList:
    "The rule listed nothing: no comparison met it. The list is whatever the rule yields, and today that is nothing.",

  entryPair: (first: string, second: string) => `${first} vs ${second}`,
  clauseNoSplit: "Listed because its verdict is “no split”.",
  clauseReversed: "Listed because its verdict is “split” and the goal expected to cut less cut more.",
  alsoAgainstAuthor:
    "This pair is also against the author’s starting expectation: a “no split” here is consistent with the Roundtable’s claim and against what the author expected.",
  s4Note:
    "A note on scenario s4: it offers a cut and an expansion rather than a cut alone, so reading “cut more” as “fund less” is the one direction a reviewer could dispute. The rule reads it that way because the starting expectation was that new capability is used to cut payroll rather than to expand what is possible.",
  none: "none",
  differenceLabel: "Difference",
  intervalLabel: "Interval",
  validRunsLabel: "Valid runs",
  verdictLabel: "Official verdict",
} as const;
