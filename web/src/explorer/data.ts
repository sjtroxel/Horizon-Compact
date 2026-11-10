/**
 * Loaders for the explorer's data (Phase 6 IMPLEMENTATION doc section 6, C3 decision 4). Each is a `fetch` of a file
 * under `/data/` on the site's own origin (the content security policy's `connect-src 'self'`), at a path taken from
 * the index's `files` block, never from a list written here. They reshape nothing and compute nothing: no mean, no
 * interval, no rounding (section 5's rule). What comes back is the parsed JSON, as the builder wrote it.
 *
 * The types cover what the shell and C4 read, from the real files. A field no view reads yet is `unknown`; the step
 * that first reads it types it.
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

export interface Comparison {
  first: string;
  second: string;
  role: "primary" | "secondary";
  label: string;
  outcome: string;
  difference: number | null;
  low: number | null;
  high: number | null;
  /** One entry per wording: its id, the runs attempted and the runs valid, as the builder wrote them. */
  valid_runs: Array<[string, number, number]>;
  kept_wordings: string[];
  dropped_wordings: DroppedWording[];
  final_verdict: Verdict;
  downgrade_reason: string | null;
  headline: string;
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
  clause: string;
  roundtable_pair: boolean;
  difference: number | null;
  low: number | null;
  high: number | null;
  valid_runs: Array<[string, number, number]>;
  kept_wordings: string[];
  dropped_wordings: DroppedWording[];
  final_verdict: Verdict;
  headline: string;
}

export interface AgainstThesis {
  rule: string;
  entries: AgainstThesisEntry[];
  scenarios: unknown[];
}

export interface DataFiles {
  /** model key, then scenario id, to a path relative to /data/. */
  grid: Record<string, Record<string, string>>;
  thinking: Record<string, Record<string, string>>;
  /** The cases index's path. */
  cases: string;
  /** case label, then model key, to a path. */
  case_results: Record<string, Record<string, string>>;
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

/** One scenario's file for one model: the grid's, or the thinking sub-study's (same shape). */
export interface GridFile {
  model_key: string;
  sweep_id: string;
  scenario_id: string;
  primary_outcome: string;
  kind: ScenarioEntry["kind"];
  threshold: number;
  comparisons: Comparison[];
  cells: unknown[];
  objective_rates: unknown[];
  pair_rates: unknown[];
  position: unknown;
  descriptive: unknown;
}

export interface CaseEntry {
  label: string;
  type: string;
  shape: string;
  exploratory: boolean;
  exploratory_label: string;
  description: unknown;
  dossier: unknown;
  reidentification: unknown;
  probes: unknown;
}

export interface CasesIndex {
  shortfall: unknown;
  provenance: unknown;
  cases: CaseEntry[];
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
  thresholds: unknown;
  dimensions: unknown;
  company: unknown;
  company_alternatives: unknown[];
  readings: unknown[];
  alternative_readings: unknown;
  depends_on_reading: boolean;
  provenance: unknown;
}

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

export interface DataApi {
  loadIndex(): Promise<DataIndex>;
  loadGrid(model: string, scenario: string): Promise<GridFile>;
  /** Every thinking sub-study file the index lists, one per model and scenario (today, one). */
  loadThinking(): Promise<GridFile[]>;
  loadCasesIndex(): Promise<CasesIndex>;
  loadCase(label: string, model: string): Promise<CaseFile>;
}

/** The loaders over a fetch function; tests pass one that serves fixtures. The index is fetched once. */
export function createDataApi(fetcher: Fetcher = (path) => fetch(path)): DataApi {
  async function getJson<T>(path: string): Promise<T> {
    const response = await fetcher(path);
    if (!response.ok) throw new Error(`explorer data: ${path} answered ${response.status}`);
    return (await response.json()) as T;
  }

  let index: Promise<DataIndex> | null = null;
  function loadIndex(): Promise<DataIndex> {
    if (index === null) {
      index = getJson<DataIndex>(INDEX_PATH);
      index.catch(() => {
        index = null; // a failed load is tried again, not remembered
      });
    }
    return index;
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
  };
}

export const defaultData: DataApi = createDataApi();
export const { loadIndex, loadGrid, loadThinking, loadCasesIndex, loadCase } = defaultData;
