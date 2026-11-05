/**
 * Every word the page shows lives in this file, except data values and the name "Horizon Compact".
 *
 * `his` is for his words (planning/06 section 8; these four were Claude-drafted at his request and approved by him,
 * 2026-11-05, the IMPLEMENTATION doc section 20). A value may be a marked placeholder while it is unwritten: the
 * test "his words are written" fails while any still begins with `[his:`, so the deploy commit cannot ship without
 * them. An empty `description` means the page has no meta description.
 */
export const his = {
  lede: "A compact is an agreement about whose good a group is run for, and a horizon is how far ahead it looks. Horizon Compact asks AI models to make the same decision about where a company's money goes under five different stated objectives, one of them no objective at all. The point is to test a claim the Business Roundtable has made since 2019, that over a long enough horizon, running a company for its shareholders and running it for everyone with a stake in it lead to the same decisions.",
  notice:
    "Nothing below is a result. These are fifteen test runs on a made-up garden club's $1,500 budget, a stand-in with the same shape as the experiment's decision and none of its subject, so the charts and tables could be checked without revealing anything about the real question. The experiment's runs reach this site when they are complete.",
  resultsTitle: "Results that go against what I expected",
  resultsSentence:
    "Nothing is here yet. When the experiment's results reach this site, every finding that goes against what I expected will be listed in this section, which was planned before the experiment ran so that listing them would be the default rather than a choice made after seeing them.",
  description: "",
};

/**
 * Claude-drafted words, approved by him word for word only where section 20 says so (the three redrafted keys and
 * notes, 2026-11-05); the rest await his explicit approval before the page goes public (C4). Where a key or note holds related facts they are
 * joined as a person would join them, with no run of short same-length sentences, no "not X, it's Y" turn, no
 * reflexive three, no colon reveal and no tidy closing restatement (his rule, 2026-11-05).
 */
export const labels = {
  // The chart
  chartTitle: "Amounts by line, three runs per priority",
  chartKey:
    "Each dot is one run, the solid tick marks the mean of the three, and the thin mark at the end of each line is its cap; point at a dot to follow that run through every line.",
  priorityControl: "Priority",
  allFive: "All five",
  priorities: {
    color: "Color",
    fragrance: "Fragrance",
    water: "Low water use",
    butterflies: "Butterflies",
    none: "No priority set",
  } as Record<string, string>,
  sources: "Sources",
  uses: "Uses",
  runCount: (n: number) => `n = ${n} runs`,
  openDay: "open day",
  testLabel: "test run, placeholder content",
  tooltipRun: "run",

  // First attempt and final
  statusTitle: "First attempt and final",
  statusKey:
    "The table counts how each priority's runs ended, on the first attempt and on the final one, and lists every status even at zero.",
  statusHeading: "Status",
  runsHeading: "Runs",
  first: "first",
  final: "final",

  // Every run
  runsTitle: "Every run",
  runsKey: "Each run in the chart above has one row here, with its amount on every line.",
  runsTableLabel: "Every run, one row each",
  statusTableLabel: "First attempt and final status counts, by priority",
  columnRun: "Run",
  columnPriority: "Priority",
  columnStatus: "Status",
  columnAttempts: "Attempts",
  columnOpenDay: "Open day",
  columnImage: "Image",

  // Provenance
  provenanceTitle: "Provenance",
  termSweep: "Sweep",
  termModel: "Model, as served",
  termImage: "Image digest",
  termCode: "Code",
  termContentHash: "Content hash",
  termRunner: "Runner",
  termStarted: "Started",
  termFinished: "Finished",
  termRuns: "Runs",
  termCost: "Measured cost",
  runsFinished: (finished: number, planned: number) => `${finished} of ${planned} finished`,
  utc: "UTC",
  provenanceNote: (prefix: string) =>
    `The records are kept write-once in S3 under ${prefix}. The image this digest names is no longer in the registry, whose old rule kept only the ten newest images.`,

  // Footer
  copyright: "© 2026 sjtroxel",
  allRightsReserved: ". All rights reserved.",
  githubLabel: "GitHub, Horizon Compact (opens in a new tab)",
};

export const PLACEHOLDER_MARK = "[his:";

/** A value is still a placeholder while it begins with the marker. */
export function isPlaceholder(text: string): boolean {
  return text.startsWith(PLACEHOLDER_MARK);
}
