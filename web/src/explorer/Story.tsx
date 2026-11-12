/**
 * The guided story, `/` (Phase 6 IMPLEMENTATION doc sections 9 and 28, C6 part B): nine beats, each a `<section>` with
 * an id, in the order the doc lists them. Every sentence in it is his (a `his.json` value, a placeholder until he writes
 * it), an approved result-sentence template, or a label; nothing else, and no number is computed here.
 *
 * Which model where (decision 7): the main model is the first of `orderedModels(index.models)` and the second is the
 * other. The story ignores `?model=` for its own content, because it shows both models by design; the shell shows no
 * model switch on `/`.
 *
 * Motion (planning/06 section 7.2 rule 7): every beat is in the document from the first render, and nothing is fetched
 * on scroll. With `IntersectionObserver` present and no `prefers-reduced-motion`, a beat that starts below the first
 * screen gets the class `beat-enter` (CSS: a short fade and an 8 px rise) until it comes into view. No sticky
 * positioning, no scroll-linked animation, no scroll library.
 *
 * Loading: the first two beats need only the index and render at once. Every other beat that waits on data shows the
 * loading line in place; a failed load shows the failure line in that beat only. The story reports once to the shell
 * when every beat's data has loaded or failed (`onSettled`), because the shell's reveal of a hash (the section for
 * results against the thesis, say) waits for that: the beats above the target change its place on the page as they fill.
 */
import { useEffect, useId, useRef, useState } from "react";
import type { ReactNode, RefObject } from "react";
import { AgainstThesis } from "./AgainstThesis";
import { AboutResults, CardCaption, ChartCard, GoalsList, IntervalFrame } from "./ChartCard";
import { againstWords } from "./againstWords";
import { Description, ExploratoryLabel } from "./caseParts";
import { everyReadingNoGoodMatch, labelUnderEveryReading } from "./caseData";
import { SENTENCE_ORDER, findComparison, orderedComparisons } from "./chartData";
import { rowOfComparison } from "./charts";
import type { Names } from "./charts";
import { explorerHis, explorerLabels as L } from "./copy";
import type { CaseFile, CasesIndex, DataApi, DataIndex, GridComparison, GridFile } from "./data";
import { attemptedRuns, comparisonRuns, formatPoints } from "./format";
import { ROUNDTABLE_CLAIM_URL, ROUNDTABLE_OVERVIEW_URL, protocolUrl, scenarioTextUrl } from "./links";
import { modelName, orderedModels } from "./models";
import { His, HisHeading, HisInline, ProtocolReading, Title } from "./parts";
import { readingFor } from "./protocol";
import { hrefOf } from "./route";
import { resultSentence } from "./sentences";

const names: Names = L.objectiveNames;
const NOTHING_HIDDEN: ReadonlySet<string> = new Set();
const verdictWord = (verdict: string) => L.verdictWords[verdict] ?? verdict;
const typeWord = (type: string) => L.caseTypes[type] ?? type;

/** The class a beat carries while it waits below the first screen. Its CSS is a short entrance and nothing else. */
const ENTER_CLASS = "beat-enter";

// ----------------------------------------------------------------------------------------------------------------
// Data

/** A file that arrived or did not. A file with no slot yet is still loading. */
type Slot<T> = { state: "loaded"; value: T } | { state: "failed" };

interface StoryData {
  grids: Record<string, Slot<GridFile>>;
  cases: Record<string, Slot<CaseFile>>;
}

const gridKey = (model: string, scenario: string) => `${model}|${scenario}`;
const caseKey = (label: string, model: string) => `${label}|${model}`;

type Gathered<T> = { status: "loading" } | { status: "failed" } | { status: "loaded"; values: T[] };

/** The state of a beat that needs several files: failed if any failed, loaded when all have, loading otherwise. */
function gather<T>(slots: ReadonlyArray<Slot<T> | undefined>): Gathered<T> {
  const values: T[] = [];
  let waiting = false;
  for (const slot of slots) {
    if (slot === undefined) waiting = true;
    else if (slot.state === "failed") return { status: "failed" };
    else values.push(slot.value);
  }
  return waiting ? { status: "loading" } : { status: "loaded", values };
}

