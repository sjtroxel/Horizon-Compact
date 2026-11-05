import { useCallback, useEffect, useRef, useState } from "react";
import { Chart, Tooltip } from "./components/Chart";
import type { TipState, Trace } from "./components/Chart";
import { Control } from "./components/Control";
import { Footer } from "./components/Footer";
import { Logo } from "./components/Logo";
import { Provenance } from "./components/Provenance";
import { RunsTable, StatusTable } from "./components/Tables";
import { his, isPlaceholder, labels } from "./copy";
import { data, money } from "./data";

/** A paragraph or heading of his words; while it is still a marked placeholder it shows in the secondary ink. */
function His({
  as: Tag,
  text,
  className,
  id,
}: {
  as: "h2" | "p";
  text: string;
  className?: string;
  id?: string;
}) {
  const classes = [className, isPlaceholder(text) ? "placeholder" : undefined].filter(Boolean).join(" ");
  return (
    <Tag id={id} className={classes || undefined}>
      {text}
    </Tag>
  );
}

const HIDDEN_TIP: TipState = { show: false, amount: "", line: "", runId: "", status: "", left: 0, top: 0 };

function tipPosition(anchor: HTMLElement): { left: number; top: number } {
  const r = anchor.getBoundingClientRect();
  return {
    left: Math.min(Math.max(r.left + r.width / 2, 120), window.innerWidth - 120),
    top: r.top + 6,
  };
}

export function App() {
  const [chosen, setChosen] = useState("all");
  const [traced, setTraced] = useState<Trace | null>(null);
  const [tip, setTip] = useState<TipState>(HIDDEN_TIP);
  const anchor = useRef<HTMLElement | null>(null);

  // A marker for the browser check (the content security policy proof): set once the app has mounted.
  useEffect(() => {
    document.documentElement.dataset["mounted"] = "yes";
  }, []);

  const onTrace = useCallback((trace: Trace, el: HTMLElement) => {
    anchor.current = el;
    const run = data.runs.find((r) => r.run_id === trace.runId);
    const line = data.scenario.lines.find((l) => l.key === trace.lineKey);
    if (!run || !line) return;
    setTraced((current) =>
      current && current.runId === trace.runId && current.source === trace.source ? current : trace,
    );
    setTip({
      show: true,
      amount: money(run.amounts[line.key] ?? 0),
      line: line.label,
      runId: run.run_id,
      status: run.status,
      ...tipPosition(el),
    });
  }, []);

  const onClear = useCallback(() => {
    anchor.current = null;
    setTraced(null);
    setTip((current) => (current.show ? { ...current, show: false } : current));
  }, []);

  // A scroll clears a pointer's trace. A keyboard user's focus scrolls the page by itself, so a focused dot keeps
  // its trace and the tooltip follows it.
  const source = traced?.source ?? null;
  useEffect(() => {
    if (source === null) return;
    const onScroll = () => {
      if (source === "pointer" || anchor.current === null) {
        onClear();
        return;
      }
      const position = tipPosition(anchor.current);
      setTip((current) => ({ ...current, ...position }));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [source, onClear]);

  return (
    <>
      {his.description !== "" && <meta name="description" content={his.description} />}
      <main>
        <header className="hero">
          <div className="brand">
            <Logo />
          </div>
          <h1>Horizon Compact</h1>
          <His as="p" className="lede" text={his.lede} />
          <His as="p" className="notice" text={his.notice} />
        </header>

        <section aria-labelledby="chart-title">
          <h2 id="chart-title">{labels.chartTitle}</h2>
          <p className="key">{labels.chartKey}</p>
          <Control
            chosen={chosen}
            onChoose={setChosen}
            objectiveIds={data.cells.map((c) => c.objective_id)}
          />
          <Chart chosen={chosen} traced={traced} onTrace={onTrace} onClear={onClear} />
        </section>

        <section aria-labelledby="status-title">
          <h2 id="status-title">{labels.statusTitle}</h2>
          <p className="key">{labels.statusKey}</p>
          <StatusTable />
        </section>

        <section className="prose" aria-labelledby="results-title">
          <His as="h2" id="results-title" text={his.resultsTitle} />
          <His as="p" text={his.resultsSentence} />
        </section>

        <section aria-labelledby="runs-title">
          <h2 id="runs-title">{labels.runsTitle}</h2>
          <p className="key">{labels.runsKey}</p>
          <RunsTable chosen={chosen} tracedRunId={traced?.runId ?? null} />
        </section>

        <section aria-labelledby="provenance-title">
          <h2 id="provenance-title">{labels.provenanceTitle}</h2>
          <Provenance />
        </section>
      </main>
      <Footer />
      <Tooltip tip={tip} />
    </>
  );
}
