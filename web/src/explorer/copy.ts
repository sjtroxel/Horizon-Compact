/**
 * Every word the explorer shows lives here or in his.json, except data values and the name "Horizon Compact".
 *
 * BOTH OBJECTS ARE APPROVED (his, 2026-11-11, the Phase 6 IMPLEMENTATION doc section 11's dated notes). Both are
 * Claude-drafted: `explorerHis` at his request on that pass, `explorerLabels` from C3 to C5 with a plain-language pass
 * at step 8. A change to either is his approval again, word for word. The gate that fails on an unwritten explorer word is Phase 6.5's go-live, not this
 * file's tests: the placeholder page's test `his words are written` (src/copy.test.ts) is not widened to these.
 *
 * His words live in his.json (not in this file) because the build's write-paths script, which is plain Node, reads
 * the same titles and descriptions for each path's HTML file.
 *
 * This file may import from ../copy; nothing the placeholder entry (src/main.tsx) imports may import this file.
 */
import type { Pages } from "./page-meta.mjs";
import hisJson from "./his.json";

export { PLACEHOLDER_MARK, isPlaceholder } from "../copy";

export interface StoryHis {
  setupTitle: string;
  setupIntro: string;
  s1Title: string;
  s1Intro: string;
  comparisonsTitle: string;
  comparisonsIntro: string;
  secondTitle: string;
  secondIntro: string;
  othersTitle: string;
  othersIntro: string;
  casesTitle: string;
  casesIntro: string;
  methodsTitle: string;
  methodsText: string;
}

export interface ExplorerHis {
  landingQuestion: string;
  scopeSentence: string;
  /** The opening screen's line explaining the name (planning/06 section 6.4): his words, a placeholder until he writes them. */
  storyName: string;
  /** The guided story's titles and introductions for beats 2 to 6, 8 and 9 (beat 7 keeps `againstTitle` and `againstIntro`). */
  story: StoryHis;
  /** The scenario in brief, per scenario id: his words, a placeholder until he writes them. */
  scenarioBriefs: Record<string, string>;
  /** The section for results against the thesis: his title and his introductory sentence. */
  againstTitle: string;
  againstIntro: string;
  /** The memo reader's introduction. */
  memosIntro: string;
  /** The real-cases page's introduction, and the note that explains why no real-case memo text is shown. */
  casesIntro: string;
  caseMemosHeld: string;
  /** The studies page: its introduction and the titles of its two parts. */
  studiesIntro: string;
  studiesThinkingTitle: string;
  studiesAwarenessTitle: string;
  pages: Pages;
}

export const explorerHis: ExplorerHis = hisJson;

