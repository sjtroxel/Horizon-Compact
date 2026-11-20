/**
 * The methods page, `/methods/` (Phase 6.5 IMPLEMENTATION doc section 3, decision E; step 4 built its frame, step 5
 * its words).
 *
 * The page is the outline's thirteen sections (methods.json), each with an anchor, his title (his.json) and its
 * blocks of words. A block carries the disclosure ledger's ids it states (doc section 1), and every figure in its text
 * names where it comes from: a file and the words there that hold it, or a count of the results files. methods.test.ts
 * checks each one against its source, so no number in the prose is typed without a trace. A part not written yet (one
 * that a later step fills) is a `pending` block and shows as a visibly marked placeholder (`METHODS_PLACEHOLDER`).
 * Two sections also carry data: the models, settings, dates and run counts (M3) and the published raw text's totals
 * and links (M7). Every number there is a field of a data file, shown through format.ts; nothing is typed.
 *
 * Both models are shown, the main one first, one under the other and never added together. There is no model switch.
 */
import { Fragment, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { explorerHis, explorerLabels as L, isMethodsPlaceholder, METHODS_PLACEHOLDER } from "./copy";
import type { DataApi, DataIndex, GridFile, MethodsFile, MethodsSetting, MethodsSweep } from "./data";
import { SECTIONS } from "./methodsOutline";
import type { Block, OutlineSection } from "./methodsOutline";
import { formatCount, formatUtc, sessionSpan, statusCounts } from "./format";
import { mainFileUrl, mainFolderUrl } from "./links";
import { modelName, orderedModels } from "./models";
import { Title } from "./parts";

export type { Block, CountSpec, Figure, MethodsWordsFile, OutlineSection } from "./methodsOutline";

const markClass = (text: string): string | undefined =>
  isMethodsPlaceholder(text) ? "methods-placeholder" : undefined;

/** What a section shows where its words are not written: the body placeholder, in a dashed outline. */
function BodyPlaceholder() {
  return (
    <p className="methods-placeholder" data-placeholder="body">
      {METHODS_PLACEHOLDER.body}
    </p>
  );
}

// ----------------------------------------------------------------------------------------------------------------
// M3's data: each model's settings, who served its attempts, its dates and its runs.

/** A setting as the record has it: a sentence or number as written; a flag and "none" by their labels. */
function settingText(value: MethodsSetting): string {
  if (value === null) return L.methodsNone;
  if (typeof value === "boolean") return value ? L.methodsYes : L.methodsNo;
  return String(value);
}

function SettingRows({ entries }: { entries: Array<[string, MethodsSetting]> }) {
  return (
    <>
      {entries.map(([field, value]) => (
        <tr key={field}>
          <th scope="row">{L.methodsSettingLabels[field] ?? field}</th>
          <td className="break">{settingText(value)}</td>
        </tr>
      ))}
    </>
  );
}

/** The settings a reader needs first, then every other recorded setting in a closed details part (none is dropped). */
function SettingsTable({ sweep, name }: { sweep: MethodsSweep; name: string }) {
  const all = Object.entries(sweep.settings);
  const main = all.filter(([field]) => L.methodsSettingsMain.includes(field));
  const more = all.filter(([field]) => !L.methodsSettingsMain.includes(field));
  const head = (
    <thead>
      <tr>
        <th scope="col">{L.methodsSettingColumn}</th>
        <th scope="col">{L.methodsValueColumn}</th>
      </tr>
    </thead>
  );
  return (
    <>
      <div className="x-table-wrap">
        <table className="x-table methods-kv">
          <caption>{L.methodsSettingsCaption(name)}</caption>
          {head}
          <tbody>
            <SettingRows entries={main} />
          </tbody>
        </table>
      </div>
      {more.length > 0 && (
        <details className="methods-more">
          <summary>{L.methodsSettingsMore}</summary>
          <div className="x-table-wrap">
            <table className="x-table methods-kv">
              <caption>{L.methodsSettingsCaption(name)}</caption>
              {head}
              <tbody>
                <SettingRows entries={more} />
              </tbody>
            </table>
          </div>
        </details>
      )}
    </>
  );
}

function ServedTables({ sweep, name }: { sweep: MethodsSweep; name: string }) {
  return (
    <>
      {Object.entries(sweep.served).map(([field, values]) => (
        <div className="x-table-wrap" key={field}>
          <table className="x-table">
            <caption>{L.methodsServedCaption(name, L.methodsServedLabels[field] ?? field)}</caption>
            <thead>
              <tr>
                <th scope="col">{L.methodsServedColumn}</th>
                <th scope="col" className="num">
                  {L.methodsAttemptsColumn}
                </th>
              </tr>
            </thead>
            <tbody>
              {values.map((entry) => (
                <tr key={entry.value}>
                  <th scope="row" className="break">
                    {entry.value}
                  </th>
                  <td className="num">{formatCount(entry.attempts)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </>
  );
}

function DatesTable({ sweep, name }: { sweep: MethodsSweep; name: string }) {
  const span = sessionSpan(sweep.sessions);
  return (
    <div className="x-table-wrap">
      <table className="x-table methods-kv">
        <caption>{L.methodsDatesCaption(name)}</caption>
        <tbody>
          {span !== null && (
            <>
              <tr>
                <th scope="row">{L.methodsFirstStarted}</th>
                <td>{formatUtc(span.first)}</td>
              </tr>
              <tr>
                <th scope="row">{L.methodsLastFinished}</th>
                <td>{formatUtc(span.last)}</td>
              </tr>
            </>
          )}
          <tr>
            <th scope="row">{L.methodsSessionCount}</th>
            <td>{formatCount(sweep.sessions.length)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

/** A failure type as the file words it (`sum_mismatch`), with a place to break the line after each underscore. The text is unchanged. */
function BreakableType({ text }: { text: string }) {
  const parts = text.split("_");
  return (
    <>
      {parts.map((part, i) => (
        <Fragment key={i}>
          {i > 0 && (
            <>
              _<wbr />
            </>
          )}
          {part}
        </Fragment>
      ))}
    </>
  );
}

/** The runs of each scenario of one sweep, read from its results files' cells and summed (never derived further). */
function CountsTable({ name, files }: { name: string; files: readonly GridFile[] }) {
  return (
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>{L.methodsCountsCaption(name)}</caption>
        <thead>
          <tr>
            <th scope="col">{L.methodsScenarioColumn}</th>
            <th scope="col" className="num">
              {L.methodsAttemptedColumn}
            </th>
            <th scope="col" className="num">
              {L.methodsValidColumn}
            </th>
            <th scope="col" className="num">
              {L.methodsRefusedColumn}
            </th>
            <th scope="col">{L.methodsFailedColumn}</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => {
            const counts = statusCounts(file.cells);
            return (
              <tr key={file.scenario_id} data-scenario={file.scenario_id}>
                <th scope="row">{L.scenarioNames[file.scenario_id] ?? file.scenario_id}</th>
                <td className="num">{formatCount(counts.attempted)}</td>
                <td className="num">{formatCount(counts.valid)}</td>
                <td className="num">{formatCount(counts.refused)}</td>
                <td className="break">
                  {counts.failed.length === 0
                    ? L.methodsNoFailures
                    : counts.failed.map(([type, runs], i) => (
                        <Fragment key={type}>
                          {i > 0 && ", "}
                          <BreakableType text={type} /> {formatCount(runs)}
                        </Fragment>
                      ))}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** One sweep's four parts. `name` captions every table: the model's name, or the side study's name for it. */
function SweepData({
  sweep,
  files,
  name,
}: {
  sweep: MethodsSweep;
  files: readonly GridFile[];
  name: string;
}) {
  return (
    <>
      <SettingsTable sweep={sweep} name={name} />
      <ServedTables sweep={sweep} name={name} />
      <DatesTable sweep={sweep} name={name} />
      <CountsTable name={name} files={files} />
    </>
  );
}

interface Loaded {
  /** The page's words (methods.json), checked to hold exactly the thirteen sections, in order. */
  words: OutlineSection[];
  methods: MethodsFile;
  /** Each model's main grid: its sweep, and its results file for every scenario, in the index's order. */
  grids: Array<{ sweep: MethodsSweep; files: GridFile[] }>;
  /** The side study: its sweep and its results files. */
  thinking: Array<{ sweep: MethodsSweep; files: GridFile[] }>;
}

async function loadAll(index: DataIndex, data: DataApi): Promise<Loaded> {
  const [wordsFile, methods, thinkingFiles] = await Promise.all([
    data.loadMethodsWords(),
    data.loadMethods(),
    data.loadThinking(),
  ]);
  const words = wordsFile.sections;
  const shape = (list: ReadonlyArray<{ id: string; anchor: string }>) =>
    list.map((s) => `${s.id}#${s.anchor}`).join(",");
  if (shape(words) !== shape(SECTIONS))
    throw new Error("explorer data: the methods words do not hold the thirteen sections in order");
  const sweepOf = (model: string, kind: MethodsSweep["kind"]): MethodsSweep => {
    const found = methods.sweeps.find((s) => s.model_key === model && s.kind === kind);
    if (found === undefined)
      throw new Error(`explorer data: the methods file has no ${kind} sweep for ${model}`);
    return found;
  };
  const grids = await Promise.all(
    orderedModels(index.models).map(async (m) => ({
      sweep: sweepOf(m.model_key, "grid"),
      files: await Promise.all(index.scenarios.map((s) => data.loadGrid(m.model_key, s.scenario_id))),
    })),
  );
  const thinking = orderedModels(index.models).flatMap((m) => {
    const files = thinkingFiles.filter((f) => f.model_key === m.model_key);
    return files.length === 0 ? [] : [{ sweep: sweepOf(m.model_key, "thinking"), files }];
  });
  return { words, methods, grids, thinking };
}

function ModelsData({ loaded }: { loaded: Loaded }) {
  return (
    <div className="methods-data" data-part="data">
      {loaded.grids.map(({ sweep, files }) => (
        <Fragment key={sweep.sweep_id}>
          <h3>{modelName(sweep.model_key)}</h3>
          <SweepData sweep={sweep} files={files} name={modelName(sweep.model_key)} />
        </Fragment>
      ))}
      {loaded.thinking.map(({ sweep, files }) => (
        <Fragment key={sweep.sweep_id}>
          <h3>{L.methodsSideStudy}</h3>
          <SweepData sweep={sweep} files={files} name={L.methodsSideStudyModel(modelName(sweep.model_key))} />
        </Fragment>
      ))}
    </div>
  );
}

// ----------------------------------------------------------------------------------------------------------------
// M7's data: how much raw text there is, and where it is.

function RawData({ raw }: { raw: MethodsFile["raw_text"] }) {
  return (
    <div className="methods-data" data-part="data">
      <div className="x-table-wrap">
        <table className="x-table methods-kv">
          <caption>{L.methodsRawCaption}</caption>
          <tbody>
            <tr>
              <th scope="row">{L.methodsRawObjects}</th>
              <td>{formatCount(raw.object_count)}</td>
            </tr>
            <tr>
              <th scope="row">{L.methodsRawBytes}</th>
              <td>{formatCount(raw.total_bytes)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <ul className="x-sources">
        <li>
          <a href={mainFolderUrl(raw.folder)} target="_blank" rel="noopener noreferrer">
            {L.methodsRawFolderLink}
          </a>
        </li>
        <li>
          <a href={mainFileUrl(raw.manifest)} target="_blank" rel="noopener noreferrer">
            {L.methodsRawManifestLink}
          </a>
        </li>
      </ul>
    </div>
  );
}

// ----------------------------------------------------------------------------------------------------------------
// The sections

function Lead({ text }: { text: string | undefined }) {
  return text === undefined ? null : (
    <>
      <strong>{text}</strong>{" "}
    </>
  );
}

function ObjectivesTable({ index }: { index: DataIndex }) {
  return (
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>{L.methodsGoalsCaption}</caption>
        <thead>
          <tr>
            <th scope="col">{L.methodsGoalColumn}</th>
            <th scope="col">{L.methodsWhoColumn}</th>
            <th scope="col">{L.methodsWhenColumn}</th>
          </tr>
        </thead>
        <tbody>
          {index.objectives.map((o) => (
            <tr key={o.id}>
              <th scope="row">
                {o.id}: {L.objectiveNames[o.id] ?? o.id}
              </th>
              {o.who === null || o.when === null ? (
                <td colSpan={2}>{L.methodsNoGoal}</td>
              ) : (
                <>
                  <td>{o.who}</td>
                  <td>{o.when}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScenarioList({ index }: { index: DataIndex }) {
  return (
    <ul className="methods-list">
      {index.scenarios.map((s) => (
        <li key={s.scenario_id}>
          <strong>{L.scenarioNames[s.scenario_id] ?? s.scenario_id}.</strong>{" "}
          {explorerHis.scenarioBriefs[s.scenario_id as keyof typeof explorerHis.scenarioBriefs]}{" "}
          {L.methodsScenarioResult(s.primary_outcome, String(Math.round(s.threshold * 100)))}
        </li>
      ))}
    </ul>
  );
}

/**
 * The video (step 9): it loads nothing until it is played (`preload="none"`), shows its poster, carries its captions,
 * and has its words below it as text, so a reader who cannot or will not play it loses nothing.
 */
function VideoBlock({ block }: { block: Extract<Block, { kind: "video" }> }) {
  const at = (name: string) => `/media/${name}`;
  return (
    <figure data-block="video" className="methods-video">
      <video controls preload="none" poster={at(block.poster)} title={block.title} width={1280} height={720}>
        <source src={at(block.file)} type="video/mp4" />
        <track kind="captions" src={at(block.captions)} srcLang="en" label="English" default />
        {L.methodsVideoFallback}
      </video>
      <figcaption>
        <a href={at(block.file)} download>
          {L.methodsVideoDownload}
        </a>
      </figcaption>
      <details className="methods-transcript">
        <summary>{L.methodsVideoTranscript}</summary>
        <p>{block.spoken.join(" ")}</p>
        <p>
          <strong>{L.methodsVideoOnScreen}</strong> {block.onScreen}
        </p>
      </details>
    </figure>
  );
}

/** One block of words, as methods.json has it. `data-block` names its kind, so a test can find every block. */
function BlockView({ block, index }: { block: Block; index: DataIndex }) {
  switch (block.kind) {
    case "p":
      return (
        <p data-block="p">
          <Lead text={block.lead} />
          {block.text}
        </p>
      );
    case "quote":
      return (
        <div data-block="quote">
          {block.lead !== undefined && (
            <p>
              <strong>{block.lead}</strong>
            </p>
          )}
          {block.texts.map((text) => (
            <blockquote key={text} className="methods-quote">
              <p>{text}</p>
            </blockquote>
          ))}
        </div>
      );
    case "list":
      return (
        <div data-block="list">
          {block.lead !== undefined && (
            <p>
              <strong>{block.lead}</strong>
            </p>
          )}
          <ul className="methods-list">
            {block.items.map((item) => (
              <li key={item.text}>
                {item.text}
                {item.anchor !== undefined && (
                  <>
                    {" "}
                    <a href={`#${item.anchor}`}>{L.methodsSeeSection}</a>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>
      );
    case "scope":
      return (
        <p data-block="scope" className="methods-scope">
          {explorerHis.scopeSentence}
        </p>
      );
    case "objectives":
      return (
        <div data-block="objectives">
          <ObjectivesTable index={index} />
        </div>
      );
    case "scenarios":
      return (
        <div data-block="scenarios">
          <ScenarioList index={index} />
        </div>
      );
    case "video":
      return <VideoBlock block={block} />;
    case "pending":
      return (
        <p className="methods-placeholder" data-placeholder="body" data-block="pending">
          {METHODS_PLACEHOLDER.body}
        </p>
      );
  }
}

/** A section's sources, each once, in the order its blocks name them. */
function sourcesOf(section: OutlineSection): string[] {
  const seen: string[] = [];
  for (const block of section.blocks)
    for (const source of block.sources ?? []) if (!seen.includes(source)) seen.push(source);
  return seen;
}

function Section({
  section,
  index,
  children,
}: {
  section: OutlineSection;
  index: DataIndex;
  children?: ReactNode;
}) {
  const title = explorerHis.methods.sectionTitles[section.id];
  if (title === undefined) throw new Error(`his.json has no title for methods section ${section.id}`);
  const sources = sourcesOf(section);
  const headingId = `${section.anchor}-title`;
  return (
    <section
      id={section.anchor}
      className="x-section methods-section"
      tabIndex={-1}
      aria-labelledby={headingId}
    >
      <h2 id={headingId} className={markClass(title)}>
        {title}
      </h2>
      {section.blocks.length === 0 ? (
        <BodyPlaceholder />
      ) : (
        section.blocks.map((block, i) => <BlockView key={i} block={block} index={index} />)
      )}
      {children}
      {sources.length > 0 && (
        <div className="methods-sources">
          <p>{L.methodsSourcesLabel}</p>
          <ul className="x-sources">
            {sources.map((source) => (
              <li key={source}>
                <a href={mainFileUrl(source)} target="_blank" rel="noopener noreferrer">
                  <code>{source}</code>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

interface MethodsViewProps {
  index: DataIndex;
  data: DataApi;
}

export function MethodsView({ index, data }: MethodsViewProps) {
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let live = true;
    loadAll(index, data).then(
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

  // The sections exist once the data has loaded, so an address that names one (`/methods/#real-cases`) is revealed
  // then: the shell's own reveal ran at mount, when the target was not there yet.
  useEffect(() => {
    if (loaded === null) return;
    let id = "";
    try {
      id = decodeURIComponent(window.location.hash.slice(1));
    } catch {
      return; // a malformed percent escape names nothing
    }
    const target = id === "" ? null : document.getElementById(id);
    if (target === null || !SECTIONS.some((section) => section.anchor === id)) return;
    if (typeof target.scrollIntoView === "function") target.scrollIntoView();
    target.focus({ preventScroll: true });
  }, [loaded]);

  return (
    <>
      <Title route={{ kind: "methods" }}>
        <nav className="jump-menu" aria-label={L.methodsContentsLabel}>
          <ul>
            {SECTIONS.map((section) => {
              const title = explorerHis.methods.sectionTitles[section.id] ?? section.id;
              return (
                <li key={section.id}>
                  <a href={`#${section.anchor}`} className={markClass(title)}>
                    {title}
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>
      </Title>
      {failed ? (
        <p role="alert">{L.loadFailed}</p>
      ) : loaded === null ? (
        <p role="status">{L.methodsLoading}</p>
      ) : (
        loaded.words.map((section) => (
          <Section key={section.id} section={section} index={index}>
            {section.id === "M3" && <ModelsData loaded={loaded} />}
            {section.id === "M7" && <RawData raw={loaded.methods.raw_text} />}
          </Section>
        ))
      )}
    </>
  );
}
