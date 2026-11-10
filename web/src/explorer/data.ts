/**
 * Loaders for the explorer's data (Phase 6 IMPLEMENTATION doc section 6, C3 decision 4). Each is a `fetch` of a file
 * under `/data/` on the site's own origin (the content security policy's `connect-src 'self'`), at a path taken from
 * the index's `files` block, never from a list written here. They reshape nothing and compute nothing: no mean, no
 * interval, no rounding (section 5's rule). What comes back is the parsed JSON, as the builder wrote it. A file once
 * fetched is kept in memory by its path, so switching back to a model or a scenario does not fetch it again.
 *
 * The types cover what the shell, C4 and the views read, from the real files. A field no view reads yet is
 * `unknown`; the step that first reads it types it.
 */

export interface ModelEntry {
  model_key: string;
  sweep_id: string;
  alpha: number;
  descriptive_alpha: number;
  sealed_wording: string;
}

export interface Objective {
  id: string;
  who: string;
  when: string;
}

export interface ScenarioEntry {
  scenario_id: string;
  primary_outcome: string;
  kind: "share" | "choice_rate";
  threshold: number;
}

export type Verdict = "split" | "no_split" | "inconclusive" | "not_assessable";

export interface DroppedWording {
  wording_id: string;
  cells: Array<{ objective_id: string; unsuccessful: number; attempted: number }>;
}

/**
 * One entry per kept wording: `[wording_id, valid runs of the first objective, valid runs of the second]`. Not
 * "attempted and valid": the two numbers are the two sides of the comparison. A comparison that is not assessable
 * has none.
 */
export type ValidRuns = Array<[string, number, number]>;

export interface Comparison {
  first: string;
  second: string;
  role: "primary" | "secondary";
  label: string;
  outcome: string;
  difference: number | null;
  low: number | null;
  high: number | null;
  valid_runs: ValidRuns;
  kept_wordings: string[];
  dropped_wordings: DroppedWording[];
  final_verdict: Verdict;
  downgrade_reason: string | null;
  headline: string;
}

export interface PerWording {
  wording_id: string;
  first_value: number;
  second_value: number;
  n_first: number;
  n_second: number;
  difference: number;
  direction: string;
}

/** The sealed wording's own result, outside the family of 16. */
export interface SealedBlock {
  label: string;
  sealed_wording: string;
  final_verdict: Verdict;
  difference: number | null;
  low: number | null;
  high: number | null;
  relation: string;
  relation_reason: string;
}

/** The result before any wording was dropped for failures. Its dropped wordings are bare ids. */
export interface FirstAttempt {
  final_verdict: Verdict;
  difference: number | null;
  low: number | null;
  high: number | null;
  kept_wordings: string[];
  dropped_wordings: string[];
}

/** A comparison as a grid file carries it: the index's fields and the ones the details need. */
export interface GridComparison extends Comparison {
  scenario_id: string;
  kind: ScenarioEntry["kind"];
  threshold: number;
  method: string | null;
  alpha: number;
  per_wording: PerWording[];
  sealed: SealedBlock;
  first_attempt: FirstAttempt;
}

export interface VerdictBlock {
  model_key: string;
  sweep_id: string;
  scenario_id: string;
  comparisons: Comparison[];
}

export interface AgainstThesisEntry {
  model_key: string;
  sweep_id: string;
  scenario_id: string;
  first: string;
  second: string;
  /** Which clause of the rule listed it: a "no split", or a split in the direction the thesis did not expect. */
  clause: "no_split" | "reversed_split";
  roundtable_pair: boolean;
  difference: number | null;
  low: number | null;
  high: number | null;
  valid_runs: ValidRuns;
  kept_wordings: string[];
  dropped_wordings: DroppedWording[];
  final_verdict: Verdict;
  headline: string;
}

export interface AgainstThesis {
  rule: string;
  entries: AgainstThesisEntry[];
  /** Scenarios on which every primary comparison of a model is "no split". Empty today. */
  scenarios: Array<{ model_key: string; scenario_id: string }>;
}

export interface DataFiles {
  /** model key, then scenario id, to a path relative to /data/. */
  grid: Record<string, Record<string, string>>;
  thinking: Record<string, Record<string, string>>;
  /** The cases index's path. */
  cases: string;
  /** case label, then model key, to a path. */
  case_results: Record<string, Record<string, string>>;
  /** model key to the awareness probe's file (protocol 9.6). */
  awareness: Record<string, string>;
}

export interface DataIndex {
  explorer_data_version: number;
  sources: Array<{ path: string; sha256: string }>;
  models: ModelEntry[];
  objectives: Objective[];
  scenarios: ScenarioEntry[];
  verdicts: VerdictBlock[];
  against_thesis: AgainstThesis;
  files: DataFiles;
}

