/**
 * The studies, `/studies/` (Phase 6 IMPLEMENTATION doc sections 8 and 20, C5 B5): the thinking sub-study, set beside
 * the main grid's `s1` like for like, and the awareness probes, quoted in full.
 *
 * The sub-study is labeled as a sub-study on `s1` wherever it appears, and it is outside the family of 16: this view
 * does not use the scenario view's note about the family, shows no protocol reading (section 1.5's table is for the
 * grid), and words its interval level without the family. The awareness probes are context only and never filter or
 * weight any run.
 *
 * Nothing here computes a number: every figure is a field of a data file, shown through format.ts.
 */
import { useEffect, useId, useState } from "react";
import { goalClass, findComparison, orderedComparisons } from "./chartData";
import { ShareStrip } from "./charts";
import type { Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { AwarenessFile, DataApi, DataIndex, GridFile } from "./data";
import { attemptedRuns, comparisonRuns, confidenceLevel } from "./format";
import {
  AWARENESS_ANCHOR,
  STUDIES_AWARENESS_ID,
  STUDIES_THINKING_ID,
  THINKING_ANCHOR,
  protocolUrl,
} from "./links";
import { modelName, orderedModels } from "./models";
import { His, HisHeading, Title } from "./parts";
import { AWARENESS_INSTRUCTION } from "./protocol";
import { memoHref } from "./route";
import { Details, RunsTable } from "./RunDetails";
import { resultSentence } from "./sentences";

const names: Names = L.objectiveNames;
const NOTHING_HIDDEN: ReadonlySet<string> = new Set();
const verdictWord = (verdict: string) => L.verdictWords[verdict] ?? verdict;

interface Loaded {
  thinking: GridFile;
  grid: GridFile;
  awareness: AwarenessFile[];
}

function StripCard({
  title,
  file,
  wording,
  counts,
  goals,
}: {
  title: string;
  file: GridFile;
  wording?: string | undefined;
  counts: string | null;
  goals: readonly string[];
}) {
  return (
    <figure className="card">
      <p className="chart-key study-card-title">{title}</p>
      <ShareStrip
        file={file}
        goals={goals}
        names={names}
        hidden={NOTHING_HIDDEN}
        label={title}
        wording={wording}
      />
      <figcaption>
        <span className="model-name">{modelName(file.model_key)}</span>
        {counts !== null && (
          <>
            {" · "}
            {counts}
          </>
        )}
        {" · "}
        {L.capCompany}
        <His text={explorerHis.scopeSentence} />
      </figcaption>
    </figure>
  );
}

function Thinking({ loaded, index }: { loaded: Loaded; index: DataIndex }) {
  const { thinking, grid } = loaded;
  const goals = index.objectives.map((o) => o.id);
  const sealed = index.models.find((m) => m.model_key === thinking.model_key)?.sealed_wording;
  const comparisons = orderedComparisons(thinking);
  const alpha = comparisons[0]?.alpha;
  const headingId = useId();
  return (
    <section
      className="x-section studies-part"
      id={STUDIES_THINKING_ID}
      tabIndex={-1}
      aria-labelledby={headingId}
    >
      <HisHeading text={explorerHis.studiesThinkingTitle} level={2} id={headingId} />
      <p className="x-note" data-label="sub-study">
        {L.studiesSubStudyLabel}
      </p>
      <p className="fine">
        {L.studiesSettings}{" "}
        <a href={protocolUrl(THINKING_ANCHOR)} target="_blank" rel="noopener noreferrer">
          {L.studiesSettingsLink}
        </a>
      </p>
      <div className="layout-pair">
        <StripCard title={L.studiesGridCard} file={grid} wording={sealed} counts={null} goals={goals} />
        <StripCard
          title={L.studiesThinkingCard}
          file={thinking}
          counts={L.capValidOfAttempted(thinking.descriptive.runs, attemptedRuns(thinking.objective_rates))}
          goals={goals}
        />
      </div>
      <p className="chart-key">{L.studiesGridNote}</p>
      <h3>{L.studiesComparisonsHeading}</h3>
      {alpha !== undefined && <p className="chart-key">{L.studiesLevel(confidenceLevel(alpha))}</p>}
      <ol className="x-sentence-list">
        {comparisons.map((c) => {
          const sentence = resultSentence(c, names, L.outcomePhrases[thinking.scenario_id] ?? "");
          const runs = comparisonRuns(c);
          const gridPair = findComparison(grid, c.first, c.second);
          return (
            <li
              key={`${c.first}-${c.second}`}
              className={c.first === "C" && c.second === "D" ? "sent lead paired" : "sent paired"}
              data-pair={`${c.first}-${c.second}`}
            >
              <div className="paired-main">
                {c.first === "C" && c.second === "D" && <span className="flag">{L.roundtableFlag}</span>}
                {c.role === "secondary" && <span className="flag">{L.secondaryFlag}</span>}
                <p className="result-sentence" data-template={sentence.id}>
                  {sentence.text}
                </p>
                <p className="fine">
                  {c.final_verdict === "not_assessable"
                    ? L.noRunsCompared
                    : L.runsPair(runs.first, runs.second)}
                  {" · "}
                  {L.officialVerdict} {verdictWord(c.final_verdict)}
                </p>
                <p className="fine headline">
                  {L.headlineLabel}: {c.headline}
                </p>
              </div>
              {gridPair !== undefined && (
                <p className="fine paired-grid" data-grid-sealed={gridPair.sealed.final_verdict}>
                  {L.studiesGridSealed(
                    gridPair.sealed.sealed_wording,
                    verdictWord(gridPair.sealed.final_verdict),
                  )}
                </p>
              )}
            </li>
          );
        })}
      </ol>
      <p>
        <a
          href={memoHref(
            { kind: "thinking", scenario: thinking.scenario_id, objective: goals[0] ?? "A" },
            thinking.model_key,
          )}
        >
          {L.studiesMemosLink}
        </a>
      </p>
      <Details summary={L.studiesRunsHeading} hint={L.studiesRunsKey}>
        <RunsTable file={thinking} kind="thinking" />
      </Details>
    </section>
  );
}

/** One reply to the awareness probe, as a document with its label inside the card; the text exactly. */
function ReplyCard({ file, call }: { file: AwarenessFile; call: AwarenessFile["calls"][number] }) {
  const labelId = useId();
  const goal = call.objective_id;
  return (
    <article
      className="memo-card reply-card"
      aria-labelledby={labelId}
      data-goal={goal}
      data-template={call.template_id}
    >
      <p className="memo-label" id={labelId}>
        {L.awarenessCardLabel(modelName(file.model_key), goal, names[goal] ?? goal, call.template_id)}
      </p>
      {!call.recorded ? (
        <p className="memo-none">{L.awarenessNotRecorded}</p>
      ) : (
        <>
          <p className="fine">{L.awarenessStatus(call.status, call.stop_reason, call.output_tokens)}</p>
          {call.empty_reply ? (
            <p className="memo-none">{L.awarenessEmpty}</p>
          ) : (
            <div className="memo-text">{call.reply}</div>
          )}
        </>
      )}
    </article>
  );
}

function Awareness({ files, index }: { files: AwarenessFile[]; index: DataIndex }) {
  const headingId = useId();
  return (
    <section
      className="x-section studies-part"
      id={STUDIES_AWARENESS_ID}
      tabIndex={-1}
      aria-labelledby={headingId}
    >
      <HisHeading text={explorerHis.studiesAwarenessTitle} level={2} id={headingId} />
      <p className="x-note" data-label="awareness">
        {L.awarenessLabel}
      </p>
      <p className="fine">{L.awarenessInstructionLabel}</p>
      <blockquote className="reading probe-instruction">
        <p>{AWARENESS_INSTRUCTION}</p>
      </blockquote>
      <p className="fine">
        {L.awarenessSettings}{" "}
        <a href={protocolUrl(AWARENESS_ANCHOR)} target="_blank" rel="noopener noreferrer">
          {L.awarenessLink}
        </a>
      </p>
      {files.map((file) => (
        <div key={file.model_key} className="awareness-model" data-model={file.model_key}>
          <h3>{modelName(file.model_key)}</h3>
          {index.objectives.map((o) => (
            <div key={o.id} className={`awareness-goal ${goalClass(o.id)}`} data-goal={o.id}>
              <h4>
                <span className="swatch" aria-hidden="true" />
                {L.awarenessGoalHeading(names[o.id] ?? o.id, o.id)}
              </h4>
              {file.calls
                .filter((call) => call.objective_id === o.id)
                .map((call) => (
                  <ReplyCard key={call.template_id} file={file} call={call} />
                ))}
            </div>
          ))}
        </div>
      ))}
    </section>
  );
}

export interface StudiesViewProps {
  index: DataIndex;
  data: DataApi;
}

export function StudiesView({ index, data }: StudiesViewProps) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    (async () => {
      const [thinking] = await data.loadThinking();
      if (thinking === undefined) throw new Error("explorer data: the index lists no thinking sub-study");
      const [grid, awareness] = await Promise.all([
        data.loadGrid(thinking.model_key, thinking.scenario_id),
        Promise.all(orderedModels(index.models).map((m) => data.loadAwareness(m.model_key))),
      ]);
      return { thinking, grid, awareness };
    })().then(
      (found) => {
        if (live) setLoaded(found);
      },
      () => {
        if (live) setFailed(true);
      },
    );
    return () => {
      live = false;
    };
  }, [data, index]);
  return (
    <>
      <Title route={{ kind: "studies" }} />
      <His text={explorerHis.studiesIntro} />
      {failed ? (
        <p role="alert">{L.loadFailed}</p>
      ) : loaded === null ? (
        <p role="status">{L.studiesLoading}</p>
      ) : (
        <>
          <Thinking loaded={loaded} index={index} />
          <Awareness files={loaded.awareness} index={index} />
        </>
      )}
    </>
  );
}