/** Loads every file the story reads through the cached `DataApi`: each model's grid file for each scenario, and every
 * case file for each model. `settled` is true once each has loaded or failed. */
function useStoryData(
  data: DataApi,
  scenarios: readonly string[],
  models: readonly string[],
  labels: readonly string[],
): { loaded: StoryData; settled: boolean } {
  const [loaded, setLoaded] = useState<StoryData>({ grids: {}, cases: {} });
  const wanted = `${scenarios.join(",")}|${models.join(",")}|${labels.join(",")}`;
  useEffect(() => {
    let live = true;
    const settle = <T,>(promise: Promise<T>, put: (data: StoryData, slot: Slot<T>) => StoryData) => {
      promise
        .then(
          (value): Slot<T> => ({ state: "loaded", value }),
          (): Slot<T> => ({ state: "failed" }),
        )
        .then((slot) => {
          if (live) setLoaded((before) => put(before, slot));
        });
    };
    for (const model of models) {
      for (const id of scenarios) {
        settle(data.loadGrid(model, id), (before, slot) => ({
          ...before,
          grids: { ...before.grids, [gridKey(model, id)]: slot },
        }));
      }
      for (const label of labels) {
        settle(data.loadCase(label, model), (before, slot) => ({
          ...before,
          cases: { ...before.cases, [caseKey(label, model)]: slot },
        }));
      }
    }
    return () => {
      live = false;
    };
    // `wanted` stands for the three lists.
  }, [data, wanted]);
  const settled =
    models.every(
      (model) =>
        scenarios.every((id) => loaded.grids[gridKey(model, id)] !== undefined) &&
        labels.every((label) => loaded.cases[caseKey(label, model)] !== undefined),
    ) && models.length > 0;
  return { loaded, settled };
}

// ----------------------------------------------------------------------------------------------------------------
// Motion

/** Gives each beat after the first the entrance class while it waits below the first screen; see the file header. */
function useEntrance(root: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const element = root.current;
    if (element === null || typeof IntersectionObserver === "undefined") return;
    if (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    )
      return;
    const beats = [...element.children].filter((child) => child.tagName === "SECTION").slice(1);
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.remove(ENTER_CLASS);
            observer.unobserve(entry.target);
          } else if (entry.boundingClientRect.top >= window.innerHeight) {
            // Wholly below the screen. A beat whose top is on the first screen but inside the root margin's bottom band
            // is not intersecting yet and is left alone (it is already seen), as is a beat already scrolled past.
            entry.target.classList.add(ENTER_CLASS);
          }
        }
      },
      { rootMargin: "0px 0px -10% 0px" },
    );
    for (const beat of beats) observer.observe(beat);
    return () => observer.disconnect();
  }, [root]);
}

// ----------------------------------------------------------------------------------------------------------------
// Pieces

function Beat({
  id,
  title,
  intro,
  children,
}: {
  id: string;
  title: string;
  intro?: string;
  children?: ReactNode;
}) {
  const headingId = useId();
  return (
    <section id={id} className="x-section story-beat" aria-labelledby={headingId}>
      <HisHeading text={title} level={2} id={headingId} />
      {intro !== undefined && <His text={intro} />}
      {children}
    </section>
  );
}

/** What stands in a beat's place while its data is on its way, or when it did not load. */
function Wait({ status, label = L.loading }: { status: "loading" | "failed"; label?: string }) {
  return status === "failed" ? (
    <p role="alert">{L.loadFailed}</p>
  ) : (
    <p role="status" className="story-wait">
      {label}
    </p>
  );
}

/** A result sentence: always the template's output, with its id on the element. */
function TemplateSentence({ comparison, file }: { comparison: GridComparison; file: GridFile }) {
  const sentence = resultSentence(comparison, names, L.outcomePhrases[file.scenario_id] ?? "");
  return (
    <p className="result-sentence" data-template={sentence.id}>
      {sentence.text}
    </p>
  );
}

