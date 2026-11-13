/**
 * The real cases' distance chart (Phase 6 IMPLEMENTATION doc section 8, C5 B4), drawn by hand in SVG with the same
 * mark specs as the interval chart in charts.tsx. One row per goal, never two goals in one plot area (section 24.1's
 * note on E's gray): the distance is a dot, `low` to `high` a line, on a 0 to 1 axis, and `d_star` a rule labeled as
 * the no-good-match line. The goal's color is a secondary carrier; every row names its goal in text, and every
 * number is in text beside the row.
 *
 * The chart sits in a figure whose caption names the case, the model and the reading, so a crop of the figure keeps
 * them. Colors carry no verdict.
 */
import { explorerLabels as L } from "./copy";
import type { CaseReading } from "./data";
import { axisPercent, confidenceLevel, edgeAnchor, formatDistance } from "./format";
import { goalClass } from "./chartData";
import { Frame } from "./ChartCard";
import type { Names } from "./charts";
import { explorerHis } from "./copy";
import { HisInline } from "./parts";

const ROW_H = 30;
const MID = 15;
const AXIS = { low: 0, high: 1 } as const;
const TICKS = [0, 0.5, 1] as const;

export interface DistanceChartProps {
  caseLabel: string;
  /** The model's name as the page calls it. */
  model: string;
  /** The reading's name as the page calls it ("Primary reading"). */
  readingName: string;
  /** The matcher's label for the reading, in words. */
  labelWord: string;
  reading: CaseReading;
  /** `thresholds.d_star` of the case file: the no-good-match line. */
  dStar: number;
  /** `thresholds.alpha` of the case file, for the interval's level. */
  alpha: number;
  names: Names;
}

export function DistanceChart({
  caseLabel,
  model,
  readingName,
  labelWord,
  reading,
  dStar,
  alpha,
  names,
}: DistanceChartProps) {
  const { low, high } = AXIS;
  const rule = formatDistance(dStar);
  return (
    <Frame
      title={L.chartTitles.distance}
      unit={L.distanceLevel(confidenceLevel(alpha))}
      className="distance-figure"
      data-reading={reading.reading}
      note={
        <figcaption>
          <span className="mono">{caseLabel}</span>
          {" · "}
          <span className="model-name">{model}</span>
          {" · "}
          {readingName}
          {" · "}
          {labelWord}
          {" · "}
          <HisInline text={explorerHis.scopeShort} />
        </figcaption>
      }
    >
      <div
        className="chart distances"
        role="group"
        aria-label={L.distanceChartLabel(caseLabel, model, readingName)}
      >
        {reading.distances.map((d) => {
          const numbers = L.distanceRowNumbers(
            formatDistance(d.distance),
            formatDistance(d.low),
            formatDistance(d.high),
          );
          return (
            <div
              key={d.objective_id}
              className={`distance-row ${goalClass(d.objective_id)}`}
              data-goal={d.objective_id}
            >
              <div className="goal-label">
                <span className="swatch" aria-hidden="true" />
                <span className="goal-name">
                  {names[d.objective_id] ?? d.objective_id} <span className="letter">({d.objective_id})</span>
                </span>
              </div>
              <svg className="x-plot" width="100%" height={ROW_H} aria-hidden="true">
                {TICKS.map((v) => (
                  <line
                    key={v}
                    className="gridline"
                    x1={axisPercent(v, low, high)}
                    x2={axisPercent(v, low, high)}
                    y1={0}
                    y2={ROW_H}
                  />
                ))}
                <line
                  className="x-rule"
                  x1={axisPercent(dStar, low, high)}
                  x2={axisPercent(dStar, low, high)}
                  y1={0}
                  y2={ROW_H}
                />
                <line
                  className="d-range"
                  x1={axisPercent(d.low, low, high)}
                  x2={axisPercent(d.high, low, high)}
                  y1={MID}
                  y2={MID}
                />
                <circle className="d-dot" cx={axisPercent(d.distance, low, high)} cy={MID} r={5} />
              </svg>
              <div className="distance-numbers">
                <span>{numbers}</span>
                <span className="muted">
                  {L.distanceRunsPlain(d.runs, d.choice_only_runs, d.undistanced_runs)}
                </span>
              </div>
            </div>
          );
        })}
        <div className="distance-row distance-axis" aria-hidden="true">
          <span />
          <svg className="x-plot" width="100%" height={40}>
            <line
              className="axisline"
              x1={axisPercent(TICKS[0], low, high)}
              x2={axisPercent(TICKS[TICKS.length - 1]!, low, high)}
              y1={2}
              y2={2}
            />
            {TICKS.map((v) => (
              <text
                key={v}
                className="tick"
                x={axisPercent(v, low, high)}
                y={18}
                textAnchor={edgeAnchor(v, low, high)}
              >
                {formatDistance(v, 1)}
              </text>
            ))}
            <text className="tick edge" x={axisPercent(dStar, low, high)} y={34} textAnchor="middle">
              {L.distanceRule(rule)}
            </text>
          </svg>
        </div>
        <p className="axis-caption">{L.distanceAxis}</p>
      </div>
    </Frame>
  );
}
