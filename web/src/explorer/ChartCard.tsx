/**
 * The chart card and the pieces around it that the scenario view and the guided story share (Phase 6 IMPLEMENTATION
 * doc section 28, C6 part B). Moved out of ScenarioView.tsx so the story's chunk does not pull in the scenario view.
 *
 * The caption is what a crop of the card keeps: the model's name, the valid runs of the attempted, the company line
 * and the scope sentence (section 12's crop test). Every figure in the story's chart cards has the same caption.
 *
 * Nothing here computes a number. Every figure is a field of the grid file or the index, shown through format.ts.
 */
import { goalClass } from "./chartData";
import { ChoiceUnits, ShareStrip } from "./charts";
import type { Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { DataIndex, GridFile } from "./data";
import { attemptedRuns } from "./format";
import { modelName } from "./models";
import { His } from "./parts";

const names: Names = L.objectiveNames;

/** The caption under a chart: the model, the valid runs of those attempted, the company line and the scope sentence. */
export function CardCaption({ file }: { file: GridFile }) {
  return (
    <figcaption>
      <span className="model-name">{modelName(file.model_key)}</span>
      {" · "}
      {L.capValidOfAttempted(file.descriptive.runs, attemptedRuns(file.objective_rates))}
      {" · "}
      {L.capCompany}
      <His text={explorerHis.scopeSentence} />
    </figcaption>
  );
}

/** The primary outcome by goal, every run one dot: the strip for a share scenario, the unit chart for a choice one. */
export function ChartCard({
  file,
  goals,
  hidden,
}: {
  file: GridFile;
  goals: readonly string[];
  hidden: ReadonlySet<string>;
}) {
  const label = L.chartLabel(file.scenario_id, modelName(file.model_key));
  return (
    <figure className="card">
      <p className="chart-key">
        {file.kind === "share" ? (L.shareKey[file.scenario_id] ?? "") : L.choiceKey}
      </p>
      {file.kind === "share" ? (
        <ShareStrip file={file} goals={goals} names={names} hidden={hidden} label={label} />
      ) : (
        <ChoiceUnits file={file} goals={goals} names={names} hidden={hidden} label={label} />
      )}
      <CardCaption file={file} />
    </figure>
  );
}

/** The five goals, each with its swatch, plain name, letter and the literal description from the index. */
export function GoalsList({ index }: { index: DataIndex }) {
  return (
    <ul className="x-goals">
      {index.objectives.map((o) => (
        <li key={o.id} className={goalClass(o.id)}>
          <span className="swatch" aria-hidden="true" />
          <b>{names[o.id] ?? o.id}</b> <span className="letter">({o.id})</span>:{" "}
          {o.who === null || o.when === null ? L.goalUnstated : L.goalTold(o.who, o.when)}
        </li>
      ))}
    </ul>
  );
}