/** One cell of the grid: one goal under one wording, with every status counted (zero included). */
export interface CellStatus {
  model_key: string;
  scenario_id: string;
  objective_id: string;
  wording_id: string;
  attempted: number;
  valid: number;
  rescaled: number;
  refused: number;
  /** `[failure type, runs]`; empty when none failed. The types are the file's own words. */
  failed_by_type: Array<[string, number]>;
}

/** Runs attempted for one goal, over every wording of the scenario. */
export interface ObjectiveRate {
  objective_id: string;
  attempted: number;
  failed: number;
  refused: number;
}

export interface SummaryStats {
  n: number;
  mean: number;
  sd: number | null;
  median: number;
  minimum: number;
  maximum: number;
}

export interface LineSummary {
  key: string;
  kind: string;
  summary: SummaryStats;
}

/**
 * A descriptive cell. With `wording_id` and `choice` both null it is one goal over every wording kept in the file:
 * `runs` is the goal's count in the chart, and `lines` are its levers in canonical order.
 */
export interface DescriptiveCell {
  objective_id: string;
  wording_id: string | null;
  choice: string | null;
  runs: number;
  lines: LineSummary[];
  groups: unknown[];
}

/** For a choice scenario: how many runs of a goal (and wording, or all wordings when null) made each choice. */
export interface ChoiceSplit {
  objective_id: string;
  wording_id: string | null;
  runs: number;
  counts: Array<[string, number]>;
}

/** One valid run. `primary` is the scenario's primary outcome; `choice` is null on a share scenario. */
export interface PerRun {
  run_id: string;
  objective_id: string;
  wording_id: string;
  repeat: number;
  choice: string | null;
  primary: number;
  /** `[lever key, share]`, in the lever order of the scenario. */
  shares: Array<[string, number]>;
  secondary: unknown;
}

export interface Descriptive {
  scenario_id: string;
  /** Valid runs in the file. */
  runs: number;
  cells: DescriptiveCell[];
  choice_splits: ChoiceSplit[];
  secondaries: unknown;
  distances: unknown;
  per_run: PerRun[];
}

/** One scenario's file for one model: the grid's, or the thinking sub-study's (same shape). */
export interface GridFile {
  model_key: string;
  sweep_id: string;
  scenario_id: string;
  primary_outcome: string;
  kind: ScenarioEntry["kind"];
  threshold: number;
  comparisons: GridComparison[];
  cells: CellStatus[];
  objective_rates: ObjectiveRate[];
  pair_rates: unknown;
  position: unknown;
  descriptive: Descriptive;
}

/** What the case's coarse description says; `text` only when it is published. */
export interface CaseDescription {
  status: string;
  text?: string;
  reason?: string;
}

export interface CaseProbe {
  set: number;
  model: string;
  calls: number;
  passed: number;
}

export interface CaseEntry {
  label: string;
  type: string;
  shape: string;
  exploratory: boolean;
  /** The label as the file writes it; shown verbatim, first, wherever the case appears. */
  exploratory_label: string;
  description: CaseDescription;
  dossier: { published: boolean; reason: string };
  reidentification: { status: string; reason: string; threshold: number };
  probes: CaseProbe[];
}

/** The shortfall block of `cases.json` (protocol 12.1): copied, never derived. */
export interface Shortfall {
  at_most: number;
  cases: number;
  cases_by_type: Record<string, number>;
  short_by_type: Record<string, number>;
  filled: number;
}

export interface CasesIndex {
  shortfall: Shortfall;
  provenance: unknown;
  cases: CaseEntry[];
}

/** One goal's distance from the company in one reading: the dot, its interval, and the runs behind it. */
export interface CaseDistance {
  objective_id: string;
  distance: number;
  low: number;
  high: number;
  seed: string;
  runs: number;
  choice_only_runs: number;
  undistanced_runs: number;
}

export interface CaseGap {
  nearest: string;
  second: string;
  estimate: number;
  low: number;
  high: number;
  seed: string;
}

/** One reading of a case (the rubric's primary reading, or an alternative): the matcher's output, plus two notes
 * the builder derives from copied values (KNOWN-GAPS OPEN 2026-10-31). */
export interface CaseReading {
  reading: string;
  observable_lines: string[];
  choice_observable: boolean;
  dimensions: number;
  company_basis: string;
  /** The matcher's label: match, tie, no_good_match or not_enough_disclosed. */
  label: string;
  reason: string;
  nearest: string | null;
  tied_with: string | string[] | null;
  gap: CaseGap | null;
  distances: CaseDistance[];
  /** True when all five distances (and their intervals) are equal: the nearest goal is then a tie-break by letter. */
  all_distances_equal: boolean;
  /** True when the reading has one observable line, which the distance still averages with the choice term. */
  one_observable_line: boolean;
}