const runsLine = (comparison: GridComparison): string => {
  if (comparison.final_verdict === "not_assessable") return L.noRunsCompared;
  const runs = comparisonRuns(comparison);
  return L.runsPair(runs.first, runs.second);
};

// ----------------------------------------------------------------------------------------------------------------
// The beats

/** The sections the jump menu links to, in the story's order: each one's id and the title that is its link text (his words). */
const JUMPS: ReadonlyArray<readonly [string, string]> = [
  ["beat-setup", explorerHis.story.setupTitle],
  ["beat-s1", explorerHis.story.s1Title],
  ["beat-comparisons", explorerHis.story.comparisonsTitle],
  ["beat-second-model", explorerHis.story.secondTitle],
  ["beat-other-scenarios", explorerHis.story.othersTitle],
  [againstWords.sectionId, explorerHis.againstTitle],
  ["beat-cases", explorerHis.story.casesTitle],
  ["beat-methods", explorerHis.story.methodsTitle],
];

/** Beat 1: the page's title block (title, his metadata line, the jump menu) on the title band, then the question. */
function Question() {
  const titleId = useId();
  return (
    <section id="beat-question" className="x-section story-beat story-open" aria-labelledby={titleId}>
      <Title route={{ kind: "story" }} id={titleId}>
        <His className="meta-line" text={explorerHis.story.metaLine} />
        <nav className="jump-menu" aria-label={L.jumpMenuLabel}>
          <ul>
            {JUMPS.map(([id, title]) => (
              <li key={id}>
                <a href={`#${id}`}>{title}</a>
              </li>
            ))}
          </ul>
        </nav>
      </Title>
      <div className="story-lede">
        <His text={explorerHis.landingQuestion} />
        <His text={explorerHis.storyName} />
      </div>
    </section>
  );
}

function Setup({ index, alpha }: { index: DataIndex; alpha: number | undefined }) {
  return (
    <Beat id="beat-setup" title={explorerHis.story.setupTitle} intro={explorerHis.story.setupIntro}>
      <p className="chart-key">{L.goalsKey}</p>
      <GoalsList index={index} />
      <His text={explorerHis.scopeSentence} />
      <AboutResults alpha={alpha} />
    </Beat>
  );
}

export interface StoryProps {
  index: DataIndex;
  casesIndex: CasesIndex;
  data: DataApi;
  /** Called once when every beat's data has loaded or failed. */
  onSettled?: (() => void) | undefined;
}

