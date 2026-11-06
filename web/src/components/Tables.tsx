import { labels } from "../copy";
import { STATUSES, data, money } from "../data";

/** How each run's call ended, on its first attempt and on its final one, by priority. Zero rows stay, in grey. */
export function StatusTable() {
  const cells = data.cells;
  return (
    <div className="frame" role="region" aria-label={labels.statusTableLabel} tabIndex={0}>
      <table className="status">
        <thead>
          <tr>
            <th rowSpan={2}>{labels.statusHeading}</th>
            {cells.map((c) => (
              <th key={c.objective_id} colSpan={2} className="pri">
                {labels.priorities[c.objective_id] ?? c.objective_id}
              </th>
            ))}
          </tr>
          <tr>
            {cells.flatMap((c) => [
              <th key={`${c.objective_id}-first`} className="sub">
                {labels.first}
              </th>,
              <th key={`${c.objective_id}-final`} className="sub">
                {labels.final}
              </th>,
            ])}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th>{labels.runsHeading}</th>
            {cells.map((c) => (
              <td key={c.objective_id} colSpan={2} className="pair">
                {c.runs}
              </td>
            ))}
          </tr>
          {STATUSES.map((status) => {
            const values = cells.flatMap((c) => [
              c.first_attempt_status_counts[status] ?? 0,
              c.status_counts[status] ?? 0,
            ]);
            return (
              <tr key={status} className={values.some((v) => v > 0) ? undefined : "zero"}>
                <th className="mono">{status}</th>
                {values.map((v, i) => (
                  <td key={i} className={i % 2 === 0 ? "first" : undefined}>
                    {v}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export interface RunsTableProps {
  chosen: string;
  tracedRunId: string | null;
}

/** Every run, one row each: the chart's table twin, and the path from a dot to its record. */
export function RunsTable({ chosen, tracedRunId }: RunsTableProps) {
  const lines = data.scenario.lines;
  const order = new Map(data.cells.map((c, i) => [c.objective_id, i]));
  const runs = [...data.runs].sort(
    (a, b) => (order.get(a.objective_id) ?? 0) - (order.get(b.objective_id) ?? 0) || a.repeat - b.repeat,
  );
  const classes = ["runs"];
  if (tracedRunId !== null) classes.push("tracing");
  if (chosen !== "all") classes.push("choosing");
  return (
    <div className="frame wide" role="region" aria-label={labels.runsTableLabel} tabIndex={0}>
      <table className={classes.join(" ")}>
        <thead>
          <tr>
            <th>{labels.columnRun}</th>
            <th>{labels.columnPriority}</th>
            <th>{labels.columnStatus}</th>
            <th>{labels.columnAttempts}</th>
            {lines.map((line) => (
              <th key={line.key} className="amt">
                {line.label}
              </th>
            ))}
            <th>{labels.columnOpenDay}</th>
            <th>{labels.columnImage}</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const row = [];
            if (tracedRunId === run.run_id) row.push("on");
            if (chosen === run.objective_id) row.push("in");
            return (
              <tr key={run.run_id} className={row.join(" ") || undefined} data-run={run.run_id}>
                <td className="l mono">{run.run_id}</td>
                <td className="l">{labels.priorities[run.objective_id] ?? run.objective_id}</td>
                <td className="l mono">{run.status}</td>
                <td>{run.attempts}</td>
                {lines.map((line) => (
                  <td key={line.key}>{money(run.amounts[line.key] ?? 0)}</td>
                ))}
                <td className="l">{run.choice}</td>
                <td className="l mono">{run.image_digest.slice(7, 19)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
