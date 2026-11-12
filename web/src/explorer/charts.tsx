/**
 * The scenario view's charts, drawn by hand in SVG (no chart library). Every position is a value from the data
 * mapped to an axis, or a jitter from a hash of the run id (format.ts); every number written as text is a field of
 * the data formatted by format.ts. Colors come from classes (`goal-a` to `goal-e` set `--goal`), never from a style
 * attribute: the site's content security policy forbids inline styles.
 *
 * A goal is never carried by color alone: every row and panel names its goal in text.
 *
 * Plot areas are SVG elements at 100% width with percentage coordinates and a fixed height, so a dot stays round at
 * any width and the labels, which are HTML, stay readable.
 */
import { explorerLabels as L } from "./copy";
import type { GridComparison, GridFile, PerRun, Verdict } from "./data";
import {
  choiceOrder,
  goalClass,
  goalLines,
  goalRunCount,
  goalSplit,
  leverShare,
  runsOfGoal,
} from "./chartData";
import {
  axisExtent,
  axisPercent,
  axisSpan,
  dotY,
  edgeAnchor,
  formatDifference,
  formatPercent,
  formatPoints,
  unitBox,
  unitSlot,
  wordsSide,
} from "./format";

export type Names = Readonly<Record<string, string>>;

const nameOf = (names: Names, goal: string) => names[goal] ?? goal;

/** A goal's label: its swatch, its plain name, and the letter beside it, then its run count. */
function GoalLabel({ goal, names, count }: { goal: string; names: Names; count: number }) {
  return (
    <div className="goal-label">
      <span className="swatch" aria-hidden="true" />
      <span className="goal-name">
        {nameOf(names, goal)} <span className="letter">({goal})</span>
      </span>
      <span className="goal-count">{L.runCount(count)}</span>
    </div>
  );
}

const STRIP_H = 40;
const STRIP_JITTER = 18;

/**
 * Page 6's strip for a share scenario: one row per goal, every valid run one dot at its primary outcome, 0 to 1.
 * No ticks, no interval, no threshold and no mean: the data has no per-goal mean or interval for the primary
 * outcome, so none is drawn (Phase 6 IMPLEMENTATION doc section 24, finding 2).
 */
export function ShareStrip({
  file,
  goals,
  names,
  hidden,
  label,
  wording,
}: {
  file: GridFile;
  goals: readonly string[];
  names: Names;
  hidden: ReadonlySet<string>;
  label: string;
  /** Only this wording's runs, and its count (the studies view sets the grid beside the sub-study's wording). */
  wording?: string | undefined;
}) {
  const ends = L.axisEnds[file.scenario_id];
  return (
    <div className="chart strip" role="img" aria-label={label}>
      {goals.map((goal) => {
        const off = hidden.has(goal);
        return (
          <div
            key={goal}
            className={`goal-row ${goalClass(goal)}`}
            data-goal={goal}
            data-off={off ? "true" : "false"}
            aria-hidden={off ? true : undefined}
          >
            <GoalLabel goal={goal} names={names} count={goalRunCount(file, goal, wording)} />
            <svg className="x-plot" width="100%" height={STRIP_H}>
              {[0, 0.5, 1].map((v) => (
                <line
                  key={v}
                  className="gridline"
                  x1={axisPercent(v, 0, 1)}
                  x2={axisPercent(v, 0, 1)}
                  y1={0}
                  y2={STRIP_H}
                />
              ))}
              {runsOfGoal(file, goal, wording).map((run) => (
                <circle
                  key={run.run_id}
                  className="x-dot"
                  cx={axisPercent(run.primary, 0, 1)}
                  cy={dotY(STRIP_H, run.run_id, STRIP_JITTER)}
                  r={4.5}
                >
                  <title>
                    {L.dotTitleShare(
                      nameOf(names, goal),
                      run.wording_id,
                      run.repeat,
                      formatPercent(run.primary),
                    )}
                  </title>
                </circle>
              ))}
            </svg>
          </div>
        );
      })}
      {ends && (
        <div className="axis-ends" aria-hidden="true">
          <span className="axis-title">{ends.title}</span>
          <div className="axis-words">
            <span>{ends.low}</span>
            <span>{ends.mid}</span>
            <span>{ends.high}</span>
          </div>
        </div>
      )}
    </div>
  );
}

