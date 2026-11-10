import { isPlaceholder, explorerHis, explorerLabels } from "./copy";
import type { CasesIndex, DataIndex } from "./data";
import { pageMeta } from "./page-meta.mjs";
import type { PageRoute } from "./page-meta.mjs";
import type { Route } from "./route";
import { hrefOf } from "./route";

/** A sentence of his; while it is still a marked placeholder it shows in the secondary ink. */
function His({ text, className }: { text: string; className?: string }) {
  const classes = [className, isPlaceholder(text) ? "placeholder" : undefined].filter(Boolean).join(" ");
  return <p className={classes || undefined}>{text}</p>;
}

/** The view's title: his words for the kind of page, and the scenario's id or the case's label after it. */
function Title({ route }: { route: PageRoute }) {
  const title = pageMeta(route, explorerHis.pages).title;
  return (
    <h1
      tabIndex={-1}
      className={isPlaceholder(explorerHis.pages[route.kind].title) ? "placeholder" : undefined}
    >
      {title}
    </h1>
  );
}

export interface ViewProps {
  route: Route;
  index: DataIndex;
  casesIndex: CasesIndex;
  model: string;
}

/**
 * The stub of each route (C3). Each holds its title and little else: the views are C4 (the scenario view), C5 (the
 * memo reader, the cases, the studies) and C6 (the story). Nothing here draws a chart, a comparison or a sentence.
 */
export function View({ route, index, casesIndex, model }: ViewProps) {
  switch (route.kind) {
    case "story":
      return (
        <>
          <Title route={route} />
          <His text={explorerHis.landingQuestion} />
          <His text={explorerHis.scopeSentence} />
        </>
      );
    case "scenario": {
      const scenario = index.scenarios.find((s) => s.scenario_id === route.id);
      return (
        <>
          <Title route={route} />
          <div className="layout-2">
            <figure className="card">
              <dl className="stub">
                <dt>{explorerLabels.scenario}</dt>
                <dd className="mono">{route.id}</dd>
                <dt>{explorerLabels.primaryOutcome}</dt>
                <dd>{scenario?.primary_outcome}</dd>
              </dl>
              <figcaption>
                <span className="model-name">{model}</span>
                <His text={explorerHis.scopeSentence} />
              </figcaption>
            </figure>
          </div>
        </>
      );
    }
    case "cases":
      return (
        <>
          <Title route={route} />
          <His text={explorerHis.scopeSentence} />
          <ul className="stub-list">
            {casesIndex.cases.map((c) => (
              <li key={c.label}>
                <a className="mono" href={hrefOf({ kind: "case", label: c.label }, model)}>
                  {c.label}
                </a>
                {c.exploratory && <span className="tag">{explorerLabels.exploratory}</span>}
              </li>
            ))}
          </ul>
        </>
      );
    case "case": {
      const entry = casesIndex.cases.find((c) => c.label === route.label);
      return (
        <>
          <Title route={route} />
          <p>
            <span className="mono">{route.label}</span>
            {entry?.exploratory && <span className="tag">{explorerLabels.exploratory}</span>}
          </p>
        </>
      );
    }
    case "studies":
    case "memos":
      return (
        <>
          <Title route={route} />
          <His text={explorerHis.scopeSentence} />
        </>
      );
    case "not_found":
      return (
        <>
          <h1 tabIndex={-1}>{explorerLabels.notFoundTitle}</h1>
          <p>{explorerLabels.notFoundText}</p>
          <p>
            <a href={hrefOf({ kind: "story" }, model)}>{explorerLabels.backToStory}</a>
          </p>
        </>
      );
  }
}
