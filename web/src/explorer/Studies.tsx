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
import { CardCaption, Frame, NoteLine } from "./ChartCard";
import { goalClass, findComparison, orderedComparisons } from "./chartData";
import { ShareStrip } from "./charts";
import type { Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { AwarenessFile, DataApi, DataIndex, GridFile } from "./data";
import { comparisonRuns, confidenceLevel, wordingRuns } from "./format";
import {
  AWARENESS_ANCHOR,
  STUDIES_AWARENESS_ID,
  STUDIES_THINKING_ID,
  THINKING_ANCHOR,
  protocolUrl,
} from "./links";
import { modelName, orderedModels } from "./models";
import { FindingMore, His, HisHeading, Title } from "./parts";
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
  goals,
}: {
  title: string;
  file: GridFile;
  wording?: string | undefined;
  goals: readonly string[];
}) {
  // A figure that draws one wording of the grid states that wording's runs, not the whole file's.
  const counts = wording === undefined ? null : wordingRuns(file, wording);
  const note =
    counts === null ? (
      <CardCaption file={file} />
    ) : (
      <NoteLine
        model={modelName(file.model_key)}
        middle={L.capValidOfAttempted(counts.valid, counts.attempted)}
      />
    );
  return (
    <Frame title={title} unit={L.shareKey[file.scenario_id] ?? null} note={note}>
      <ShareStrip
        file={file}
        goals={goals}
        names={names}
        hidden={NOTHING_HIDDEN}
        label={title}
        wording={wording}
      />
    </Frame>
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
      <div className="studies-words">
        <p className="x-note" data-label="sub-study">
          {L.studiesSubStudyLabel}
        </p>
        <p className="fine">
          {L.studiesSettings}{" "}
          <a href={protocolUrl(THINKING_ANCHOR)} target="_blank" rel="noopener noreferrer">
            {L.studiesSettingsLink}
          </a>
        </p>
        <p className="chart-key">{L.studiesGridNote}</p>
      </div>
      <div className="studies-figures">
        <StripCard title={L.studiesGridCard} file={grid} wording={sealed} goals={goals} />
        <StripCard title={L.studiesThinkingCard} file={thinking} goals={goals} />
      </div>
      <h3>{L.studiesComparisonsHeading}</h3>
      {alpha !== undefined && <p className="chart-key">{L.studiesLevel(confidenceLevel(alpha))}</p>}
      {sealed !== undefined && (
        // Not hidden from a screen reader, and shown on a phone too: it is the only place the page says the grid's w2
        // cut is not one of the 16 main comparisons (Opus review, section 33a).
        <div className="paired-head">
          <span />
          <p>{L.studiesGridColumn(sealed)}</p>
        </div>
      )}
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
                </p>
                <FindingMore>
                  <p className="fine">
                    {L.officialVerdict} {verdictWord(c.final_verdict)}
                  </p>
                  <p className="fine headline">
                    {L.headlineLabel}: {c.headline}
                  </p>
                </FindingMore>
              </div>
              {gridPair !== undefined && (
                <p className="paired-grid" data-grid-sealed={gridPair.sealed.final_verdict}>
                  <span className="paired-row-label">
                    {L.studiesGridRowLabel(gridPair.sealed.sealed_wording)}:{" "}
                  </span>
                  <span className="paired-verdict">{verdictWord(gridPair.sealed.final_verdict)}</span>
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

/**
 * One reply to the awareness probe, in its cell of the grid: its template, its status line and the reply text exactly
 * (protocol section 9.6 quotes every reply in full). No card of its own; the row's rules separate the rows.
 */
function ReplyCell({ goalId, call }: { goalId: string; call: AwarenessFile["calls"][number] }) {
  const tagId = useId();
  return (
    <article
      className="reply-cell"
      aria-labelledby={`${goalId} ${tagId}`}
      data-goal={call.objective_id}
      data-template={call.template_id}
    >
      <p className="reply-tag" id={tagId}>
        {L.awarenessTemplateTag(call.template_id)}
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

/** One goal's row: its color dot and name, then its replies, a column to a template (stacked on a phone). */
function ReplyRow({ file, goal }: { file: AwarenessFile; goal: { id: string } }) {
  const headingId = useId();
  return (
    <div className={`reply-row ${goalClass(goal.id)}`} data-goal={goal.id}>
      <h4 id={headingId}>
        <span className="swatch" aria-hidden="true" />
        {L.awarenessGoalHeading(names[goal.id] ?? goal.id, goal.id)}
      </h4>
      <div className="reply-cells">
        {file.calls
          .filter((call) => call.objective_id === goal.id)
          .map((call) => (
            <ReplyCell key={call.template_id} goalId={headingId} call={call} />
          ))}
      </div>
    </div>
  );
}

/** The awareness probe's replies of the model the page is showing (the switch is the tab); the sub-study above does not follow it. */
function Awareness({ files, index, model }: { files: AwarenessFile[]; index: DataIndex; model: string }) {
  const headingId = useId();
  const file = files.find((f) => f.model_key === model);
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
      {file !== undefined && (
        <div className="awareness-model" data-model={file.model_key}>
          <h3>{modelName(file.model_key)}</h3>
          <p className="chart-key">{L.awarenessGridLabel(modelName(file.model_key))}</p>
          <div className="reply-grid">
            {index.objectives.map((o) => (
              <ReplyRow key={o.id} file={file} goal={o} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export interface StudiesViewProps {
  index: DataIndex;
  /** The model the switch shows: the awareness replies follow it; the thinking sub-study (Haiku 5.5 only) does not. */
  model: string;
  data: DataApi;
}

export function StudiesView({ index, model, data }: StudiesViewProps) {
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
      <His text={explorerHis.scopeSentence} />
      {failed ? (
        <p role="alert">{L.loadFailed}</p>
      ) : loaded === null ? (
        <p role="status">{L.studiesLoading}</p>
      ) : (
        <>
          <Thinking loaded={loaded} index={index} />
          <Awareness files={loaded.awareness} index={index} model={model} />
        </>
      )}
    </>
  );
}