export function Story({ index, casesIndex, data, onSettled }: StoryProps) {
  const root = useRef<HTMLDivElement | null>(null);
  const models = orderedModels(index.models).map((m) => m.model_key);
  const main = models[0]!;
  const scenarioIds = index.scenarios.map((s) => s.scenario_id);
  const [walked, ...others] = scenarioIds as [string, ...string[]];
  const labels = casesIndex.cases.map((c) => c.label);
  const { loaded, settled } = useStoryData(data, scenarioIds, models, labels);

  useEntrance(root);
  useEffect(() => {
    if (settled) onSettled?.();
  }, [settled, onSettled]);

  const grid = (model: string, id: string) => loaded.grids[gridKey(model, id)];
  const mainWalked = gather([grid(main, walked)]);
  const bothWalked = gather(models.map((model) => grid(model, walked)));
  const otherGrids = gather(others.flatMap((id) => models.map((model) => grid(model, id))));
  const caseFiles = gather(
    labels.flatMap((label) => models.map((model) => loaded.cases[caseKey(label, model)])),
  );
  const goals = index.objectives.map((o) => o.id);
  const mainEntry = index.models.find((m) => m.model_key === main);

  return (
    <div className="story" ref={root}>
      <Question />
      <Setup index={index} alpha={mainEntry?.alpha} />

      <Beat id="beat-s1" title={explorerHis.story.s1Title} intro={explorerHis.story.s1Intro}>
        <div className="beside">
          <div className="beside-text">
            {explorerHis.scenarioBriefs[walked] !== undefined && (
              <His text={explorerHis.scenarioBriefs[walked]} />
            )}
            <p>
              <a href={scenarioTextUrl(walked)} target="_blank" rel="noopener noreferrer">
                {L.sceneFullText}
              </a>{" "}
              <span className="muted">({L.sceneFullTextNote})</span>
            </p>
            <p>
              <a href={hrefOf({ kind: "scenario", id: walked }, main)}>
                {L.storyOpenScenario(walked, modelName(main))}
              </a>
            </p>
          </div>
          {mainWalked.status === "loaded" ? (
            <ChartCard file={mainWalked.values[0]!} goals={goals} hidden={NOTHING_HIDDEN} />
          ) : (
            <Wait status={mainWalked.status} />
          )}
        </div>
      </Beat>

      <Beat
        id="beat-comparisons"
        title={explorerHis.story.comparisonsTitle}
        intro={explorerHis.story.comparisonsIntro}
      >
        <ul className="x-sources story-links" data-sources="roundtable">
          <li>
            <a href={ROUNDTABLE_OVERVIEW_URL} target="_blank" rel="noopener noreferrer">
              {L.storyRoundtableOverview}
            </a>
          </li>
          <li>
            <a href={ROUNDTABLE_CLAIM_URL} target="_blank" rel="noopener noreferrer">
              {L.storyRoundtableClaim}
            </a>
          </li>
        </ul>
        {mainWalked.status === "loaded" ? (
          <Comparisons file={mainWalked.values[0]!} />
        ) : (
          <Wait status={mainWalked.status} />
        )}
      </Beat>

      <Beat
        id="beat-second-model"
        title={explorerHis.story.secondTitle}
        intro={explorerHis.story.secondIntro}
      >
        {bothWalked.status === "loaded" ? (
          <>
            <div className="layout-pair">
              {bothWalked.values.map((file) => (
                <ModelColumn key={file.model_key} file={file} />
              ))}
            </div>
            <VerdictTable
              id={walked}
              files={bothWalked.values}
              cell="gap"
              caption={L.storySecondTableCaption(walked)}
            />
          </>
        ) : (
          <Wait status={bothWalked.status} />
        )}
      </Beat>

      <Beat
        id="beat-other-scenarios"
        title={explorerHis.story.othersTitle}
        intro={explorerHis.story.othersIntro}
      >
        {otherGrids.status === "loaded" ? (
          others.map((id) => (
            <ScenarioTable
              key={id}
              id={id}
              files={models.map((model) =>
                otherGrids.values.find((f) => f.scenario_id === id && f.model_key === model)!,
              )}
            />
          ))
        ) : (
          <Wait status={otherGrids.status} />
        )}
      </Beat>

      <AgainstThesis index={index} />

      <CasesBeat casesIndex={casesIndex} models={models} files={caseFiles} main={main} />

      <Beat id="beat-methods" title={explorerHis.story.methodsTitle} intro={explorerHis.story.methodsText}>
        <ul className="x-sources story-links">
          <li>
            <a href={protocolUrl()} target="_blank" rel="noopener noreferrer">
              {L.storyProtocolLink}
            </a>
          </li>
          <li>
            <a href={hrefOf({ kind: "studies" }, main)}>{L.storyStudiesLink}</a>
          </li>
          <li>
            <a href={hrefOf({ kind: "memos" }, main)}>{L.storyMemosLink}</a>
          </li>
        </ul>
      </Beat>
    </div>
  );
}

/** Beat 4: the five comparisons on the first scenario as numbered findings, in the sentence column's order. Each is led
 * by its result sentence (the template's output) in bold, with its chart beside it at desktop width; the verdict is said
 * in the sentence and on the chart, and the rest (run counts, the official verdict, the analysis headline, the
 * protocol's reading) is in a closed section under it. The numbers 1 to 5 are the list's own, drawn by the stylesheet. */
