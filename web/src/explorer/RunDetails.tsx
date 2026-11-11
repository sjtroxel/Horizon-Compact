/**
 * Two pieces the scenario view and the studies share, moved out of ScenarioView.tsx in C6 part B so that the studies
 * path no longer loads the scenario view's chunk (Phase 6 IMPLEMENTATION doc section 28a, carried point 1): the
 * closed "See the details" section and the table of every run.
 *
 * Nothing here computes a number. Every figure is a field of the grid file, shown through format.ts.
 */
import { useState } from "react";
import type { ReactNode } from "react";
import type { Names } from "./charts";
import { explorerLabels as L } from "./copy";
import type { GridFile } from "./data";
import { formatPercent } from "./format";
import { memoHref } from "./route";

const names: Names = L.objectiveNames;

/** A `details` element closed by default whose content is built only once it is opened (the allocation panels and
 * the run table are thousands of nodes, and a closed section shows none of them). */
export function Details({ summary, hint, children }: { summary: string; hint: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <details className="x-details" onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>
        <span className="x-summary-title">{summary}</span>
        <span className="muted"> &middot; {hint}</span>
      </summary>
      {open && <div className="x-details-body">{children}</div>}
    </details>
  );
}

/**
 * Every valid run of the file as a table. Each run id is a link to that run's memo in the reader (`kind` says which
 * set of memos: the main grid's, or the thinking sub-study's), on the file's own model.
 */
export function RunsTable({ file, kind }: { file: GridFile; kind: "grid" | "thinking" }) {
  return (
    <div className="x-table-wrap" role="region" aria-label={L.runsHeading} tabIndex={0}>
      <table className="x-table">
        <thead>
          <tr>
            <th scope="col">{L.th.runId}</th>
            <th scope="col">{L.th.goal}</th>
            <th scope="col">{L.th.wording}</th>
            <th scope="col" className="num">
              {L.th.repeat}
            </th>
            <th scope="col">{L.th.value}</th>
          </tr>
        </thead>
        <tbody>
          {file.descriptive.per_run.map((run) => (
            <tr key={run.run_id}>
              <th scope="row" className="mono">
                <a
                  href={memoHref(
                    { kind, scenario: file.scenario_id, objective: run.objective_id, run: run.run_id },
                    file.model_key,
                  )}
                >
                  {run.run_id}
                </a>
              </th>
              <td>
                {names[run.objective_id] ?? run.objective_id} ({run.objective_id})
              </td>
              <td>{run.wording_id}</td>
              <td className="num">{run.repeat}</td>
              <td>
                {run.choice === null ? formatPercent(run.primary) : (L.choices[run.choice] ?? run.choice)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