export const explorerLabels = {
  skipToContent: "Skip to the content",
  navLabel: "Sections",
  navStory: "The story",
  navScenario: (id: string) => `Scenario ${id}`,
  navCases: "Real cases",
  navStudies: "Side studies",
  navMemos: "Memos",
  modelSwitch: "Model",
  seeDetails: "See the details",
  scenario: "Scenario",
  exploratory: "exploratory",
  loading: "Loading the data",
  loadFailed: "The data did not load. Reload the page to try again.",
  notFoundTitle: "Page not found",
  notFoundText: "Nothing is at this address.",
  backToStory: "Back to the story",

  // The models, in the order shown, with the name each is called on the page. The data carries only the key. A test
  // ties these keys to index.json's models, so a model added to or dropped from the data fails it.
  models: [
    { key: "haiku-5-5", name: "Haiku 5.5" },
    { key: "gpt-oss-openrouter", name: "gpt-oss-120b" },
  ],

  // The goals: plain names (the letters stay beside them until he decides, Phase 6 section 24), and the words around
  // each goal's literal description from index.json.
  objectiveNames: {
    A: "Shareholders, short term",
    B: "Everyone with a stake, short term",
    C: "Shareholders, long term",
    D: "Everyone with a stake, long term",
    E: "No goal stated",
  } as Record<string, string>,
  goalsHeading: "The five goals the model was given",
  goalsKey:
    "Each run gave the model one of these goals, in the words below, before the same decision. Goal E was given no goal.",
  goalTold: (who: string, when: string) => `Told to create value for ${who}, over ${when}.`,
  goalUnstated: "Told no goal at all.",
  toggleGroup: "Goals shown in the chart",

  // The scenario in brief and the scenario text.
  sceneBriefHeading: "The decision, in brief",
  sceneFullText: "The full scenario text, as the model saw it",
  sceneFullTextNote: "on GitHub, at the pre-registered tag",

  // The chart.
  chartLabel: (scenario: string, model: string) =>
    `The runs of ${model} on scenario ${scenario}, one dot per run`,
  shareKey: {
    s1: "Each dot is one run. Further right, more of the affected people were kept: retrained and moved to a plant role instead of let go.",
    s2: "Each dot is one run. Further right, a larger share of the shortfall fell on the workforce: roles eliminated plus wages or hours cut.",
  } as Record<string, string>,
  choiceKey: "Each dot is one run, placed under the choice the model made. A full row is ten runs.",
  axisEnds: {
    s1: { title: "People kept", low: "none kept", mid: "half", high: "all kept" },
    s2: { title: "Share borne by the workforce", low: "none of it", mid: "half", high: "all of it" },
  } as Record<string, { title: string; low: string; mid: string; high: string }>,
  choices: {
    close: "closed the plant",
    retool: "retooled the plant",
    sell: "sold the plant",
    fund: "funded the program",
    decline: "declined the program",
  } as Record<string, string>,
  runCount: (runs: number) => `${runs} ${runs === 1 ? "run" : "runs"}`,
  nOfN: (n: number, total: number) => `${n} of ${total}`,
  dotTitleShare: (goal: string, wording: string, repeat: number, value: string) =>
    `${goal}, wording ${wording}, repeat ${repeat}: ${value}`,
  dotTitleChoice: (goal: string, wording: string, repeat: number, choice: string) =>
    `${goal}, wording ${wording}, repeat ${repeat}: ${choice}`,
  capValidOfAttempted: (valid: number, attempted: number) => `${valid} valid runs of ${attempted} attempted`,
  capCompany: "on the fictional company",
  loadingScenario: "Loading this scenario",

  // The sentence column. `outcomePhrases` fill the result-sentence templates (sentences.ts), one per scenario.
  outcomePhrases: {
    s1: "the share of the affected people who were kept",
    s2: "the share of the shortfall borne by the workforce",
    s3: "the rate of closing the plant",
    s4: "the rate of funding the program",
  } as Record<string, string>,
  whatRunsShow: "What the runs show",
  verdictNote: (level: string) =>
    `Each verdict is the analysis\u2019s own, at a ${level} confidence level. That is stricter than usual because the study makes 16 main comparisons, and with that many, some would look like a difference by chance alone. The numbers behind each verdict are in the details.`,
  roundtableFlag: "The pair the Roundtable\u2019s claim is about",
  secondaryFlag: "Secondary comparison",
  officialVerdict: "official verdict:",
  verdictWords: {
    split: "split",
    no_split: "no split",
    inconclusive: "inconclusive",
    not_assessable: "not assessable",
  } as Record<string, string>,
  runsPair: (first: number, second: number) => `${first} and ${second} runs`,
  noRunsCompared: "no runs compared",
  keptWordings: (ids: string) => `wordings kept: ${ids}`,
  droppedWordings: (ids: string) => `dropped for failures: ${ids}`,
  noReading: "The protocol wrote no reading for this verdict.",
  readingsNote:
    "Before any results, the study\u2019s written plan (the protocol) said what a few outcomes would mean, for C vs D and for A vs B only. Where one applies, it is quoted under that sentence; the other sentences have none.",
  protocolReadingLabel: "The protocol\u2019s reading, written before the results:",
  repeatsLine:
    "How many times each goal and wording was run was set from a small trial run of each model, before the main runs began (protocol section 8.2).",
  againstLink: "See where the results went against the starting expectation",
  againstMarker: "listed under results against the starting expectation",

  // The details.
  detailsHint: "how sure the runs are, and everything the model chose",
  intervalHeading: "How the goals differ, with the interval",
  intervalKey: (level: string) =>
    `Each bar is the analysis\u2019s ${level} interval for a difference between two goals, first minus second, and the dot is the difference. The shaded band is the threshold the study set before it ran, on both sides of zero. The verdict beside each row is the official one, and it follows protocol section 6.3: a split needs the interval to exclude zero and the difference to reach the threshold on the same side. The interval covers the family of 16 comparisons (a Bonferroni correction).`,
  intervalAxis: "Difference, first minus second, in points",
  intervalRowNotAssessable: "no interval to draw",
  intervalChartLabel: "The differences between goals with their intervals and the threshold band",
  perComparisonHeading: "Each comparison, as the analysis wrote it",
  headlineLabel: "Analysis headline",
  differenceLabel: "Difference",
  keptLabel: "Wordings kept",
  droppedLabel: "Wordings dropped",
  droppedCell: (goal: string, unsuccessful: number, attempted: number) =>
    `${goal}: ${unsuccessful} of ${attempted} unsuccessful`,
  noneWord: "none",
  noNumbers: "no difference or interval",
  sealedLabel: "Sealed wording",
  sealedWordingIs: (id: string) => `wording ${id}`,
  firstAttemptLabel: "First attempt",
  firstAttemptNote: "before any wording was dropped",
  finalLabel: "Final",
  allocationHeading: "Everything the model chose, goal by goal",
  allocationKey:
    "One panel per goal, one row per lever in the scenario\u2019s own order. Each dot is one run\u2019s share on that lever. Every row runs from 0 to 100% unless it names a wider scale, and a lever keeps the same scale in every panel.",
  leverScale: (top: string) => `scale 0 to ${top}`,
  levers: {
    eliminate: "Role eliminated, with severance",
    move_plant_pay: "Retrained, moved to a plant role at that role\u2019s pay",
    move_keep_pay: "Retrained, moved to a plant role keeping current pay",
    eliminate_roles: "Eliminating roles",
    cut_wages_hours: "Cutting wages or hours",
    cut_rnd: "Cutting research and development",
    cut_env_projects: "Cutting environmental projects",
    raise_prices: "Raising prices",
    suppliers: "Negotiating lower prices with suppliers",
    lower_profit: "Accepting lower operating income",
    cut_payouts: "Cutting dividends and share repurchases",
    eliminated: "Roles eliminated, with severance",
    moved_other_plants: "Moved to other plants",
    kept_at_plant: "Kept at the plant (retool only)",
    transferred_to_buyer: "Transferred to the buyer (sell only)",
    program: "The program",
    increase_payouts: "Increasing dividends and share repurchases",
    retain_cash: "Retaining as cash",
    add_rnd: "Research and development outside the program",
    raise_wages: "Raising wages",
    training: "Training for current employees",
    env_projects: "Environmental projects",
    lower_prices: "Lowering prices to customers",
  } as Record<string, string>,
  summaryHeading: (goal: string) => `${goal}: what the runs put on each lever`,
  th: {
    lever: "Lever",
    n: "Runs",
    mean: "Mean",
    median: "Median",
    minimum: "Lowest",
    maximum: "Highest",
    goal: "Goal",
    wording: "Wording",
    repeat: "Repeat",
    attempted: "Attempted",
    valid: "Valid",
    rescaled: "Rescaled",
    refused: "Refused",
    failures: "Failures by type",
    runId: "Run",
    value: "Value",
  },
  failuresHeading: "Failures and refusals, every status shown",
  failuresKey: "One row per goal and wording. A count of zero is shown as zero.",
  runsHeading: "Every run",
  runsKey: "The same runs as the chart, as a table.",
  tableFailures: (type: string, runs: number) => `${type}: ${runs}`,

  // ------------------------------------------------------------------------------------------------------------
  // C5: the memo reader, the real cases and the studies. Claude-drafted, approved 2026-11-11.

  // The memo reader.
  memoKindLabel: "Set of memos",
  memoKinds: { grid: "Main grid", thinking: "Thinking sub-study" } as Record<string, string>,
  memoScenarioLabel: "Scenario",
  memoGoalLabel: "Goal",
  memoRunsHeading: "Runs in this set",
  memoRunLine: (wording: string, repeat: number, status: string) =>
    `wording ${wording}, repeat ${repeat}, ${status}`,
  memoCardLabel: (model: string, letter: string, goal: string, thinking: boolean) =>
    `Written by ${model} under goal ${letter} (${goal}), for a fictional company. This is the model’s output, not the project’s view.${thinking ? " Thinking was on for this run." : ""}`,
  memoRun: "Run",
  memoWording: "Wording",
  memoRepeat: "Repeat",
  memoStatus: "Status",
  memoSource: "Text from",
  memoSources: {
    memo: "the memo the model wrote with its decision",
    reply_text:
      "the model’s plain reply, because it answered in text instead of filling in the decision form",
  } as Record<string, string>,
  memoLeftNone: "This run left no memo.",
  memoSourceHeading: "Source records",
  memoSourceNote: (path: string, sha: string) =>
    `Where this run’s raw records are stored, with a fingerprint (sha256) of each, so anyone can check them against the published list of raw records (${path}, sha256 ${sha}).`,
  memoFinalRecord: "Final record",
  memoAttemptRecord: "Final attempt",
  memoFileLink: "The file these memos are read from",
  memoFileNote: "JSON Lines, one run to a line, exactly as the site reads it",
  memoPrevious: "Previous run",
  memoNext: "Next run",
  memoNone: "no earlier run",
  memoNoneNext: "no later run",
  memoNavLabel: "Move through this set",
  memoLoading: "Loading the memos",
  memoMessages: {
    kind: "That is not a set of memos the reader holds.",
    scenario: "That is not a scenario in this experiment.",
    objective: "That is not one of the five goals.",
    cell: "The reader holds no memos for that combination.",
    run: "That run is not in this set.",
  } as Record<string, string>,
  memoThinkingOnly: (model: string) =>
    `The thinking sub-study ran on ${model} only, so there are no thinking memos for this model.`,
  memoSeeSubStudy: "See the sub-study",
  memoToFirst: "Go to the first memo",

  // The real cases.
  casesFraming:
    "These cases apply the same study plan to real decisions. They are readings, not tests, and they do not prove the study\u2019s method right.",
  casesLabelLead: "Every case below carries this label, as its file writes it:",
  allNoGoodMatch: "Every reading of every case below is labelled no good match, for every model.",
  shortfallHeading: "What the selection found, and what it did not",
  shortfallNote:
    "The study plan asks for cases of three types. A type that finds too few cases is reported as short, and its places are never filled by judgment (protocol section 12.1).",
  caseTypes: {
    closure: "Closure or restructuring",
    retool: "Invest or retool",
    ai: "AI-attributed workforce change",
  } as Record<string, string>,
  shortfallTableLabel: "Cases found and places left short, by type",
  shortfallType: "Type",
  shortfallFound: "Cases found",
  shortfallShort: "Places left short",
  shortfallAtMost: "The most cases the protocol allows",
  shortfallFilled: "Cases that filled a short type’s place",
  shortfallFilledNote:
    "Under the exploratory selection, a place a short type left open could go to a case of another type.",
  selectionLogsHeading: "The public selection logs",
  selectionLogs: {
    preregistered: "The pre-registered search’s log",
    exploratory: "The exploratory selection’s log",
  } as Record<string, string>,
  caseTypeLabel: "Type",
  caseDescriptionHeading: "The case, as published",
  caseDescriptionStatus: (status: string) => `Description: ${status}`,
  caseDescriptionWithheld: "withheld, so this case is shown by its type only",
  caseDossierHeading: "The dossier",
  caseDossierStatus: (published: boolean) => `Dossier: ${published ? "published" : "withheld"}`,
  caseReasonLabel: "Reason, as the file states it",
  caseReidentHeading: "The check that the company cannot be identified",
  caseReidentStatus: (status: string) => `Status: ${status}`,
  caseThresholdLabel: "Threshold",
  caseProbesHeading: "Recognition probes",
  caseProbesKey:
    "Before any decision run, each model was asked which company the case\u2019s background file (the dossier) described (protocol section 12.8). A call passes when the model does not name the company.",
  caseProbeSet: "Set",
  caseProbeModel: "Model",
  caseProbeCalls: "Calls",
  caseProbePassed: "Passed",
  caseCompanyHeading: "The company’s decision, as the case codes it",
  caseCompanyChoice: (choice: string) => `Choice: ${choice}`,
  caseCompanyReading: (reading: string) => `Reading ${reading}`,
  caseNoShares: "no lever shares in this reading",
  caseDimensionsHeading: "What the case was matched on",
  caseObservable: "Matched on",
  caseExcluded: "Left out",
  caseDimensionChoice: "The choice itself (close, retool or sell)",
  caseModelHeading: (model: string) => model,
  caseRunCounts: (runs: number) => `${runs} runs, by their final status:`,
  caseFinalStatus: (status: string, runs: number) => `${status}: ${runs}`,
  caseReadingNote:
    "The primary reading follows the scoring guide (the rubric) as written. Where the guide had to make an uncertain call about what the company did, an alternative reading matches the runs again with that call made the other way.",
  readingNames: { primary: "Primary reading" } as Record<string, string>,
  readingAlternative: (id: string) => `Alternative reading ${id}`,
  readingLabels: {
    match: "match",
    tie: "tie",
    no_good_match: "no good match",
    not_enough_disclosed: "not enough disclosed",
  } as Record<string, string>,
  readingLabelIs: (label: string) => `Label: ${label}`,
  readingReason: "Reason, as the matcher wrote it",
  readingLines: "Lines of the company’s decision that could be seen in this reading",
  distanceKey:
    "One row per goal. The dot shows how far that goal’s runs were from what the company did: 0 is the same, and a larger number is further away. The line around the dot is the range the true distance likely falls in. Past the marked rule, a goal is no good match.",
  distanceAxis: "Distance from the company’s decision, 0 to 1",
  distanceRule: (distance: string) => `no good match above ${distance}`,
  distanceRowNumbers: (distance: string, low: string, high: string) =>
    `distance ${distance}, interval ${low} to ${high}`,
  distanceRuns: (runs: number, choiceOnly: number, undistanced: number) =>
    `${runs} runs measured, ${choiceOnly} on the choice alone, ${undistanced} left out`,
  distanceChartLabel: (caseLabel: string, model: string, reading: string) =>
    `Distances for ${caseLabel}, ${model}, ${reading}`,
  distanceLevel: (level: string) => `${level} range, from resampling the runs (a bootstrap interval)`,
  nearestLine: (goal: string, letter: string) => `Nearest goal: ${goal} (${letter})`,
  gapLine: (second: string, estimate: string, low: string, high: string) =>
    `Gap to the next nearest, goal ${second}: ${estimate} (interval ${low} to ${high})`,
  tiedWith: (ids: string) => `Tied with: ${ids}`,
  tieNote:
    "Every goal is the same distance from the company’s decision in this reading. The matching program then picks the earliest letter, but that is a tie-break, not a finding, so no nearest goal is shown.",
  oneLineNote:
    "Only one line of the company’s decision could be seen in this reading. The distance still averages that line with the choice itself (close, retool or sell), which pulls every goal toward a match just from how it is worked out. These distances cannot be compared with other cases’ readings.",
  dependsLabel: "Depends on the reading",
  dependsYes: "yes",
  dependsNo: "no",
  dependsTieNote:
    "This answer comes from the tie-break in a reading where every goal is the same distance away. On its own, it does not mean that how the company’s decision was read changes the result.",
  dependsSameLabel: (label: string) => `The label is ${label} under every reading.`,
  alternativesLine: (matched: number, unmatched: string) =>
    `Alternative readings matched: ${matched}. Calls left unmatched: ${unmatched}.`,
  caseMemosHeading: "Memos",
  caseMemosNone: "no real-case memo text is on this site, and none is linked",
  memoCountLabels: {
    runs: "Runs",
    with_text: "With text",
    without_text: "Without text",
    published: "Published",
    held: "Held",
  } as Record<string, string>,
  heldReasonsHeading: "Held, by reason",
  heldReasons: {
    name_confirmed: "a name was confirmed in the memo",
    reader_unclear: "a reader could not tell whether the memo names the company",
    reader_no_reply: "the reader gave no reply",
    dossier_withheld: "the memo repeats words from the case’s withheld dossier",
    overruled: "held by a later decision",
  } as Record<string, string>,
  caseLoading: "Loading the case",
  casesLoading: "Loading the cases",
  caseSeeCase: "Read the case",

  // The studies.
  studiesSubStudyLabel:
    "A sub-study on scenario s1, on Haiku 5.5 only. It is not one of the 16 main comparisons and is not part of the main grid.",
  studiesSettings:
    "Settings: all five goals, each in wording w2 only (the wording locked in before the runs), with the model\u2019s step-by-step thinking turned on at high effort. The exact request is in protocol section 9.5.",
  studiesSettingsLink: "Protocol section 9.5, at the pre-registered tag",
  studiesGridCard: "Main grid, scenario s1, wording w2 only",
  studiesThinkingCard: "Thinking sub-study, scenario s1, wording w2",
  studiesGridNote:
    "The scenario view shows the grid’s three wordings; here the grid is cut to w2, so it sits like for like beside the sub-study.",
  studiesLevel: (level: string) => `Each verdict uses the analysis’s ${level} interval.`,
  studiesComparisonsHeading: "The five comparisons in the sub-study",
  studiesGridSealed: (wording: string, verdict: string) =>
    `The main grid on wording ${wording} alone, also not one of the 16 main comparisons: ${verdict}`,
  studiesMemosLink: "Read the sub-study’s memos",
  studiesRunsHeading: "Every run of the sub-study",
  studiesRunsKey: "Each run id opens that run’s memo in the reader.",
  awarenessLabel:
    "Context only. Every reply is quoted in full and none is used to filter or weight any run (protocol section 9.6).",
  awarenessInstructionLabel:
    "The instruction the model was given in place of the decision, word for word from protocol section 9.6:",
  awarenessSettings:
    "One call for each of the five goals under each of three phrasings of the question (templates), 15 to a model, on scenario s1.",
  awarenessLink: "Protocol section 9.6, at the pre-registered tag",
  awarenessGoalHeading: (goal: string, letter: string) => `${goal} (${letter})`,
  awarenessCardLabel: (model: string, letter: string, goal: string, template: string) =>
    `A reply to the awareness probe, not a decision memo. Written by ${model} under goal ${letter} (${goal}), template ${template}.`,
  awarenessStatus: (status: string, stop: string, tokens: number) =>
    `status ${status}, stop reason ${stop}, ${tokens} output tokens`,
  awarenessNotRecorded: "This call was not recorded.",
  awarenessEmpty: "The reply had no text.",
  studiesLoading: "Loading the studies",

  // ------------------------------------------------------------------------------------------------------------
  // C6: the guided story. Claude-drafted; approved by him in the words pass of 2026-11-11 (Phase 6 IMPLEMENTATION doc
  // section 11, fourth dated note). Each label describes what a part shows; none states a result.
  storyRoundtableOverview: "Who the Business Roundtable is (Wikipedia)",
  storyRoundtableClaim: "The claim in the Roundtable\u2019s own words (its 2024 statement)",
  storyPairHeading: (firstName: string, first: string, secondName: string, second: string) =>
    `${firstName} (${first}) vs ${secondName} (${second})`,
  storyOpenScenario: (id: string, model: string) => `Open scenario ${id} on ${model}, with every detail`,
  storyTableCaption: (id: string) => `Scenario ${id}: every verdict, for each model`,
  storyComparisonColumn: "Comparison",
  storyLabelVaries: "differs by reading; see the case",
  storyAllCases: "All the real cases, in full",
  storyProtocolLink: "The protocol, fixed before the runs (on GitHub)",
  storyStudiesLink: "The side studies",
  storyMemosLink: "Read the memos the models wrote",
};

