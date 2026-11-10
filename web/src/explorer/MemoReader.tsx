/**
 * The memo reader, `/memos/` (Phase 6 IMPLEMENTATION doc section 8, C5 B3; `planning/06` sections 6.1 and 7).
 *
 * A memo is set as a document, never as a quote or as speech: no blockquote, no quotation marks, no italics. The
 * label is inside the card, so a cropped picture of the card keeps it. The text is shown exactly as the extract has
 * it: `white-space: pre-wrap` in the body face, never parsed as Markdown and never trimmed.
 *
 * Every choice is a link, so every choice is a URL: `?kind=`, `?scenario=`, `?objective=`, `?run=` and the
 * explorer's one `?model=`. Nothing here counts or computes.
 */
import { useEffect, useId, useMemo, useState } from "react";
import { explorerHis, explorerLabels as L } from "./copy";
import type { DataApi, DataIndex, MemoCell, MemoIndex, MemoRow } from "./data";
import { memoCells, resolveMemoQuery, scenariosOf } from "./memoData";
import { modelName } from "./models";
import { His, Title } from "./parts";
import { MEMO_KINDS, memoHref, readMemoQuery, withModel } from "./route";
import { STUDIES_THINKING_ID } from "./links";

const names: Readonly<Record<string, string>> = L.objectiveNames;

/**
 * One memo as a document. The label comes first and sits inside the card; then the run id, wording, repeat and
 * status; then the text, exactly; then, small, the source records a reader can check against the raw-object
 * manifest. A run with no text shows its status and the label that it left no memo, and nothing else in the text's
 * place.
 */
export function MemoCard({
  row,
  model,
  goal,
  kind,
  manifest,
}: {
  row: MemoRow;
  model: string;
  goal: string;
  kind: string;
  manifest: MemoIndex["raw_manifest"];
}) {
  const labelId = useId();
  return (
    <article className="memo-card" aria-labelledby={labelId} data-run={row.run_id}>
      <p className="memo-label" id={labelId}>
        {L.memoCardLabel(modelName(model), goal, names[goal] ?? goal, kind === "thinking")}
      </p>
      <dl className="memo-meta">
        <div>
          <dt>{L.memoRun}</dt>
          <dd className="mono">{row.run_id}</dd>
        </div>
        <div>
          <dt>{L.memoWording}</dt>
          <dd>{row.wording_id}</dd>
        </div>
        <div>
          <dt>{L.memoRepeat}</dt>
          <dd>{row.repeat}</dd>
        </div>
        <div>
          <dt>{L.memoStatus}</dt>
          <dd>{row.status}</dd>
        </div>
        {row.source !== null && (
          <div>
            <dt>{L.memoSource}</dt>
            <dd>{L.memoSources[row.source] ?? row.source}</dd>
          </div>
        )}
      </dl>
      {row.memo !== null ? (
        <div className="memo-text">{row.memo}</div>
      ) : (
        <p className="memo-none">{L.memoLeftNone}</p>
      )}
      <div className="memo-sources fine">
        <p>{L.memoSourceNote(manifest.path, manifest.sha256)}</p>
        <dl>
          <dt>{L.memoFinalRecord}</dt>
          <dd className="mono">
            {row.final.key} · {row.final.sha256}
          </dd>
          <dt>{L.memoAttemptRecord}</dt>
          <dd className="mono">
            {row.attempt.key} · {row.attempt.sha256}
          </dd>
        </dl>
      </div>
    </article>
  );
}

/** A link in a chooser: the current choice carries `aria-current`. */
function Choice({ href, current, children }: { href: string; current: boolean; children: string }) {
  return (
    <li>
      <a href={href} aria-current={current ? "true" : undefined}>
        {children}
      </a>
    </li>
  );
}

interface Loaded {
  key: string;
  cell: MemoCell;
}

export interface MemosViewProps {
  index: DataIndex;
  model: string;
  /** The URL's query string, with its leading "?" or empty. */
  search: string;
  data: DataApi;
}