const UNIT_STEP = 12;
const UNIT_R = 4.5;
const UNIT_PER_ROW = 10;

/**
 * Page 6's unit chart for a choice scenario: columns are the choices, in the order of the split's counts; each run
 * one dot under the choice it made, ten to a row, and "n of N" under each group, both from the goal's split.
 */
export function ChoiceUnits({
  file,
  goals,
  names,
  hidden,
  label,
}: {
  file: GridFile;
  goals: readonly string[];
  names: Names;
  hidden: ReadonlySet<string>;
  label: string;
}) {
  const choices = choiceOrder(file);
  return (
    <div className="chart units" role="img" aria-label={label}>
      <div className="goal-row units-head" aria-hidden="true">
        <span />
        <div className="unit-cols">
          {choices.map((choice) => (
            <span key={choice} className="unit-head">
              {L.choices[choice] ?? choice}
            </span>
          ))}
        </div>
      </div>
      {goals.map((goal) => {
        const off = hidden.has(goal);
        const split = goalSplit(file, goal);
        const runs = runsOfGoal(file, goal);
        return (
          <div
            key={goal}
            className={`goal-row ${goalClass(goal)}`}
            data-goal={goal}
            data-off={off ? "true" : "false"}
            aria-hidden={off ? true : undefined}
          >
            <GoalLabel goal={goal} names={names} count={goalRunCount(file, goal)} />
            <div className="unit-cols">
              {choices.map((choice) => {
                const made = runs.filter((run) => run.choice === choice);
                const count = split?.counts.find(([key]) => key === choice)?.[1] ?? 0;
                const box = unitBox(made.length, UNIT_PER_ROW, UNIT_STEP);
                return (
                  <div key={choice} className="unit-col">
                    <svg className="unit-svg" viewBox={`0 0 ${box.width} ${box.height}`} width="100%">
                      {made.map((run, i) => {
                        const slot = unitSlot(i, UNIT_PER_ROW, UNIT_STEP);
                        return (
                          <circle key={run.run_id} className="x-dot" cx={slot.x} cy={slot.y} r={UNIT_R}>
                            <title>
                              {L.dotTitleChoice(
                                nameOf(names, goal),
                                run.wording_id,
                                run.repeat,
                                L.choices[choice] ?? choice,
                              )}
                            </title>
                          </circle>
                        );
                      })}
                    </svg>
                    <span className="n-of-n">{L.nOfN(count, split?.runs ?? 0)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ----------------------------------------------------------------------------------------------------------------
// The comparison interval chart (Phase 6 IMPLEMENTATION doc section 7 (iii), drawn to protocol section 6.3).

/** The fields of a comparison the interval chart draws. */
export interface IntervalRow {
  first: string;
  second: string;
  secondary: boolean;
  difference: number | null;
  low: number | null;
  high: number | null;
  threshold: number;
  verdict: Verdict;
}

export function rowOfComparison(comparison: GridComparison): IntervalRow {
  return {
    first: comparison.first,
    second: comparison.second,
    secondary: comparison.role === "secondary",
    difference: comparison.difference,
    low: comparison.low,
    high: comparison.high,
    threshold: comparison.threshold,
    verdict: comparison.final_verdict,
  };
}

const INTERVAL_AXIS = { low: -1, high: 1 } as const;
const INTERVAL_TICKS = [-1, -0.5, 0, 0.5, 1] as const;
const INTERVAL_H = 50;
const INTERVAL_MID = 32; // the interval's line; the difference is written above its dot, the verdict beside its end
const WORDS_GAP = 12; // pixels between the end of an interval and its verdict word

/**
 * One row per comparison: the difference as a dot with its value written above it, `low` to `high` as a line with the
 * verdict word beside it, zero as a rule and the threshold band at plus and minus `threshold`. The verdict word is the
 * authority. The geometry does not decide a verdict and is not read as one: a split also needs the difference at the
 * threshold (protocol 6.3), and the floor and the constant check are not geometry. A row that is not assessable has no
 * line and says so. The plot is one image for a screen reader, labelled with the pair, the verdict and the numbers.
 */
export function IntervalChart({
  rows,
  names,
  label,
}: {
  rows: readonly IntervalRow[];
  names: Names;
  label: string;
}) {
  const { low, high } = INTERVAL_AXIS;
  const threshold = rows[0]?.threshold ?? 0;
  return (
    <div className="chart intervals" role="group" aria-label={label}>
      {rows.map((row) => {
        const pair = `${row.first} vs ${row.second}`;
        const numbers = formatDifference(row.difference, row.low, row.high);
        const verdict = L.verdictWords[row.verdict] ?? row.verdict;
        const drawn = row.difference !== null && row.low !== null && row.high !== null;
        const right = drawn ? wordsSide(row.low!, row.high!, low, high) === "right" : true;
        return (
          <div key={pair} className="interval-row">
            <div className="interval-label">
              <b>{pair}</b>
              {row.secondary && <span className="muted"> {L.secondaryFlag.toLowerCase()}</span>}
              <span className="interval-names">
                {nameOf(names, row.first)} vs {nameOf(names, row.second)}
              </span>
              {numbers === null && <span className="muted interval-none">{L.intervalRowNotAssessable}</span>}
            </div>
            <svg
              className="x-plot"
              width="100%"
              height={INTERVAL_H}
              role="img"
              aria-label={`${pair}: ${verdict}${numbers === null ? "" : `, ${numbers}`}`}
            >
              <rect
                className="band"
                x={axisPercent(-row.threshold, low, high)}
                width={axisSpan(-row.threshold, row.threshold, low, high)}
                y={0}
                height={INTERVAL_H}
              />
              <line
                className="x-zero"
                x1={axisPercent(0, low, high)}
                x2={axisPercent(0, low, high)}
                y1={0}
                y2={INTERVAL_H}
              />
              {drawn ? (
                <>
                  <line
                    className="interval"
                    x1={axisPercent(row.low!, low, high)}
                    x2={axisPercent(row.high!, low, high)}
                    y1={INTERVAL_MID}
                    y2={INTERVAL_MID}
                  >
                    <title>{`${pair}: ${numbers ?? ""}`}</title>
                  </line>
                  <circle
                    className="diff"
                    cx={axisPercent(row.difference!, low, high)}
                    cy={INTERVAL_MID}
                    r={5}
                  />
                  <text
                    className="diff-value"
                    x={axisPercent(row.difference!, low, high)}
                    y={INTERVAL_MID - 12}
                    textAnchor={edgeAnchor(row.difference!, low, high)}
                  >
                    {formatPoints(row.difference!)}
                  </text>
                  <text
                    className="verdict-word"
                    x={axisPercent(right ? row.high! : row.low!, low, high)}
                    dx={right ? WORDS_GAP : -WORDS_GAP}
                    y={INTERVAL_MID + 5}
                    textAnchor={right ? "start" : "end"}
                  >
                    {verdict}
                  </text>
                </>
              ) : (
                <text
                  className="verdict-word"
                  x={axisPercent(0, low, high)}
                  dx={WORDS_GAP}
                  y={INTERVAL_MID + 5}
                  textAnchor="start"
                >
                  {verdict}
                </text>
              )}
            </svg>
          </div>
        );
      })}
      <div className="interval-row interval-axis" aria-hidden="true">
        <span />
        <svg className="x-plot" width="100%" height={40}>
          <line
            className="axisline"
            x1={axisPercent(INTERVAL_TICKS[0], low, high)}
            x2={axisPercent(INTERVAL_TICKS[INTERVAL_TICKS.length - 1]!, low, high)}
            y1={2}
            y2={2}
          />
          {INTERVAL_TICKS.map((v) => (
            <text
              key={v}
              className="tick"
              x={axisPercent(v, low, high)}
              y={18}
              textAnchor={edgeAnchor(v, low, high)}
            >
              {formatPoints(v, 0)}
            </text>
          ))}
          {[-threshold, threshold].map((v) => (
            <text key={v} className="tick edge" x={axisPercent(v, low, high)} y={34} textAnchor="middle">
              {formatPoints(v, 0)}
            </text>
          ))}
        </svg>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------------------------------------------------------
// The full allocation (Phase 6 IMPLEMENTATION doc section 7 (ii)): small multiples.

const LEVER_H = 26;
const LEVER_JITTER = 12;

/** One panel per goal, one row per lever in canonical order, every run one dot at its share of that lever. */
export function AllocationPanels({
  file,
  goals,
  names,
}: {
  file: GridFile;
  goals: readonly string[];
  names: Names;
}) {
  // One scale per lever, shared by every goal's panel: 0 to 1, or the data's own highest share where it is higher.
  const extent = (lever: string) =>
    axisExtent(
      goals.flatMap((goal) =>
        goalLines(file, goal)
          .filter((line) => line.key === lever)
          .map((line) => line.summary.maximum),
      ),
    );
  return (
    <div className="x-panels">
      {goals.map((goal) => {
        const runs: PerRun[] = runsOfGoal(file, goal);
        const lines = goalLines(file, goal);
        return (
          <div key={goal} className={`x-panel ${goalClass(goal)}`} data-goal={goal}>
            <h4 className="panel-title">
              <span className="swatch" aria-hidden="true" />
              {nameOf(names, goal)} <span className="letter">({goal})</span>
              <span className="goal-count">{L.runCount(goalRunCount(file, goal))}</span>
            </h4>
            <div className="chart lever-plots">
              {lines.map((line) => {
                const leverName = L.levers[line.key] ?? line.key;
                const top = extent(line.key);
                return (
                  <div key={line.key} className="lever-row">
                    <span className="lever-label">
                      {leverName}
                      {top > 1 && (
                        <span className="fine lever-scale">{L.leverScale(formatPercent(top, 0))}</span>
                      )}
                    </span>
                    <svg className="x-plot" width="100%" height={LEVER_H} aria-hidden="true">
                      {[0, 0.5, 1].map((v) => (
                        <line
                          key={v}
                          className="gridline"
                          x1={axisPercent(v, 0, 1)}
                          x2={axisPercent(v, 0, 1)}
                          y1={0}
                          y2={LEVER_H}
                        />
                      ))}
                      {runs.map((run) => {
                        const share = leverShare(run, line.key);
                        if (share === undefined) return null;
                        return (
                          <circle
                            key={run.run_id}
                            className="x-dot x-small"
                            cx={axisPercent(share, 0, top)}
                            cy={dotY(LEVER_H, run.run_id, LEVER_JITTER)}
                            r={3.5}
                          >
                            <title>
                              {L.dotTitleShare(leverName, run.wording_id, run.repeat, formatPercent(share))}
                            </title>
                          </circle>
                        );
                      })}
                    </svg>
                  </div>
                );
              })}
              <div className="lever-row lever-axis" aria-hidden="true">
                <span />
                <div className="axis-words">
                  {[0, 0.5, 1].map((v) => (
                    <span key={v}>{formatPercent(v, 0)}</span>
                  ))}
                </div>
              </div>
            </div>
            <div className="table-wrap">
              <table className="x-table summary">
                <caption>{L.summaryHeading(nameOf(names, goal))}</caption>
                <thead>
                  <tr>
                    <th scope="col">{L.th.lever}</th>
                    <th scope="col" className="num">
                      {L.th.n}
                    </th>
                    <th scope="col" className="num">
                      {L.th.mean}
                    </th>
                    <th scope="col" className="num">
                      {L.th.median}
                    </th>
                    <th scope="col" className="num">
                      {L.th.minimum}
                    </th>
                    <th scope="col" className="num">
                      {L.th.maximum}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line) => (
                    <tr key={line.key}>
                      <th scope="row">{L.levers[line.key] ?? line.key}</th>
                      <td className="num">{line.summary.n}</td>
                      <td className="num">{formatPercent(line.summary.mean)}</td>
                      <td className="num">{formatPercent(line.summary.median)}</td>
                      <td className="num">{formatPercent(line.summary.minimum)}</td>
                      <td className="num">{formatPercent(line.summary.maximum)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
