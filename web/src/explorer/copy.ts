/**
 * Every word the explorer shows lives here or in his.json, except data values and the name "Horizon Compact".
 *
 * BOTH OBJECTS ARE UNAPPROVED. `explorerHis` is a set of marked placeholders (`[his: ...]`) naming what he writes;
 * `explorerLabels` is Claude-drafted and unapproved until the Phase 6 IMPLEMENTATION doc section 14, step 8, where he
 * approves it word for word. The gate that fails on an unwritten explorer word is Phase 6.5's go-live, not this
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

export interface ExplorerHis {
  landingQuestion: string;
  scopeSentence: string;
  /** The scenario in brief, per scenario id: his words, a placeholder until he writes them. */
  scenarioBriefs: Record<string, string>;
  /** The section for results against the thesis: his title and his introductory sentence. */
  againstTitle: string;
  againstIntro: string;
  pages: Pages;
}

export const explorerHis: ExplorerHis = hisJson;

export const explorerLabels = {
  skipToContent: "Skip to the content",
  navLabel: "Sections",
  navStory: "The story",
  navScenario: (id: string) => `Scenario ${id}`,
  navCases: "Real cases",
  navStudies: "Studies",
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
    `Each verdict is the analysis\u2019s own, at the ${level} confidence level (a Bonferroni correction over the family of 16 comparisons). The interval behind each one is in the details.`,
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
  noReading: "The protocol wrote no reading for this pair.",
  readingsNote:
    "Before the results, the protocol wrote down what some outcomes would mean, for C vs D and for A vs B only. Where one applies, it is quoted under that sentence; the other sentences have none.",
  protocolReadingLabel: "The protocol\u2019s reading, written before the results:",
  repeatsLine:
    "How many repeats each cell got was set by protocol section 8.2 from each model\u2019s pilot, before the grid ran.",
  againstLink: "See the results that go against the thesis",
  againstMarker: "listed in the section for results against the thesis",

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
};
