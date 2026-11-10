/**
 * The scenario view, `/scenario/<id>/`, in layout 2 (Phase 6 IMPLEMENTATION doc sections 8, 24.2 and C4's decided
 * point 2). Top to bottom: the title (his), the scenario in brief (his), the goals listed once, the goal toggles,
 * the card (the chart, with the model's name, the run counts and the scope line in its caption) beside the column of
 * result sentences, the closed "See the details" section, and the repeats line with the link to the section for
 * results against the thesis.
 *
 * Nothing here computes a number. Every figure is a field of the grid file or the index, shown through format.ts.
 */
import { useEffect, useId, useState } from "react";
import type { ReactNode } from "react";
import { orderedComparisons, findComparison, goalClass } from "./chartData";
import { AllocationPanels, ChoiceUnits, IntervalChart, ShareStrip, rowOfComparison } from "./charts";
import type { Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { DataApi, DataIndex, GridComparison, GridFile } from "./data";
import { attemptedRuns, comparisonRuns, confidenceLevel, formatDifference, formatPercent } from "./format";
import { scenarioTextUrl } from "./links";
import { modelName } from "./models";
import { His, ProtocolReading, Title } from "./parts";
import { againstWords } from "./againstWords";
import { readingFor } from "./protocol";
import { resultSentence } from "./sentences";
import { withModel } from "./route";

const names: Names = L.objectiveNames;

/** The address of the section for results against the thesis, carrying the model. */
export function againstHref(model: string): string {
  return `${withModel("/", model)}#${againstWords.sectionId}`;
}

interface Loaded {
  model: string;
  id: string;
  file: GridFile;
}

/** A `details` element closed by default whose content is built only once it is opened (the allocation panels and
 * the run table are thousands of nodes, and a closed section shows none of them). */
function Details({ summary, hint, children }: { summary: string; hint: string; children: ReactNode }) {
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

function listOrNone(items: readonly string[]): string {
  return items.length === 0 ? L.noneWord : items.join(", ");
}

function Sentence({
  comparison,
  file,
  index,
  model,
  lead,
}: {
  comparison: GridComparison;
  file: GridFile;
  index: DataIndex;
  model: string;
  lead: boolean;
}) {
  const sentence = resultSentence(comparison, names, L.outcomePhrases[file.scenario_id] ?? "");
  const cd = findComparison(file, "C", "D");
  const reading = readingFor(
    comparison.first,
    comparison.second,
    comparison.final_verdict,
    cd?.final_verdict ?? null,
  );
  const runs = comparisonRuns(comparison);
  const verdictWord = L.verdictWords[comparison.final_verdict] ?? comparison.final_verdict;
  const dropped = comparison.dropped_wordings.map((w) => w.wording_id);
  const secondary = comparison.role === "secondary";
  const listed = index.against_thesis.entries.some(
    (entry) =>
      entry.model_key === file.model_key &&
      entry.scenario_id === file.scenario_id &&
      entry.first === comparison.first &&
      entry.second === comparison.second,
  );
  const counted =
    comparison.final_verdict === "not_assessable" ? L.noRunsCompared : L.runsPair(runs.first, runs.second);
  return (
    <li className={lead ? "sent lead" : "sent"} data-pair={`${comparison.first}-${comparison.second}`}>
      {lead && <span className="flag">{L.roundtableFlag}</span>}
      {secondary && <span className="flag">{L.secondaryFlag}</span>}
      <p className="result-sentence" data-template={sentence.id}>
        {sentence.text}
      </p>
      <p className="fine">
        {counted}
        {dropped.length > 0 && (
          <>
            {" · "}
            {L.keptWordings(listOrNone(comparison.kept_wordings))}
            {" · "}
            {L.droppedWordings(dropped.join(", "))}
          </>
        )}
        {" · "}
        {L.officialVerdict} {verdictWord}
        {listed && (
          <>
            {" · "}
            <a className="marker" href={againstHref(model)}>
              {L.againstMarker}
            </a>
          </>
        )}
      </p>
      {/* Said once for the column (readingsNote), not under each pair without a row (his pick, section 26a). */}
      {reading !== null && <ProtocolReading readingKey={reading} />}
    </li>
  );
}

function Detail({ comparison }: { comparison: GridComparison }) {
  const pair = `${comparison.first} vs ${comparison.second}`;
  const verdictWord = (v: string) => L.verdictWords[v] ?? v;
  const numbers = (c: { difference: number | null; low: number | null; high: number | null }) =>
    formatDifference(c.difference, c.low, c.high) ?? L.noNumbers;
  const sealed = comparison.sealed;
  const first = comparison.first_attempt;
  return (
    <div className="x-compare" data-pair={`${comparison.first}-${comparison.second}`}>
      <h4>
        {pair} <span className="muted">{verdictWord(comparison.final_verdict)}</span>
      </h4>
      <dl>
        <dt>{L.headlineLabel}</dt>
        <dd className="headline">{comparison.headline}</dd>
        <dt>{L.differenceLabel}</dt>
        <dd>{numbers(comparison)}</dd>
        <dt>{L.keptLabel}</dt>
        <dd>{listOrNone(comparison.kept_wordings)}</dd>
        <dt>{L.droppedLabel}</dt>
        <dd>
          {comparison.dropped_wordings.length === 0
            ? L.noneWord
            : comparison.dropped_wordings
                .map(
                  (d) =>
                    `${d.wording_id}: ${d.cells
                      .map((cell) =>
                        L.droppedCell(
                          names[cell.objective_id] ?? cell.objective_id,
                          cell.unsuccessful,
                          cell.attempted,
                        ),
                      )
                      .join("; ")}`,
                )
                .join(" · ")}
        </dd>
        <dt>{L.sealedLabel}</dt>
        <dd>
          {sealed.label}: {L.sealedWordingIs(sealed.sealed_wording)}, {verdictWord(sealed.final_verdict)},{" "}
          {numbers(sealed)} ({sealed.relation_reason})
        </dd>
        <dt>{L.firstAttemptLabel}</dt>
        <dd>
          {L.firstAttemptNote}: {verdictWord(first.final_verdict)}, {numbers(first)};{" "}
          {L.keptLabel.toLowerCase()}: {listOrNone(first.kept_wordings)}; {L.droppedLabel.toLowerCase()}:{" "}
          {listOrNone(first.dropped_wordings)}.
        </dd>
        <dt>{L.finalLabel}</dt>
        <dd>
          {verdictWord(comparison.final_verdict)}, {numbers(comparison)}.
        </dd>
      </dl>
    </div>
  );
}

function FailuresTable({ file }: { file: GridFile }) {
  return (
    <div className="x-table-wrap" role="region" aria-label={L.failuresHeading} tabIndex={0}>
      <table className="x-table">
        <thead>
          <tr>
            <th scope="col">{L.th.goal}</th>
            <th scope="col">{L.th.wording}</th>
            <th scope="col" className="num">
              {L.th.attempted}
            </th>
            <th scope="col" className="num">
              {L.th.valid}
            </th>
            <th scope="col" className="num">
              {L.th.rescaled}
            </th>
            <th scope="col" className="num">
              {L.th.refused}
            </th>
            <th scope="col">{L.th.failures}</th>
          </tr>
        </thead>
        <tbody>
          {file.cells.map((cell) => (
            <tr key={`${cell.objective_id}-${cell.wording_id}`}>
              <th scope="row">
                {names[cell.objective_id] ?? cell.objective_id} ({cell.objective_id})
              </th>
              <td>{cell.wording_id}</td>
              <td className="num">{cell.attempted}</td>
              <td className="num">{cell.valid}</td>
              <td className="num">{cell.rescaled}</td>
              <td className="num">{cell.refused}</td>
              <td>
                {cell.failed_by_type.length === 0
                  ? L.noneWord
                  : cell.failed_by_type.map(([type, runs]) => L.tableFailures(type, runs)).join("; ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RunsTable({ file }: { file: GridFile }) {
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
                {run.run_id}
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

function DetailsBody({ file, index }: { file: GridFile; index: DataIndex }) {
  const goals = index.objectives.map((o) => o.id);
  const comparisons = orderedComparisons(file);
  const alpha = index.models.find((m) => m.model_key === file.model_key)?.alpha ?? comparisons[0]?.alpha;
  return (
    <>
      <h3>{L.intervalHeading}</h3>
      {alpha !== undefined && <p className="chart-key">{L.intervalKey(confidenceLevel(alpha))}</p>}
      <IntervalChart rows={comparisons.map(rowOfComparison)} names={names} label={L.intervalChartLabel} />
      <h3>{L.perComparisonHeading}</h3>
      {comparisons.map((c) => (
        <Detail key={`${c.first}-${c.second}`} comparison={c} />
      ))}
      <h3>{L.allocationHeading}</h3>
      <p className="chart-key">{L.allocationKey}</p>
      <AllocationPanels file={file} goals={goals} names={names} />
      <h3>{L.failuresHeading}</h3>
      <p className="chart-key">{L.failuresKey}</p>
      <FailuresTable file={file} />
      <h3>{L.runsHeading}</h3>
      <p className="chart-key">{L.runsKey}</p>
      <RunsTable file={file} />
    </>
  );
}

function Card({
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
      <figcaption>
        <span className="model-name">{modelName(file.model_key)}</span>
        {" · "}
        {L.capValidOfAttempted(file.descriptive.runs, attemptedRuns(file.objective_rates))}
        {" · "}
        {L.capCompany}
        <His text={explorerHis.scopeSentence} />
      </figcaption>
    </figure>
  );
}

export interface ScenarioViewProps {
  id: string;
  index: DataIndex;
  model: string;
  data: DataApi;
}

export function ScenarioView({ id, index, model, data }: ScenarioViewProps) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failed, setFailed] = useState<{ model: string; id: string } | null>(null);
  const [hidden, setHidden] = useState<ReadonlySet<string>>(() => new Set());
  const briefId = useId();
  const goalsId = useId();
  const toggleId = useId();
  const sentencesId = useId();

  useEffect(() => {
    let live = true;
    data.loadGrid(model, id).then(
      (file) => {
        if (!live) return;
        setFailed(null);
        setLoaded({ model, id, file });
      },
      () => {
        if (live) setFailed({ model, id });
      },
    );
    return () => {
      live = false;
    };
  }, [data, model, id]);

  const goals = index.objectives.map((o) => o.id);
  const current = loaded !== null && loaded.id === id ? loaded : null;
  const stale = current !== null && current.model !== model;
  const hasFailed = failed !== null && failed.id === id && failed.model === model;
  const brief = explorerHis.scenarioBriefs[id];
  const modelEntry = index.models.find((m) => m.model_key === current?.file.model_key);

  const toggle = (goal: string) =>
    setHidden((before) => {
      const next = new Set(before);
      if (next.has(goal)) next.delete(goal);
      else next.add(goal);
      return next;
    });

  return (
    <>
      <Title route={{ kind: "scenario", id }} />
      <section className="x-section" aria-labelledby={briefId}>
        <h2 id={briefId}>{L.sceneBriefHeading}</h2>
        {brief !== undefined && <His text={brief} />}
        <p>
          <a href={scenarioTextUrl(id)} target="_blank" rel="noopener noreferrer">
            {L.sceneFullText}
          </a>{" "}
          <span className="muted">({L.sceneFullTextNote})</span>
        </p>
      </section>
      <section className="x-section" aria-labelledby={goalsId}>
        <h2 id={goalsId}>{L.goalsHeading}</h2>
        <p className="chart-key">{L.goalsKey}</p>
        <ul className="x-goals">
          {index.objectives.map((o) => (
            <li key={o.id} className={goalClass(o.id)}>
              <span className="swatch" aria-hidden="true" />
              <b>{names[o.id] ?? o.id}</b> <span className="letter">({o.id})</span>:{" "}
              {o.who === null || o.when === null ? L.goalUnstated : L.goalTold(o.who, o.when)}
            </li>
          ))}
        </ul>
      </section>
      {hasFailed ? (
        <p role="alert">{L.loadFailed}</p>
      ) : current === null ? (
        <p role="status">{L.loadingScenario}</p>
      ) : (
        <div className="x-loaded" data-stale={stale ? "true" : "false"} aria-busy={stale}>
          <div className="x-toggles" role="group" aria-labelledby={toggleId}>
            <span id={toggleId} className="x-toggles-label">
              {L.toggleGroup}
            </span>
            {goals.map((goal) => (
              <button
                key={goal}
                type="button"
                className={`x-toggle ${goalClass(goal)}`}
                aria-pressed={!hidden.has(goal)}
                onClick={() => toggle(goal)}
              >
                <span className="swatch" aria-hidden="true" />
                {names[goal] ?? goal} ({goal})
              </button>
            ))}
          </div>
          <div className="layout-2">
            <Card file={current.file} goals={goals} hidden={hidden} />
            <div className="x-sentences" aria-labelledby={sentencesId} role="region">
              <h2 id={sentencesId}>{L.whatRunsShow}</h2>
              {modelEntry !== undefined && (
                <p className="chart-key">{L.verdictNote(confidenceLevel(modelEntry.alpha))}</p>
              )}
              <p className="chart-key readings-note">{L.readingsNote}</p>
              <ol className="x-sentence-list">
                {orderedComparisons(current.file).map((c) => (
                  <Sentence
                    key={`${c.first}-${c.second}`}
                    comparison={c}
                    file={current.file}
                    index={index}
                    model={model}
                    lead={c.first === "C" && c.second === "D"}
                  />
                ))}
              </ol>
            </div>
          </div>
          <Details summary={L.seeDetails} hint={L.detailsHint}>
            <DetailsBody file={current.file} index={index} />
          </Details>
          <p className="x-after">{L.repeatsLine}</p>
          <p>
            <a href={againstHref(model)}>{L.againstLink}</a>
          </p>
        </div>
      )}
    </>
  );
}
