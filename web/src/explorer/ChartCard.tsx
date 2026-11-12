/**
 * The chart frame and the pieces around it that the scenario view, the studies and the guided story share (Phase 6
 * IMPLEMENTATION doc section 28, C6 part B; reframed in section 31, the step 11 redesign batch).
 *
 * A chart is framed by a rule, not a box (`Frame`): a top rule, a bold title naming the measure (never a result), an
 * italic line for the unit or how to read it, the chart, then ONE note line in the `figcaption`: the model's name, the
 * valid runs of those attempted (or, where the chart has none, what the caller gives) and the short scope line. A crop
 * of the figure keeps all three (section 12's crop test). The full scope sentence is on the page once, not under a chart.
 * The class `card` is kept as the figure's hook (the views' tests and the styles select it); it is no longer a box.
 *
 * Nothing here computes a number. Every figure is a field of the grid file or the index, shown through format.ts.
 */
import { useId } from "react";
import type { ReactNode } from "react";
import { goalClass } from "./chartData";
import { ChoiceUnits, IntervalChart, ShareStrip } from "./charts";
import type { IntervalRow, Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { DataIndex, GridFile } from "./data";
import { attemptedRuns, confidenceLevel } from "./format";
import { modelName } from "./models";
import { HisInline } from "./parts";

const names: Names = L.objectiveNames;

/** The note line of a figure: the model, then `middle` (valid of attempted, or the rows' own counts), then the scope line. */
export function NoteLine({ model, middle }: { model: string; middle: ReactNode }) {
  return (
    <figcaption>
      <span className="model-name">{model}</span>
      {middle !== null && (
        <>
          {" · "}
          {middle}
        </>
      )}
      {" · "}
      <HisInline text={explorerHis.scopeShort} />
    </figcaption>
  );
}

/** The note line of a figure drawn from one grid file: the model's name and its valid runs of those attempted. */
export function CardCaption({ file }: { file: GridFile }) {
  return (
    <NoteLine
      model={modelName(file.model_key)}
      middle={L.capValidOfAttempted(file.descriptive.runs, attemptedRuns(file.objective_rates))}
    />
  );
}

/** A figure framed by a rule: title, unit line, the chart, the note line. `note` is a `NoteLine`. */
export function Frame({
  title,
  unit,
  note,
  children,
  className,
  ...rest
}: {
  title: string;
  unit?: string | null;
  note: ReactNode;
  children: ReactNode;
  className?: string;
  "data-reading"?: string;
}) {
  const titleId = useId();
  return (
    <figure
      className={className === undefined ? "card" : `card ${className}`}
      aria-labelledby={titleId}
      {...rest}
    >
      <p className="frame-title" id={titleId}>
        {title}
      </p>
      {unit !== undefined && unit !== null && <p className="frame-unit">{unit}</p>}
      {children}
      {note}
    </figure>
  );
}

/** The interval chart in its frame: the measure as the title and the unit as the italic line. */
export function IntervalFrame({
  rows,
  outcome,
  note,
}: {
  rows: readonly IntervalRow[];
  outcome: string;
  note: ReactNode;
}) {
  return (
    <Frame title={L.chartTitles.interval(outcome)} unit={L.intervalAxis} note={note}>
      <IntervalChart rows={rows} names={names} label={L.intervalChartLabel} />
    </Frame>
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
  const share = file.kind === "share";
  return (
    <Frame
      title={share ? (L.chartTitles.share[file.scenario_id] ?? "") : L.chartTitles.choice}
      unit={share ? (L.shareKey[file.scenario_id] ?? "") : L.choiceKey}
      note={<CardCaption file={file} />}
    >
      {share ? (
        <ShareStrip file={file} goals={goals} names={names} hidden={hidden} label={label} />
      ) : (
        <ChoiceUnits file={file} goals={goals} names={names} hidden={hidden} label={label} />
      )}
    </Frame>
  );
}

/** The closed "about these results" section: what the interval, the level and the correction mean, said once. */
export function AboutResults({ alpha }: { alpha: number | undefined }) {
  return (
    <details className="about">
      <summary>{L.aboutSummary}</summary>
      <div className="about-body">
        {alpha !== undefined && (
          <>
            <p>{L.verdictNote(confidenceLevel(alpha))}</p>
            <p>{L.intervalKey(confidenceLevel(alpha))}</p>
          </>
        )}
        <p className="readings-note">{L.readingsNote}</p>
      </div>
    </details>
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
