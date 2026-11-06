import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent, Ref } from "react";
import { labels } from "../copy";
import { TICKS, data, money, percent } from "../data";
import type { Cell, Line, Run } from "../data";

/** A run being traced, and where the tooltip sits. */
export interface Trace {
  runId: string;
  objectiveId: string;
  lineKey: string;
  source: "pointer" | "focus";
}

export interface ChartProps {
  chosen: string;
  traced: Trace | null;
  onTrace: (trace: Trace, anchor: HTMLElement) => void;
  onClear: () => void;
}

const REPEATS_PER_LINE = 3;

function openDay(counts: Record<string, number>): string {
  return Object.entries(counts)
    .filter(([, n]) => n > 0)
    .map(([season, n]) => `${season} ${n}`)
    .join(", ");
}

interface PanelProps {
  cell: Cell;
  runs: Run[];
  isChosen: boolean;
  /** Set only on the chosen panel, so the chart can bring it into view. */
  panelRef?: Ref<HTMLDivElement> | undefined;
  traced: Trace | null;
  onTrace: ChartProps["onTrace"];
  onClear: () => void;
}

function Panel({ cell, runs, isChosen, panelRef, traced, onTrace, onClear }: PanelProps) {
  const id = cell.objective_id;
  const name = labels.priorities[id] ?? id;
  const lines = data.scenario.lines;
  const tracingHere = traced !== null && traced.objectiveId === id;

  // One tab stop per panel: only the active dot is in the tab order, and the arrow keys move the active one.
  const dots = useRef<Array<HTMLButtonElement | null>>([]);
  const [active, setActive] = useState(0);

  const dotsInOrder = lines.flatMap((line) => runs.map((run) => ({ line, run })));

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      onClear();
      return;
    }
    const current = dots.current.indexOf(document.activeElement as HTMLButtonElement);
    if (current < 0) return;
    const step = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: REPEATS_PER_LINE, ArrowUp: -REPEATS_PER_LINE }[
      event.key as "ArrowRight"
    ];
    if (step === undefined) return;
    event.preventDefault();
    const next = Math.min(Math.max(current + step, 0), dotsInOrder.length - 1);
    setActive(next);
    dots.current[next]?.focus();
  }

  function renderRow(line: Line) {
    const mean = cell.lines[line.key]?.mean ?? null;
    const base = dotsInOrder.findIndex((d) => d.line.key === line.key);
    return (
      <div className="row" key={line.key}>
        <div className="label">{line.label}</div>
        <div className="plot">
          {TICKS.map((t) => (
            <span className="g" key={t} style={{ left: percent(t) }} />
          ))}
          <span className="cap" style={{ left: percent(line.cap) }} />
          {mean !== null && <span className="mean" style={{ left: percent(mean) }} />}
          {runs.map((run, i) => {
            const amount = run.amounts[line.key] ?? 0;
            const index = base + i;
            const lit = traced !== null && traced.runId === run.run_id;
            return (
              <button
                key={run.run_id}
                ref={(el) => {
                  dots.current[index] = el;
                }}
                type="button"
                className={lit ? "dot on" : "dot"}
                tabIndex={index === active ? 0 : -1}
                style={{ left: percent(amount), top: `${50 + (i - (runs.length - 1) / 2) * 22}%` }}
                aria-label={`${money(amount)}, ${line.label}, ${labels.tooltipRun} ${run.run_id}, ${run.status}`}
                onPointerEnter={(e) =>
                  onTrace(
                    { runId: run.run_id, objectiveId: id, lineKey: line.key, source: "pointer" },
                    e.currentTarget,
                  )
                }
                onFocus={(e) => {
                  setActive(index);
                  onTrace(
                    { runId: run.run_id, objectiveId: id, lineKey: line.key, source: "focus" },
                    e.currentTarget,
                  );
                }}
              />
            );
          })}
        </div>
      </div>
    );
  }

  const classes = ["panel"];
  if (tracingHere) classes.push("tracing");
  if (isChosen) classes.push("chosen");

  return (
    <div
      ref={panelRef}
      className={classes.join(" ")}
      role="group"
      aria-label={name}
      data-priority={id}
      onKeyDown={onKeyDown}
      onPointerLeave={onClear}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) onClear();
      }}
    >
      <h3>{name}</h3>
      <p className="meta">
        {labels.runCount(cell.runs)}; {labels.openDay}: {openDay(cell.choice_counts)}; {labels.testLabel}
      </p>
      {(["source", "use"] as const).map((kind) => (
        <div className="kind" key={kind}>
          <div className="group">{kind === "source" ? labels.sources : labels.uses}</div>
          {lines.filter((line) => line.kind === kind).map(renderRow)}
        </div>
      ))}
      <div className="axis">
        <span />
        <div className="ticks">
          {TICKS.map((t) => (
            <span className="t" key={t} style={{ left: percent(t) }}>
              {money(t)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export function Chart({ chosen, traced, onTrace, onClear }: ChartProps) {
  // On a phone the panels stack in one column, so a chosen panel can sit below the fold while the others dim. When
  // a priority is chosen and its panel is not fully in the viewport, bring it in with its top just below the top
  // edge (the panel's scroll-margin-top). A panel already in view does not move the page. No smooth scroll under
  // reduced motion. In the two-column layout (54rem and up, styles.css) the page never moves: there it would carry
  // the control off screen at every choice (his decision at review, IMPLEMENTATION doc section 23).
  const chosenPanel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const panel = chosenPanel.current;
    if (chosen === "all" || panel === null) return;
    const media = (query: string) =>
      typeof window.matchMedia === "function" && window.matchMedia(query).matches;
    if (media("(min-width: 54rem)")) return;
    const rect = panel.getBoundingClientRect();
    if (rect.top >= 0 && rect.bottom <= window.innerHeight) return;
    const reduced = media("(prefers-reduced-motion: reduce)");
    panel.scrollIntoView?.({ block: "start", behavior: reduced ? "auto" : "smooth" });
  }, [chosen]);

  return (
    <div className={chosen === "all" ? "panels" : "panels focus"}>
      {data.cells.map((cell) => (
        <Panel
          key={cell.objective_id}
          cell={cell}
          runs={data.runs
            .filter((r) => r.objective_id === cell.objective_id)
            .sort((a, b) => a.repeat - b.repeat)}
          isChosen={chosen === cell.objective_id}
          panelRef={chosen === cell.objective_id ? chosenPanel : undefined}
          traced={traced}
          onTrace={onTrace}
          onClear={onClear}
        />
      ))}
    </div>
  );
}

export interface TipState {
  show: boolean;
  amount: string;
  line: string;
  runId: string;
  status: string;
  left: number;
  top: number;
}

/** The tooltip enhances and never gates: every value is also in the run table. It eases in above the dot. */
export function Tooltip({ tip }: { tip: TipState }) {
  return (
    <div
      className={tip.show ? "tip show" : "tip"}
      aria-hidden="true"
      style={{ left: tip.left, top: tip.top }}
    >
      <b>{tip.amount}</b>
      {tip.line}
      <br />
      {tip.runId}, {tip.status}
    </div>
  );
}
