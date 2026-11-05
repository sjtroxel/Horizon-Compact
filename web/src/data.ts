import raw from "./data/placeholder.json";

// The statuses a call can end in, in the order of `Status` in src/horizon_compact/sweep/classify.py (a Python test
// holds the two lists equal). Valid first; each is shown even at zero.
export const STATUSES = [
  "valid",
  "valid_rescaled",
  "refusal",
  "truncated",
  "malformed_tool_use",
  "no_tool_call",
  "multiple_calls",
  "schema_invalid",
  "sum_mismatch",
  "unexpected_stop",
  "api_error",
  "config_error",
] as const;

export interface Line {
  key: string;
  label: string;
  kind: "source" | "use";
  cap: number;
}

export interface Run {
  run_id: string;
  objective_id: string;
  repeat: number;
  status: string;
  attempts: number;
  amounts: Record<string, number>;
  choice: string;
  image_digest: string;
}

export interface Cell {
  objective_id: string;
  runs: number;
  valid: number;
  status_counts: Record<string, number>;
  first_attempt_status_counts: Record<string, number>;
  lines: Record<string, { mean: number | null; min: number | null; max: number | null }>;
  choice_counts: Record<string, number>;
}

export interface Sweep {
  sweep_id: string;
  experiment: string;
  role: string;
  served_models: string[];
  runs_planned: number;
  runs_finished: number;
  cost_usd: number;
  image_digests: string[];
  git_shas: string[];
  content_hashes: string[];
  runners: string[];
  started_at: string;
  finished_at: string;
}

export interface SiteData {
  schema: string;
  schema_version: number;
  kind: string;
  content: string;
  sweep: Sweep;
  scenario: { id: string; total: number; lines: Line[] };
  cells: Cell[];
  runs: Run[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * The page refuses to build from anything but the labeled placeholder test run (Phase 1.5 IMPLEMENTATION doc
 * section 0 item 4 and section 16): a wrong schema, version, kind, content or role throws, and so does a shape
 * the page could not draw. Official and case results never reach this page.
 */
export function parseSiteData(value: unknown): SiteData {
  if (!isRecord(value)) throw new Error("site data: not an object");
  if (value["schema"] !== "horizon-compact/site-placeholder") {
    throw new Error(
      `site data: schema is ${JSON.stringify(value["schema"])}, not horizon-compact/site-placeholder`,
    );
  }
  if (value["schema_version"] !== 1) throw new Error("site data: schema_version is not 1");
  if (value["kind"] !== "test-run") throw new Error("site data: kind is not test-run");
  if (value["content"] !== "placeholder") throw new Error("site data: content is not placeholder");
  const sweep = value["sweep"];
  if (!isRecord(sweep) || sweep["role"] !== "development") {
    throw new Error("site data: sweep.role is not development");
  }
  if (sweep["experiment"] !== "placeholder")
    throw new Error("site data: sweep.experiment is not placeholder");
  const scenario = value["scenario"];
  if (!isRecord(scenario) || !Array.isArray(scenario["lines"]) || scenario["lines"].length === 0) {
    throw new Error("site data: scenario.lines is missing");
  }
  if (!Array.isArray(value["cells"]) || value["cells"].length === 0) {
    throw new Error("site data: cells is missing");
  }
  if (!Array.isArray(value["runs"]) || value["runs"].length === 0) {
    throw new Error("site data: runs is missing");
  }
  const data = value as unknown as SiteData;
  for (const run of data.runs) {
    for (const line of data.scenario.lines) {
      if (typeof run.amounts[line.key] !== "number") {
        throw new Error(`site data: run ${run.run_id} has no amount for ${line.key}`);
      }
    }
  }
  return data;
}

export const data: SiteData = parseSiteData(raw);

/** The scale every panel shares: $0 up to the largest cap. */
export const AXIS_MAX = Math.max(...data.scenario.lines.map((line) => line.cap));
export const TICKS = [0, 250, 500, 750, 1000] as const;

/** Whole dollars, thousands separated: the page never shows cents. */
export function money(value: number): string {
  return `$${Math.round(value).toLocaleString("en-US")}`;
}

export function percent(value: number): string {
  return `${((100 * value) / AXIS_MAX).toFixed(3)}%`;
}
