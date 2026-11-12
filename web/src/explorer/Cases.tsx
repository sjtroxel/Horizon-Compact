/**
 * The real cases, `/cases/` and `/cases/<label>/` (Phase 6 IMPLEMENTATION doc sections 8 and 20, C5 B4).
 *
 * Framed as the protocol applied to real decisions, never as validation. The exploratory label comes first on every
 * card and page, as the file writes it. A case is shown only by its label and the fields its files carry: nothing is
 * described, summarized or inferred about the company beyond them. No real-case memo text is on the site and none is
 * linked (decision 5, section 22): the page shows counts.
 *
 * Nothing here computes a number: every figure is a field of a data file, shown through format.ts.
 */
import { useEffect, useId, useState } from "react";
import {
  dependsOnReadingNote,
  everyReadingNoGoodMatch,
  hasOneLineNote,
  hasTieNote,
  labelUnderEveryReading,
  orderedReadings,
  showsNearest,
} from "./caseData";
import { Description, ExploratoryLabel } from "./caseParts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { CaseEntry, CaseFile, CasesIndex, CompanyReading, DataApi, DataIndex } from "./data";
import { DistanceChart } from "./distanceChart";
import { formatDistance, formatPercent } from "./format";
import { SELECTION_LOGS, selectionLogUrl } from "./links";
import { modelName, orderedModels } from "./models";
import { His, Title } from "./parts";
import { hrefOf } from "./route";

const names: Readonly<Record<string, string>> = L.objectiveNames;

/** The files of every case for every model, once loaded: label, then model key. */
type Files = Record<string, Record<string, CaseFile>>;

const readingName = (id: string) => L.readingNames[id] ?? L.readingAlternative(id);
const labelWord = (label: string) => L.readingLabels[label] ?? label;
const typeWord = (type: string) => L.caseTypes[type] ?? type;
const dimensionWord = (key: string) => (key === "choice" ? L.caseDimensionChoice : (L.levers[key] ?? key));

/** Loads every case file for every model of the index; `null` until all have arrived, and `failed` if one did not. */
function useCaseFiles(
  data: DataApi,
  labels: readonly string[],
  models: readonly string[],
): { files: Files | null; failed: boolean } {
  const [state, setState] = useState<{ files: Files | null; failed: boolean }>({
    files: null,
    failed: false,
  });
  const wanted = `${labels.join(",")}|${models.join(",")}`;
  useEffect(() => {
    let live = true;
    Promise.all(
      labels.flatMap((label) =>
        models.map(async (model) => [label, model, await data.loadCase(label, model)] as const),
      ),
    ).then(
      (found) => {
        if (!live) return;
        const files: Files = {};
        for (const [label, model, file] of found) (files[label] ??= {})[model] = file;
        setState({ files, failed: false });
      },
      () => {
        if (live) setState({ files: null, failed: true });
      },
    );
    return () => {
      live = false;
    };
    // `wanted` stands for the two lists.
  }, [data, wanted]);
  return state;
}