export interface CompanyReading {
  reading: string;
  choice: string;
  shares: Record<string, number>;
}

/** The six count fields of a case's memo summary (decision 5: counts, never text). */
export interface MemoCounts {
  runs: number;
  with_text: number;
  without_text: number;
  published: number;
  held: number;
  held_by_reason: Record<string, number>;
}

/** One case's results for one model. */
export interface CaseFile {
  results_version: number;
  case: string;
  type: string;
  exploratory: boolean;
  exploratory_label: string;
  experiment: string;
  scenario_id: string;
  model_key: string;
  sweep_id: string;
  run_counts: { runs: number; by_final_status: Record<string, number> };
  thresholds: { d_star: number; k_star: number; alpha: number; resamples: number };
  dimensions: { observable: string[]; excluded: string[] };
  company: CompanyReading;
  company_alternatives: CompanyReading[];
  readings: CaseReading[];
  alternative_readings: { matched: number; unmatched_calls: unknown[] };
  depends_on_reading: boolean;
  provenance: unknown;
  memo_counts: MemoCounts;
}

/** One call of the awareness probe (protocol 9.6): fifteen to a model, five goals by three templates. */
export type AwarenessCall =
  | { objective_id: string; template_id: string; recorded: false }
  | {
      objective_id: string;
      template_id: string;
      recorded: true;
      status: string;
      stop_reason: string;
      output_tokens: number;
      /** The reply exactly as the report has it; "(no text)" when the reply had none, flagged by `empty_reply`. */
      reply: string;
      empty_reply: boolean;
    };

export interface AwarenessFile {
  model_key: string;
  sweep_id: string;
  experiment: string;
  content_hash: string;
  scenario: string;
  seed: number;
  calls_recorded: number;
  calls_total: number;
  calls: AwarenessCall[];
}

/** A pointer to the source record a memo was read from, so a reader can check it against the raw-object manifest. */
export interface SourceRecord {
  key: string;
  sha256: string;
}

/** One row of the memo extract. `memo` is null for a run that left no text. */
export interface MemoRow {
  run_id: string;
  wording_id: string;
  repeat: number;
  status: string;
  /** `memo`: the memo field of the model's first tool call; `reply_text`: its text, when it made no tool call. */
  source: "memo" | "reply_text" | null;
  memo: string | null;
  final: SourceRecord;
  attempt: SourceRecord;
}

export interface MemoSweep {
  kind: string;
  model_key: string;
  sweep_id: string;
  prefix: string;
  runs: number;
  with_text: number;
  by_status: Record<string, number>;
}

export interface MemoIndex {
  explorer_memos_version: number;
  head: string;
  raw_manifest: { path: string; sha256: string };
  sweeps: MemoSweep[];
  /** Every file of the extract, relative to /data/memos/, in order. */
  files: string[];
}

/** The rows of one cell (a kind, a model, a scenario and a goal), or that the index lists no such cell. */
export type MemoCell = { found: true; rows: MemoRow[]; paths: string[] } | { found: false };

const DATA_ROOT = "/data/";
const INDEX_PATH = `${DATA_ROOT}index.json`;

/**
 * A path from the index's `files` block, made into a path under /data/. A path that is absolute, names another host,
 * climbs out with `..` or holds a backslash is refused: the data is only ever read from /data/ on this origin.
 */
export function dataPath(relative: string): string {
  const refused =
    relative === "" ||
    relative.startsWith("/") ||
    relative.includes("\\") ||
    /^[a-z][a-z0-9+.-]*:/i.test(relative) ||
    relative.split("/").some((segment) => segment === ".." || segment === "." || segment === "");
  if (refused)
    throw new Error(`explorer data: refusing the path "${relative}", it is not under ${DATA_ROOT}`);
  return `${DATA_ROOT}${relative}`;
}

type Fetcher = (path: string) => Promise<Response>;

/** Where the memo extract lives under /data/ (the build copies web/explorer-memos/ there). */
export const MEMOS_ROOT = "memos/";

/**
 * Which cell a memo file belongs to, from its path in the index's `files`: `<kind>/<model>/<scenario>/<goal>.jsonl`,
 * or `<goal>-<wording>.jsonl` when a cell was split by wording (Phase 6 doc section 23). Null for a path of any
 * other shape.
 */
export function memoPathCell(
  path: string,
): { kind: string; model: string; scenario: string; objective: string } | null {
  const parts = path.split("/");
  if (parts.length !== 4) return null;
  const [kind, model, scenario, file] = parts as [string, string, string, string];
  const found = /^([A-Z])(?:-[a-z0-9]+)?\.jsonl$/.exec(file);
  return found === null ? null : { kind, model, scenario, objective: found[1]! };
}