export function MemosView({ index, model, search, data }: MemosViewProps) {
  const [memoIndex, setMemoIndex] = useState<MemoIndex | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const kindsId = useId();
  const scenariosId = useId();
  const goalsId = useId();
  const runsId = useId();

  useEffect(() => {
    let live = true;
    data.loadMemoIndex().then(
      (found) => {
        if (live) setMemoIndex(found);
      },
      () => {
        if (live) setFailed("index");
      },
    );
    return () => {
      live = false;
    };
  }, [data]);

  const scenarioIds = useMemo(() => index.scenarios.map((s) => s.scenario_id), [index]);
  const goalIds = useMemo(() => index.objectives.map((o) => o.id), [index]);
  const cells = useMemo(() => (memoIndex === null ? [] : memoCells(memoIndex)), [memoIndex]);
  const query = readMemoQuery(search);
  const resolved = memoIndex === null ? null : resolveMemoQuery(query, model, scenarioIds, goalIds, cells);
  const key =
    resolved !== null && resolved.ok
      ? `${resolved.kind}/${model}/${resolved.scenario}/${resolved.objective}`
      : null;

  useEffect(() => {
    if (resolved === null || !resolved.ok || key === null) return;
    let live = true;
    data.loadMemos(resolved.kind, model, resolved.scenario, resolved.objective).then(
      (cell) => {
        if (live) setLoaded({ key, cell });
      },
      () => {
        if (live) setFailed(key);
      },
    );
    return () => {
      live = false;
    };
    // The selection is its key: a new key, a new load.
  }, [data, model, key]);

  const toDefault = memoHref(
    { kind: "grid", scenario: scenarioIds[0] ?? "s1", objective: goalIds[0] ?? "A" },
    model,
  );

  const body = () => {
    if (failed === "index") return <p role="alert">{L.loadFailed}</p>;
    if (resolved === null) return <p role="status">{L.memoLoading}</p>;
    if (!resolved.ok) {
      return (
        <div className="x-empty" data-refusal={resolved.why}>
          {resolved.why === "thinking_model" ? (
            <>
              <p>{L.memoThinkingOnly(modelName("haiku-5-5"))}</p>
              <p>
                <a href={`${withModel("/studies/", model)}#${STUDIES_THINKING_ID}`}>{L.memoSeeSubStudy}</a>
              </p>
            </>
          ) : (
            <>
              <p>{L.memoMessages[resolved.why]}</p>
              <p>
                <a href={toDefault}>{L.memoToFirst}</a>
              </p>
            </>
          )}
        </div>
      );
    }
    const { kind, scenario, objective } = resolved;
    const here = { kind, scenario, objective };
    const choosers = (
      <div className="memo-choosers">
        <div role="group" aria-labelledby={kindsId}>
          <span className="chooser-label" id={kindsId}>
            {L.memoKindLabel}
          </span>
          <ul>
            {MEMO_KINDS.map((k) => {
              const first = cells.find((c) => c.kind === k && c.model === model);
              // A kind with no memos for this model is not offered; the thinking sub-study is Haiku 5.5's only.
              if (first === undefined) return null;
              const sameScenario = cells.some(
                (c) =>
                  c.kind === k && c.model === model && c.scenario === scenario && c.objective === objective,
              );
              const target = sameScenario ? here : { scenario: first.scenario, objective: first.objective };
              return (
                <Choice key={k} href={memoHref({ ...here, ...target, kind: k }, model)} current={k === kind}>
                  {L.memoKinds[k] ?? k}
                </Choice>
              );
            })}
          </ul>
        </div>
        <div role="group" aria-labelledby={scenariosId}>
          <span className="chooser-label" id={scenariosId}>
            {L.memoScenarioLabel}
          </span>
          <ul>
            {scenariosOf(cells, kind, model).map((s) => (
              <Choice
                key={s}
                href={memoHref({ kind, scenario: s, objective }, model)}
                current={s === scenario}
              >
                {s}
              </Choice>
            ))}
          </ul>
        </div>
        <div role="group" aria-labelledby={goalsId}>
          <span className="chooser-label" id={goalsId}>
            {L.memoGoalLabel}
          </span>
          <ul>
            {goalIds.map((g) => (
              <Choice
                key={g}
                href={memoHref({ kind, scenario, objective: g }, model)}
                current={g === objective}
              >
                {`${names[g] ?? g} (${g})`}
              </Choice>
            ))}
          </ul>
        </div>
      </div>
    );
    if (failed === key)
      return (
        <>
          {choosers}
          <p role="alert">{L.loadFailed}</p>
        </>
      );
    if (loaded === null || loaded.key !== key) {
      return (
        <>
          {choosers}
          <p role="status">{L.memoLoading}</p>
        </>
      );
    }
    if (!loaded.cell.found) {
      return (
        <>
          {choosers}
          <div className="x-empty" data-refusal="cell">
            <p>{L.memoMessages["cell"]}</p>
            <p>
              <a href={toDefault}>{L.memoToFirst}</a>
            </p>
          </div>
        </>
      );
    }
    const { rows, paths } = loaded.cell;
    const at = query.run === null ? 0 : rows.findIndex((r) => r.run_id === query.run);
    if (at === -1) {
      return (
        <>
          {choosers}
          <div className="x-empty" data-refusal="run">
            <p>{L.memoMessages["run"]}</p>
            <p>
              <a href={memoHref(here, model)}>{L.memoToFirst}</a>
            </p>
          </div>
        </>
      );
    }
    const row = rows[at]!;
    const before = rows[at - 1];
    const after = rows[at + 1];
    const open = (r: MemoRow) => memoHref({ ...here, run: r.run_id }, model);
    return (
      <>
        {choosers}
        <MemoCard row={row} model={model} goal={objective} kind={kind} manifest={memoIndex!.raw_manifest} />
        <nav className="memo-prevnext" aria-label={L.memoNavLabel}>
          {before === undefined ? (
            <span className="muted">{L.memoNone}</span>
          ) : (
            <a href={open(before)} rel="prev">
              {L.memoPrevious}
            </a>
          )}
          {after === undefined ? (
            <span className="muted">{L.memoNoneNext}</span>
          ) : (
            <a href={open(after)} rel="next">
              {L.memoNext}
            </a>
          )}
        </nav>
        <section className="x-section" aria-labelledby={runsId}>
          <h2 id={runsId}>{L.memoRunsHeading}</h2>
          <ol className="memo-runs">
            {rows.map((r) => (
              <li key={r.run_id}>
                <a href={open(r)} aria-current={r.run_id === row.run_id ? "true" : undefined}>
                  <span className="mono">{r.run_id}</span> {L.memoRunLine(r.wording_id, r.repeat, r.status)}
                </a>
              </li>
            ))}
          </ol>
        </section>
        <p className="fine memo-file">
          {paths.map((path) => (
            <span key={path}>
              <a href={`/data/memos/${path}`}>{L.memoFileLink}</a> <span className="mono">{path}</span> (
              {L.memoFileNote})
            </span>
          ))}
        </p>
      </>
    );
  };

  return (
    <>
      <Title route={{ kind: "memos" }} />
      <His text={explorerHis.memosIntro} />
      {body()}
    </>
  );
}