function Comparisons({ file }: { file: GridFile }) {
  const cdVerdict = findComparison(file, "C", "D")?.final_verdict ?? null;
  const outcome = L.outcomePhrases[file.scenario_id] ?? "";
  return (
    <ol className="story-comparisons findings" role="list">
      {orderedComparisons(file).map((c) => {
        const lead = c.first === "C" && c.second === "D";
        const reading = readingFor(c.first, c.second, c.final_verdict, cdVerdict);
        return (
          <li
            key={`${c.first}-${c.second}`}
            className="story-comparison finding"
            data-pair={`${c.first}-${c.second}`}
          >
            <div className="beside">
              <div className="beside-text">
                <div className={lead ? "sent lead" : "sent"}>
                  {lead && <span className="flag">{L.roundtableFlag}</span>}
                  {c.role === "secondary" && <span className="flag">{L.secondaryFlag}</span>}
                  <TemplateSentence comparison={c} file={file} />
                </div>
                <details className="finding-more">
                  <summary>{L.findingMore}</summary>
                  <p className="fine">
                    {runsLine(c)}
                    {" · "}
                    {L.officialVerdict} {verdictWord(c.final_verdict)}
                  </p>
                  <p className="fine">
                    {L.headlineLabel}: <span className="headline">{c.headline}</span>
                  </p>
                  {reading !== null ? (
                    <ProtocolReading readingKey={reading} />
                  ) : (
                    lead && <ProtocolReading readingKey={null} />
                  )}
                </details>
              </div>
              <IntervalFrame
                rows={[rowOfComparison(c)]}
                outcome={outcome}
                note={<CardCaption file={file} />}
              />
            </div>
          </li>
        );
      })}
    </ol>
  );
}

/** Beat 5: one model's five comparisons as one chart in its frame. The sentences are on the scenario pages. */
function ModelColumn({ file }: { file: GridFile }) {
  const comparisons = orderedComparisons(file);
  return (
    <div className="story-model" data-model={file.model_key}>
      <h3>{modelName(file.model_key)}</h3>
      <IntervalFrame
        rows={comparisons.map(rowOfComparison)}
        outcome={L.outcomePhrases[file.scenario_id] ?? ""}
        note={<CardCaption file={file} />}
      />
    </div>
  );
}

/**
 * A table of every verdict for one scenario, a column to a model, in the sentence column's order. Words, in place, no
 * color. `cell` says what a cell holds beside the verdict word: "gap" (the second model's table) the gap in points where
 * the verdict is a split, which is where the result sentence states one, and nothing otherwise; "runs" (beat 6) the
 * comparison's run counts. Under it, one note line: each model, its valid runs of those attempted, the short scope line.
 */
