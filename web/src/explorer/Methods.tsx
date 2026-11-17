/**
 * The methods page, `/methods/` (Phase 6.5 IMPLEMENTATION doc section 3, decision E; step 4 builds its frame).
 *
 * The frame is the outline's thirteen sections (methods.json), each with an anchor, his title (his.json) and a body.
 * **No sentence of the page is written in this step**: a title or a body that is not written yet shows as a visibly
 * marked placeholder (`METHODS_PLACEHOLDER`), so nobody takes this preview for a finished page. Two sections carry
 * data now, because they need no prose: the models, settings, dates and run counts (M3) and the published raw text's
 * totals and links (M7). Every number there is a field of a data file, shown through format.ts; nothing is typed.
 *
 * Both models are shown, the main one first, one under the other and never added together. There is no model switch.
 */
import { Fragment, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { explorerHis, explorerLabels as L, isMethodsPlaceholder, METHODS_PLACEHOLDER } from "./copy";
import type { DataApi, DataIndex, GridFile, MethodsFile, MethodsSetting, MethodsSweep } from "./data";
import { formatCount, formatUtc, sessionSpan, statusCounts } from "./format";
import { mainFileUrl, mainFolderUrl } from "./links";
import outlineJson from "./methods.json";
import { modelName, orderedModels } from "./models";
import { Title } from "./parts";

/** One section of the outline: the file's shape, which step 5's test also reads. */
export interface OutlineSection {
  id: string;
  anchor: string;
  /** The disclosure ledger's line ids (doc section 1) this section carries. */
  ledger: string[];
  /** What else the outline's column names (Delivers and definition-of-done rows) when it gives no ledger line. */
  also: string[];
  /** The section's blocks of words, written in step 5. Empty until then: the body placeholder shows. */
  blocks: unknown[];
}

export const OUTLINE: readonly OutlineSection[] = outlineJson.sections;

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

function SettingsTable({ sweep }: { sweep: MethodsSweep }) {
  return (
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>{L.methodsSettingsCaption(modelName(sweep.model_key))}</caption>
        <thead>
          <tr>
            <th scope="col">{L.methodsSettingColumn}</th>
            <th scope="col">{L.methodsValueColumn}</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(sweep.settings).map(([field, value]) => (
            <tr key={field}>
              <th scope="row">{L.methodsSettingLabels[field] ?? field}</th>
              <td className="break">{settingText(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ServedTables({ sweep }: { sweep: MethodsSweep }) {
  return (
    <>
      {Object.entries(sweep.served).map(([field, values]) => (
        <div className="x-table-wrap" key={field}>
          <table className="x-table">
            <caption>
              {L.methodsServedCaption(modelName(sweep.model_key), L.methodsServedLabels[field] ?? field)}
            </caption>
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

function DatesTable({ sweep }: { sweep: MethodsSweep }) {
  const span = sessionSpan(sweep.sessions);
  return (
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>{L.methodsDatesCaption(modelName(sweep.model_key))}</caption>
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
function CountsTable({ model, files }: { model: string; files: readonly GridFile[] }) {
  return (
    <div className="x-table-wrap">
      <table className="x-table">
        <caption>{L.methodsCountsCaption(modelName(model))}</caption>
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

function SweepData({ sweep, files }: { sweep: MethodsSweep; files: readonly GridFile[] }) {
  return (
    <>
      <SettingsTable sweep={sweep} />
      <ServedTables sweep={sweep} />
      <DatesTable sweep={sweep} />
      <CountsTable model={sweep.model_key} files={files} />
    </>
  );
}

interface Loaded {
  methods: MethodsFile;
  /** Each model's main grid: its sweep, and its results file for every scenario, in the index's order. */
  grids: Array<{ sweep: MethodsSweep; files: GridFile[] }>;
  /** The side study: its sweep and its results files. */
  thinking: Array<{ sweep: MethodsSweep; files: GridFile[] }>;
}

async function loadAll(index: DataIndex, data: DataApi): Promise<Loaded> {
  const [methods, thinkingFiles] = await Promise.all([data.loadMethods(), data.loadThinking()]);
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
  return { methods, grids, thinking };
}

function ModelsData({ loaded }: { loaded: Loaded }) {
  return (
    <div className="methods-data" data-part="data">
      {loaded.grids.map(({ sweep, files }) => (
        <Fragment key={sweep.sweep_id}>
          <h3>{modelName(sweep.model_key)}</h3>
          <SweepData sweep={sweep} files={files} />
        </Fragment>
      ))}
      {loaded.thinking.map(({ sweep, files }) => (
        <Fragment key={sweep.sweep_id}>
          <h3>{L.methodsSideStudy}</h3>
          <SweepData sweep={sweep} files={files} />
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
        <table className="x-table">
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

function Section({ section, children }: { section: OutlineSection; children?: ReactNode }) {
  const title = explorerHis.methods.sectionTitles[section.id];
  if (title === undefined) throw new Error(`his.json has no title for methods section ${section.id}`);
  if (section.blocks.length > 0) {
    // Step 5 gives blocks a renderer; until it does, a block must not be dropped without a word.
    throw new Error(`methods section ${section.id} has blocks and the page has no renderer for them yet`);
  }
  return (
    // No aria-labelledby: a labelled section is a landmark, and until his titles replace the placeholders thirteen of
    // them would share one name (axe: landmark-unique). The heading gives the structure.
    <section id={section.anchor} className="x-section methods-section" tabIndex={-1}>
      <h2 className={markClass(title)}>{title}</h2>
      <BodyPlaceholder />
      {children}
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
    if (target === null || !OUTLINE.some((section) => section.anchor === id)) return;
    if (typeof target.scrollIntoView === "function") target.scrollIntoView();
    target.focus({ preventScroll: true });
  }, [loaded]);

  return (
    <>
      <Title route={{ kind: "methods" }}>
        <nav className="jump-menu" aria-label={L.methodsContentsLabel}>
          <ul>
            {OUTLINE.map((section) => {
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
        OUTLINE.map((section) => (
          <Section key={section.id} section={section}>
            {section.id === "M3" && <ModelsData loaded={loaded} />}
            {section.id === "M7" && <RawData raw={loaded.methods.raw_text} />}
          </Section>
        ))
      )}
    </>
  );
}