function Shortfall({ casesIndex }: { casesIndex: CasesIndex }) {
  const headingId = useId();
  const { shortfall } = casesIndex;
  return (
    <section className="x-section shortfall" aria-labelledby={headingId}>
      <h2 id={headingId}>{L.shortfallHeading}</h2>
      <p className="chart-key">{L.shortfallNote}</p>
      <div className="x-table-wrap" role="region" aria-label={L.shortfallTableLabel} tabIndex={0}>
        <table className="x-table">
          <thead>
            <tr>
              <th scope="col">{L.shortfallType}</th>
              <th scope="col" className="num">
                {L.shortfallFound}
              </th>
              <th scope="col" className="num">
                {L.shortfallShort}
              </th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(shortfall.cases_by_type).map((type) => (
              <tr key={type} data-type={type}>
                <th scope="row">{typeWord(type)}</th>
                <td className="num">{shortfall.cases_by_type[type]}</td>
                <td className="num">{shortfall.short_by_type[type]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <dl className="x-facts">
        <dt>{L.shortfallAtMost}</dt>
        <dd>{shortfall.at_most}</dd>
        <dt>{L.shortfallFilled}</dt>
        <dd>
          {shortfall.filled} <span className="muted">({L.shortfallFilledNote})</span>
        </dd>
      </dl>
      <h3>{L.selectionLogsHeading}</h3>
      <ul className="x-sources">
        {SELECTION_LOGS.map((log) => (
          <li key={log.id}>
            <a href={selectionLogUrl(log.path)} target="_blank" rel="noopener noreferrer">
              {L.selectionLogs[log.id]}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

export interface CasesViewProps {
  index: DataIndex;
  casesIndex: CasesIndex;
  model: string;
  data: DataApi;
}

/** `/cases/`: his introduction, the framing, the exploratory label, the shortfall, the logs, and a card a case. */
export function CasesView({ index, casesIndex, model, data }: CasesViewProps) {
  const models = orderedModels(index.models).map((m) => m.model_key);
  const { files, failed } = useCaseFiles(
    data,
    casesIndex.cases.map((c) => c.label),
    models,
  );
  const everyFile = files === null ? [] : Object.values(files).flatMap((byModel) => Object.values(byModel));
  const labels = [...new Set(casesIndex.cases.map((c) => c.exploratory_label))];
  return (
    <>
      <Title route={{ kind: "cases" }} />
      <His text={explorerHis.casesIntro} />
      <His text={explorerHis.scopeSentence} />
      <p className="x-note case-framing">{L.casesFraming}</p>
      <section className="x-section exploratory-lead">
        <p>{L.casesLabelLead}</p>
        {labels.map((text) => (
          <ExploratoryLabel key={text} text={text} />
        ))}
      </section>
      {everyReadingNoGoodMatch(everyFile) && (
        <p className="x-note" data-sentence="every-reading-no-good-match">
          {L.allNoGoodMatch}
        </p>
      )}
      <Shortfall casesIndex={casesIndex} />
      {failed && <p role="alert">{L.loadFailed}</p>}
      <ul className="case-cards">
        {casesIndex.cases.map((entry) => (
          <li key={entry.label} className="case-card" data-case={entry.label}>
            <h2>
              <a className="mono" href={hrefOf({ kind: "case", label: entry.label }, model)}>
                {entry.label}
              </a>
            </h2>
            <ExploratoryLabel text={entry.exploratory_label} />
            <p className="fine">
              {L.caseTypeLabel}: {typeWord(entry.type)}
            </p>
            <Description entry={entry} />
            {files === null ? (
              failed ? null : (
                <p role="status">{L.casesLoading}</p>
              )
            ) : (
              <ul className="case-readings">
                {models.map((key) => {
                  const file = files[entry.label]?.[key];
                  if (file === undefined) return null;
                  return (
                    <li key={key} data-model={key}>
                      <b>{modelName(key)}</b>:{" "}
                      {orderedReadings(file)
                        .map((r) => `${readingName(r.reading)}: ${labelWord(r.label)}`)
                        .join("; ")}
                    </li>
                  );
                })}
              </ul>
            )}
            <p>
              <a href={hrefOf({ kind: "case", label: entry.label }, model)}>{L.caseSeeCase}</a>
            </p>
          </li>
        ))}
      </ul>
    </>
  );
}

function CompanyDecision({
  company,
  alternatives,
}: {
  company: CompanyReading;
  alternatives: CompanyReading[];
}) {
  const shares = (reading: CompanyReading) => {
    const entries = Object.entries(reading.shares);
    return entries.length === 0
      ? L.caseNoShares
      : entries.map(([lever, share]) => `${L.levers[lever] ?? lever}: ${formatPercent(share)}`).join("; ");
  };
  return (
    <>
      <p>{L.caseCompanyChoice(L.choices[company.choice] ?? company.choice)}</p>
      <ul className="x-facts-list">
        {[company, ...alternatives].map((reading) => (
          <li key={reading.reading}>
            <b>{readingName(reading.reading)}</b>: {shares(reading)}
          </li>
        ))}
      </ul>
    </>
  );
}

function ModelSection({ entry, file }: { entry: CaseEntry; file: CaseFile }) {
  const model = modelName(file.model_key);
  const counts = file.memo_counts;
  const sameLabel = labelUnderEveryReading(file);
  const unmatched = file.alternative_readings.unmatched_calls;
  return (
    <section className="x-section case-model" data-model={file.model_key}>
      <h2>{L.caseModelHeading(model)}</h2>
      <p>{L.caseRunCounts(file.run_counts.runs)}</p>
      <ul className="x-facts-list">
        {Object.entries(file.run_counts.by_final_status).map(([status, runs]) => (
          <li key={status}>{L.caseFinalStatus(status, runs)}</li>
        ))}
      </ul>
      {orderedReadings(file).map((reading) => (
        <div
          key={reading.reading}
          className="case-reading"
          data-reading={reading.reading}
          data-label={reading.label}
        >
          <h3>{readingName(reading.reading)}</h3>
          <p>
            <b>{L.readingLabelIs(labelWord(reading.label))}</b>
          </p>
          <p className="fine reading-reason">
            {L.readingReason}: {reading.reason}
          </p>
          <p className="fine">
            {L.readingLines}:{" "}
            {reading.observable_lines.length === 0
              ? L.noneWord
              : reading.observable_lines.map(dimensionWord).join("; ")}
          </p>
          <DistanceChart
            caseLabel={entry.label}
            model={model}
            readingName={readingName(reading.reading)}
            labelWord={labelWord(reading.label)}
            reading={reading}
            dStar={file.thresholds.d_star}
            alpha={file.thresholds.alpha}
            names={names}
          />
          {showsNearest(reading) && reading.nearest !== null && (
            <div className="nearest" data-nearest={reading.nearest}>
              <p>{L.nearestLine(names[reading.nearest] ?? reading.nearest, reading.nearest)}</p>
              {reading.tied_with !== null && <p>{L.tiedWith([reading.tied_with].flat().join(", "))}</p>}
              {reading.gap !== null && (
                <p className="fine">
                  {L.gapLine(
                    reading.gap.second,
                    formatDistance(reading.gap.estimate),
                    formatDistance(reading.gap.low),
                    formatDistance(reading.gap.high),
                  )}
                </p>
              )}
            </div>
          )}
          {hasTieNote(reading) && (
            <p className="x-note" data-note="tie">
              {L.tieNote}
            </p>
          )}
          {hasOneLineNote(reading) && (
            <p className="x-note" data-note="one-line">
              {L.oneLineNote}
            </p>
          )}
        </div>
      ))}
      <p data-depends={file.depends_on_reading ? "yes" : "no"}>
        {L.dependsLabel}: {file.depends_on_reading ? L.dependsYes : L.dependsNo}
      </p>
      {dependsOnReadingNote(file) && (
        <p className="x-note" data-note="depends-tie">
          {L.dependsTieNote}
          {sameLabel !== null && ` ${L.dependsSameLabel(labelWord(sameLabel))}`}
        </p>
      )}
      <p className="fine">
        {L.alternativesLine(
          file.alternative_readings.matched,
          unmatched.length === 0 ? L.noneWord : JSON.stringify(unmatched),
        )}
      </p>
      <h3>{L.caseMemosHeading}</h3>
      <His text={explorerHis.caseMemosHeld} />
      <p className="fine">{L.caseMemosNone}</p>
      <dl className="x-facts">
        {Object.entries(L.memoCountLabels).map(([key, word]) => (
          <div key={key}>
            <dt>{word}</dt>
            <dd>{counts[key as keyof typeof counts] as number}</dd>
          </div>
        ))}
      </dl>
      <h4>{L.heldReasonsHeading}</h4>
      <ul className="x-facts-list">
        {Object.entries(counts.held_by_reason).map(([reason, n]) => (
          <li key={reason}>
            {L.heldReasons[reason] ?? reason}: {n}
          </li>
        ))}
      </ul>
    </section>
  );
}

export interface CaseViewProps {
  label: string;
  index: DataIndex;
  casesIndex: CasesIndex;
  data: DataApi;
}

/** `/cases/<label>/`, top to bottom as section 8 lists it. */
export function CaseView({ label, index, casesIndex, data }: CaseViewProps) {
  const entry = casesIndex.cases.find((c) => c.label === label);
  const models = orderedModels(index.models).map((m) => m.model_key);
  const { files, failed } = useCaseFiles(data, entry === undefined ? [] : [label], models);
  if (entry === undefined) return null;
  const mine = files?.[label];
  const first = mine === undefined ? undefined : mine[models[0]!];
  return (
    <>
      <Title route={{ kind: "case", label }} />
      <ExploratoryLabel text={entry.exploratory_label} />
      <His text={explorerHis.scopeSentence} />
      <section className="x-section">
        <h2>{L.caseDescriptionHeading}</h2>
        <p className="fine">
          {L.caseTypeLabel}: {typeWord(entry.type)}
        </p>
        <Description entry={entry} />
        {entry.description.status !== "published" && (
          <p className="fine">
            {L.caseDescriptionWithheld}
            {entry.description.reason !== undefined && (
              <>
                {" "}
                · {L.caseReasonLabel}: {entry.description.reason}
              </>
            )}
          </p>
        )}
      </section>
      <section className="x-section">
        <h2>{L.caseDossierHeading}</h2>
        <p>{L.caseDossierStatus(entry.dossier.published)}</p>
        <p className="fine">
          {L.caseReasonLabel}: {entry.dossier.reason}
        </p>
      </section>
      <section className="x-section">
        <h2>{L.caseReidentHeading}</h2>
        <p>{L.caseReidentStatus(entry.reidentification.status)}</p>
        <p className="fine">
          {L.caseReasonLabel}: {entry.reidentification.reason}
        </p>
        <p className="fine">
          {L.caseThresholdLabel}: {entry.reidentification.threshold}
        </p>
      </section>
      <section className="x-section">
        <h2>{L.caseProbesHeading}</h2>
        <p className="chart-key">{L.caseProbesKey}</p>
        <div className="x-table-wrap" role="region" aria-label={L.caseProbesHeading} tabIndex={0}>
          <table className="x-table">
            <thead>
              <tr>
                <th scope="col">{L.caseProbeSet}</th>
                <th scope="col">{L.caseProbeModel}</th>
                <th scope="col" className="num">
                  {L.caseProbeCalls}
                </th>
                <th scope="col" className="num">
                  {L.caseProbePassed}
                </th>
              </tr>
            </thead>
            <tbody>
              {entry.probes.map((probe) => (
                <tr key={`${probe.set}-${probe.model}`}>
                  <th scope="row">{probe.set}</th>
                  <td>{modelName(probe.model)}</td>
                  <td className="num">{probe.calls}</td>
                  <td className="num">{probe.passed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {failed && <p role="alert">{L.loadFailed}</p>}
      {mine === undefined || first === undefined ? (
        failed ? null : (
          <p role="status">{L.caseLoading}</p>
        )
      ) : (
        <>
          <section className="x-section">
            <h2>{L.caseCompanyHeading}</h2>
            <CompanyDecision company={first.company} alternatives={first.company_alternatives} />
          </section>
          <section className="x-section">
            <h2>{L.caseDimensionsHeading}</h2>
            <dl className="x-facts">
              <dt>{L.caseObservable}</dt>
              <dd>{first.dimensions.observable.map(dimensionWord).join("; ")}</dd>
              <dt>{L.caseExcluded}</dt>
              <dd>{first.dimensions.excluded.map(dimensionWord).join("; ")}</dd>
            </dl>
          </section>
          <p className="chart-key">{L.caseReadingNote}</p>
          <p className="chart-key">{L.distanceKey}</p>
          {models.map((key) => {
            const file = mine[key];
            return file === undefined ? null : <ModelSection key={key} entry={entry} file={file} />;
          })}
        </>
      )}
    </>
  );
}