export interface DataApi {
  loadIndex(): Promise<DataIndex>;
  loadGrid(model: string, scenario: string): Promise<GridFile>;
  /** Every thinking sub-study file the index lists, one per model and scenario (today, one). */
  loadThinking(): Promise<GridFile[]>;
  loadCasesIndex(): Promise<CasesIndex>;
  loadCase(label: string, model: string): Promise<CaseFile>;
  /** The memo extract's index (`/data/memos/index.json`). */
  loadMemoIndex(): Promise<MemoIndex>;
  /** A cell's rows in file order, from the files the memo index lists for it; `found: false` when it lists none. */
  loadMemos(kind: string, model: string, scenario: string, objective: string): Promise<MemoCell>;
  /** One model's awareness probe (protocol 9.6). */
  loadAwareness(model: string): Promise<AwarenessFile>;
}

/** The loaders over a fetch function; tests pass one that serves fixtures. Each file is fetched once. */
export function createDataApi(fetcher: Fetcher = (path) => fetch(path)): DataApi {
  // One fetch per path, kept for the life of the page. A failed fetch is forgotten, so the next ask tries again.
  const cache = new Map<string, Promise<unknown>>();
  function getJson<T>(path: string): Promise<T> {
    const kept = cache.get(path);
    if (kept !== undefined) return kept as Promise<T>;
    const loading = (async () => {
      const response = await fetcher(path);
      if (!response.ok) throw new Error(`explorer data: ${path} answered ${response.status}`);
      return (await response.json()) as T;
    })();
    cache.set(path, loading);
    loading.catch(() => {
      if (cache.get(path) === loading) cache.delete(path);
    });
    return loading;
  }

  function loadIndex(): Promise<DataIndex> {
    return getJson<DataIndex>(INDEX_PATH);
  }

  // JSON Lines: one object a line, kept by path like any other file. The rows come back in the file's order.
  function getRows<T>(path: string): Promise<T[]> {
    const key = `rows:${path}`;
    const kept = cache.get(key);
    if (kept !== undefined) return kept as Promise<T[]>;
    const loading = (async () => {
      const response = await fetcher(path);
      if (!response.ok) throw new Error(`explorer data: ${path} answered ${response.status}`);
      const text = await response.text();
      return text
        .split("\n")
        .filter((line) => line.trim() !== "")
        .map((line) => JSON.parse(line) as T);
    })();
    cache.set(key, loading);
    loading.catch(() => {
      if (cache.get(key) === loading) cache.delete(key);
    });
    return loading;
  }

  function loadMemoIndex(): Promise<MemoIndex> {
    return getJson<MemoIndex>(`${DATA_ROOT}${MEMOS_ROOT}index.json`);
  }

  async function fromFiles<T>(describe: string, pick: (files: DataFiles) => string | undefined): Promise<T> {
    const { files } = await loadIndex();
    const relative = pick(files);
    if (relative === undefined) throw new Error(`explorer data: the index lists no file for ${describe}`);
    return getJson<T>(dataPath(relative));
  }

  return {
    loadIndex,
    loadGrid: (model, scenario) =>
      fromFiles(`grid ${model} ${scenario}`, (files) => files.grid[model]?.[scenario]),
    async loadThinking() {
      const { files } = await loadIndex();
      const relatives = Object.values(files.thinking).flatMap((byScenario) => Object.values(byScenario));
      return Promise.all(relatives.map((relative) => getJson<GridFile>(dataPath(relative))));
    },
    loadCasesIndex: () => fromFiles("the cases index", (files) => files.cases),
    loadCase: (label, model) =>
      fromFiles(`case ${label} ${model}`, (files) => files.case_results[label]?.[model]),
    loadMemoIndex,
    async loadMemos(kind, model, scenario, objective) {
      const { files } = await loadMemoIndex();
      // The cell's files are read from the index's list, never built from the names alone.
      const paths = files.filter((path) => {
        const cell = memoPathCell(path);
        return (
          cell !== null &&
          cell.kind === kind &&
          cell.model === model &&
          cell.scenario === scenario &&
          cell.objective === objective
        );
      });
      if (paths.length === 0) return { found: false };
      const parts = await Promise.all(
        paths.map((path) => getRows<MemoRow>(dataPath(`${MEMOS_ROOT}${path}`))),
      );
      return { found: true, rows: parts.flat(), paths };
    },
    loadAwareness: (model) => fromFiles(`awareness ${model}`, (files) => files.awareness[model]),
  };
}

export const defaultData: DataApi = createDataApi();
export const {
  loadIndex,
  loadGrid,
  loadThinking,
  loadCasesIndex,
  loadCase,
  loadMemoIndex,
  loadMemos,
  loadAwareness,
} = defaultData;
