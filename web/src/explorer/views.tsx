import { AgainstThesis } from "./AgainstThesis";
import { explorerHis, explorerLabels } from "./copy";
import type { CasesIndex, DataApi, DataIndex } from "./data";
import { His, Title } from "./parts";
import type { Route } from "./route";
import { hrefOf } from "./route";
import { ScenarioView } from "./ScenarioView";

export interface ViewProps {
  route: Route;
  index: DataIndex;
  casesIndex: CasesIndex;
  model: string;
  data: DataApi;
}

/**
 * Each route's view. The scenario view and the section for results against the thesis are C4; the rest are still
 * C3's stubs, each holding its title and little else: the memo reader, the cases and the studies are C5, the story is
 * C6 (it shows the section under its stub until then).
 */
export function View({ route, index, casesIndex, model, data }: ViewProps) {
  switch (route.kind) {
    case "story":
      return (
        <>
          <Title route={route} />
          <His text={explorerHis.landingQuestion} />
          <His text={explorerHis.scopeSentence} />
          <AgainstThesis index={index} />
        </>
      );
    case "scenario":
      // Keyed by scenario, so the goal toggles start over on a new scenario and carry across a model switch.
      return <ScenarioView key={route.id} id={route.id} index={index} model={model} data={data} />;
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