/**
 * C7: the share cards' labels (Phase 6 IMPLEMENTATION doc section 10; section 29 lists them). CLAUDE-DRAFTED AND NOT YET
 * APPROVED: they wait for the words pass after Opus's review. Each describes what a card or a link preview shows; none
 * states a result, and none holds a ratio. The cards also use labels of `explorerLabels` (`allNoGoodMatch`,
 * `capValidOfAttempted`, `roundtableFlag`, `storyPairHeading`, `readingLabelIs`, `storyLabelVaries`, `verdictWords`,
 * `objectiveNames`, `readingLabels`, `caseDescriptionStatus`) and his words, unchanged.
 *
 * A separate export, not more keys of `explorerLabels`, so that no view imports it and the bundler leaves it out: the
 * explorer's JavaScript is the same size as before C7 (the build's check-dist lines show it), and nothing a page loads
 * changes. Only the build (cards.ts, write-paths.mjs) reads it.
 */
export const explorerCardLabels = {
  cardName: "Horizon Compact",
  cardTwoModels: (first: string, second: string) => `Two models: ${first} and ${second}`,
  cardMemoLabel:
    "Written by a model under one goal, for a fictional company. This is the model\u2019s output, not the project\u2019s view.",
  // The alternative text of each kind of page's link-preview image (og:image:alt).
  cardAlt: {
    story:
      "A card for the project\u2019s front page: its name, its question, the two models it tests, and what it does not measure. It shows no result.",
    scenario:
      "A card for one company decision: the scenario in brief, how many valid runs each of the two models made, and the study\u2019s verdict for each comparison, side by side. The verdicts are the study\u2019s own.",
    cases:
      "A card for the real cases: how they were chosen, and what each model\u2019s reading of every case was. It names no company.",
    case: "A card for one real case: how it was chosen, its short description with the company\u2019s name removed, and what each model\u2019s reading of it was.",
    studies:
      "A card for the two side studies: what they ask, and what the study measures and does not. It shows no result.",
    memos:
      "A card for the memo reader: what a memo is, and that it is the model\u2019s own writing and not the project\u2019s view. It shows no memo text.",
  } as Record<string, string>,
};
