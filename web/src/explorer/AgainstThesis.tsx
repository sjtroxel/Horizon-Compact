/**
 * The section for results against the thesis (Phase 6 IMPLEMENTATION doc sections 8 and 19, C4's decided point 6).
 *
 * It has no path of its own: it is mounted on `/`, under the story's stub, with the id `against-the-thesis`, and every
 * scenario view links to `/#against-the-thesis`. The list is whatever `against_thesis.entries` holds, in the file's
 * order, never re-filtered and never re-sorted. Each entry carries the same interval chart as the details, at the
 * same size (planning/06 section 7.2, rule 4: equal visual weight for unwelcome results).
 */
import { useId } from "react";
import { againstWords } from "./againstWords";
import { IntervalChart } from "./charts";
import type { IntervalRow, Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { AgainstThesisEntry, DataIndex } from "./data";
import { comparisonRuns, formatPoints } from "./format";
import { modelName } from "./models";
import { His, HisHeading, ProtocolReading } from "./parts";
import { readingFor } from "./protocol";

const names: Names = L.objectiveNames;

function listOrNone(items: readonly string[]): string {
  return items.length === 0 ? againstWords.none : items.join(", ");
}

function rowOf(entry: AgainstThesisEntry, threshold: number): IntervalRow {
  return {
    first: entry.first,
    second: entry.second,
    secondary: false, // the rule reads primary comparisons only
    difference: entry.difference,
    low: entry.low,
    high: entry.high,
    threshold,
    verdict: entry.final_verdict,
  };
}

function Entry({ entry, index }: { entry: AgainstThesisEntry; index: DataIndex }) {
  const scenario = index.scenarios.find((s) => s.scenario_id === entry.scenario_id);
  const block = index.verdicts.find(
    (v) => v.model_key === entry.model_key && v.scenario_id === entry.scenario_id,
  );
  const cdVerdict =
    block?.comparisons.find((c) => c.first === "C" && c.second === "D")?.final_verdict ?? null;
  const reading = readingFor(entry.first, entry.second, entry.final_verdict, cdVerdict);
  const pair = againstWords.entryPair(entry.first, entry.second);
  const runs = comparisonRuns(entry);
  const dropped = entry.dropped_wordings.map((d) => d.wording_id);
  const verdictWord = L.verdictWords[entry.final_verdict] ?? entry.final_verdict;
  return (
    <li
      className="x-entry"
      data-model={entry.model_key}
      data-scenario={entry.scenario_id}
      data-pair={`${entry.first}-${entry.second}`}
    >
      <h4>
        {modelName(entry.model_key)} <span className="muted">&middot;</span> {L.scenario} {entry.scenario_id}{" "}
        <span className="muted">&middot;</span> {pair}
      </h4>
      <p className="fine muted">
        {entry.clause === "no_split" ? againstWords.clauseNoSplit : againstWords.clauseReversed}
      </p>
      <dl>
        <dt>{againstWords.verdictLabel}</dt>
        <dd>{verdictWord}</dd>
        <dt>{againstWords.differenceLabel}</dt>
        <dd>{entry.difference === null ? againstWords.none : `${formatPoints(entry.difference)} points`}</dd>
        <dt>{againstWords.intervalLabel}</dt>
        <dd>
          {entry.low === null || entry.high === null
            ? againstWords.none
            : `${formatPoints(entry.low)} to ${formatPoints(entry.high)} points`}
        </dd>
        <dt>{againstWords.validRunsLabel}</dt>
        <dd>{L.runsPair(runs.first, runs.second)}</dd>
        <dt>{L.keptLabel}</dt>
        <dd>{listOrNone(entry.kept_wordings)}</dd>
        <dt>{L.droppedLabel}</dt>
        <dd>{listOrNone(dropped)}</dd>
        <dt>{L.headlineLabel}</dt>
        <dd className="headline">{entry.headline}</dd>
      </dl>
      {scenario !== undefined && (
        <IntervalChart rows={[rowOf(entry, scenario.threshold)]} names={names} label={L.intervalChartLabel} />
      )}
      <ProtocolReading readingKey={reading} />
      {entry.roundtable_pair && <p className="x-note">{againstWords.alsoAgainstAuthor}</p>}
      {entry.scenario_id === "s4" && <p className="x-note">{againstWords.s4Note}</p>}
    </li>
  );
}

export function AgainstThesis({ index }: { index: DataIndex }) {
  const titleId = useId();
  const { entries, scenarios, rule } = index.against_thesis;
  return (
    <section
      id={againstWords.sectionId}
      className="x-section x-against"
      tabIndex={-1}
      aria-labelledby={titleId}
    >
      <HisHeading text={explorerHis.againstTitle} level={2} id={titleId} />
      <His text={explorerHis.againstIntro} />
      <h3>{againstWords.ruleHeading}</h3>
      {againstWords.ruleParagraphs.map((paragraph) => (
        <p key={paragraph}>{paragraph}</p>
      ))}
      <h3>{againstWords.sourcesHeading}</h3>
      <ul className="x-sources">
        {againstWords.sources.map((source) => (
          <li key={source}>{source}</li>
        ))}
      </ul>
      <p>{againstWords.writtenLine}</p>
      <p>{againstWords.disclosure}</p>
      <p className="fine">
        {againstWords.citationLabel} <span className="mono">{rule}</span>
      </p>
      <h3>{againstWords.entriesHeading}</h3>
      {entries.length === 0 ? (
        <p className="x-empty">{againstWords.emptyList}</p>
      ) : (
        <ol className="x-entries">
          {entries.map((entry) => (
            <Entry
              key={`${entry.model_key}-${entry.scenario_id}-${entry.first}-${entry.second}`}
              entry={entry}
              index={index}
            />
          ))}
        </ol>
      )}
      {scenarios.length > 0 && (
        <>
          <h3>{againstWords.wholeHeading}</h3>
          <ul className="x-whole">
            {scenarios.map((s) => (
              <li key={`${s.model_key}-${s.scenario_id}`}>
                {againstWords.wholeLine(s.scenario_id, modelName(s.model_key))}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
