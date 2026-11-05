import type { ReactNode } from "react";
import { labels } from "../copy";
import { data } from "../data";

export const REPOSITORY = "https://github.com/sjtroxel/horizon-compact";

function utc(iso: string): string {
  return `${iso.slice(0, 19).replace("T", " ")} ${labels.utc}`;
}

/** Where the numbers came from: the sweep, the model as served, the image, the code and the cost. */
export function Provenance() {
  const sweep = data.sweep;
  const sha = sweep.git_shas[0] ?? "";
  const prefix = `${sweep.role}/${sweep.experiment}/${sweep.sweep_id}/`;
  const items: Array<[string, ReactNode]> = [
    [labels.termSweep, <span className="mono">{sweep.sweep_id}</span>],
    [labels.termModel, sweep.served_models.join(", ")],
    [labels.termImage, <span className="mono">{sweep.image_digests[0]}</span>],
    [
      labels.termCode,
      <a className="mono" href={`${REPOSITORY}/commit/${sha}`}>
        {sha}
      </a>,
    ],
    [labels.termContentHash, <span className="mono">{sweep.content_hashes[0]}</span>],
    [labels.termRunner, sweep.runners.join(", ")],
    [labels.termStarted, utc(sweep.started_at)],
    [labels.termFinished, utc(sweep.finished_at)],
    [labels.termRuns, labels.runsFinished(sweep.runs_finished, sweep.runs_planned)],
    [labels.termCost, `$${sweep.cost_usd.toFixed(6)}`],
  ];
  return (
    <>
      <dl>
        {items.map(([term, value]) => (
          <div className="item" key={term}>
            <dt>{term}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <p className="notes">{labels.provenanceNote(prefix)}</p>
    </>
  );
}