function VerdictTable({
  id,
  files,
  cell,
  caption,
}: {
  id: string;
  files: readonly GridFile[];
  cell: "gap" | "runs";
  caption: string;
}) {
  return (
    <>
      <div className="x-table-wrap" role="region" aria-label={caption} tabIndex={0}>
        <table className="x-table story-table" data-scenario={id} data-cell={cell}>
          <caption>{caption}</caption>
          <thead>
            <tr>
              <th scope="col">{L.storyComparisonColumn}</th>
              {files.map((file) => (
                <th key={file.model_key} scope="col">
                  {modelName(file.model_key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SENTENCE_ORDER.map(([first, second]) => (
              <tr key={`${first}-${second}`} data-pair={`${first}-${second}`}>
                <th scope="row">
                  <b>
                    {first} vs {second}
                  </b>
                  {files[0] !== undefined &&
                    findComparison(files[0], first, second)?.role === "secondary" && (
                      <span className="muted"> {L.secondaryFlag.toLowerCase()}</span>
                    )}
                  <span className="muted story-pair-names">
                    {names[first] ?? first} vs {names[second] ?? second}
                  </span>
                </th>
                {files.map((file) => {
                  const c = findComparison(file, first, second);
                  return (
                    <td key={file.model_key} data-model={file.model_key} data-verdict={c?.final_verdict}>
                      {c === undefined ? (
                        L.noneWord
                      ) : (
                        <>
                          <span className="verdict-word">{verdictWord(c.final_verdict)}</span>
                          {cell === "runs" ? (
                            <span className="fine story-cell-runs">{runsLine(c)}</span>
                          ) : (
                            c.final_verdict === "split" &&
                            c.difference !== null && (
                              <span className="story-cell-gap">
                                {L.gapPoints(formatPoints(c.difference))}
                              </span>
                            )
                          )}
                        </>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <TableNote files={files} />
    </>
  );
}

/** The note line under a table: each model, its valid runs of those attempted, then the short scope line. */
function TableNote({ files }: { files: readonly GridFile[] }) {
  return (
    <p className="table-note">
      {files.map((file) => (
        <span key={file.model_key}>
          <span className="model-name">{modelName(file.model_key)}</span>
          {" · "}
          {L.capValidOfAttempted(file.descriptive.runs, attemptedRuns(file.objective_rates))}
          {" · "}
        </span>
      ))}
      <HisInline text={explorerHis.scopeShort} />
    </p>
  );
}

const scenarioTitle = (id: string): string =>
  (explorerHis.story as unknown as Record<string, string>)[`${id}Title`] ?? `${L.scenario} ${id}`;

/** Beat 6, one scenario: its heading (his, the same level and style as the first scenario's), its brief, its table. */
function ScenarioTable({ id, files }: { id: string; files: readonly GridFile[] }) {
  const headingId = useId();
  const brief = explorerHis.scenarioBriefs[id];
  return (
    <section className="story-scenario" data-scenario={id} aria-labelledby={headingId}>
      <HisHeading text={scenarioTitle(id)} level={2} id={headingId} />
      {brief !== undefined && <His text={brief} />}
      <VerdictTable id={id} files={files} cell="runs" caption={L.storyTableCaption(id)} />
      <ul className="x-sources story-links">
        {files.map((file) => (
          <li key={file.model_key}>
            <a href={hrefOf({ kind: "scenario", id }, file.model_key)}>
              {L.storyOpenScenario(id, modelName(file.model_key))}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

/**
 * Beat 8: the real cases, exploratory label first. Nothing about a case beyond the fields of its files that the cases
 * page shows; no memo text and no link to a memo (rule zero; decision 5).
 */
function CasesBeat({
  casesIndex,
  models,
  files,
  main,
}: {
  casesIndex: CasesIndex;
  models: readonly string[];
  files: Gathered<CaseFile>;
  main: string;
}) {
  const { shortfall } = casesIndex;
  const distinctLabels = [...new Set(casesIndex.cases.map((c) => c.exploratory_label))];
  return (
    <Beat id="beat-cases" title={explorerHis.story.casesTitle} intro={explorerHis.story.casesIntro}>
      <div className="exploratory-lead">
        <p>{L.casesLabelLead}</p>
        {distinctLabels.map((text) => (
          <ExploratoryLabel key={text} text={text} />
        ))}
      </div>
      {files.status !== "loaded" ? (
        <Wait status={files.status} label={L.casesLoading} />
      ) : (
        <>
          {everyReadingNoGoodMatch(files.values) && (
            <p className="x-note" data-sentence="every-reading-no-good-match">
              {L.allNoGoodMatch}
            </p>
          )}
          <ul className="case-cards story-cases">
            {casesIndex.cases.map((entry) => (
              <li key={entry.label} className="case-card" data-case={entry.label}>
                <h3 className="mono">{entry.label}</h3>
                <ExploratoryLabel text={entry.exploratory_label} />
                <Description entry={entry} />
                <ul className="case-readings">
                  {models.map((model) => {
                    const file = files.values.find((f) => f.case === entry.label && f.model_key === model);
                    if (file === undefined) return null;
                    const label = labelUnderEveryReading(file);
                    return (
                      <li key={model} data-model={model}>
                        <b>{modelName(model)}</b>:{" "}
                        {label === null ? L.storyLabelVaries : (L.readingLabels[label] ?? label)}
                      </li>
                    );
                  })}
                </ul>
                <p>
                  <a href={hrefOf({ kind: "case", label: entry.label }, main)}>{L.caseSeeCase}</a>
                </p>
              </li>
            ))}
          </ul>
        </>
      )}
      <h3>{L.shortfallHeading}</h3>
      <div className="x-table-wrap" role="region" aria-label={L.shortfallTableLabel} tabIndex={0}>
        <table className="x-table story-shortfall">
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
      <p>
        <a href={hrefOf({ kind: "cases" }, main)}>{L.storyAllCases}</a>
      </p>
    </Beat>
  );
}
