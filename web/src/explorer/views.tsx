import { AgainstThesis } from "./AgainstThesis";
import { CaseView, CasesView } from "./Cases";
import { explorerHis, explorerLabels } from "./copy";
import type { CasesIndex, DataApi, DataIndex } from "./data";
import { His, Title } from "./parts";
import type { Route } from "./route";
import { hrefOf } from "./route";
import { MemosView } from "./MemoReader";
import { ScenarioView } from "./ScenarioView";
import { StudiesView } from "./Studies";

export interface ViewProps {
  route: Route;
  index: DataIndex;
  casesIndex: CasesIndex;
  model: string;
  /** The URL's query string (with its "?", or empty): the memo reader's choices are in it. */
  search: string;
  data: DataApi;
}

/**
 * Each route's view. The scenario view and the section for results against the thesis are C4; the memo reader, the
 * real cases and the studies are C5. The story is still C3's stub, C6's to build (it shows the section for results
 * against the thesis under its stub until then).
 */
export function View({ route, index, casesIndex, model, search, data }: ViewProps) {
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
      return <CasesView index={index} casesIndex={casesIndex} model={model} data={data} />;
    case "case":
      // Keyed by label, so a new case starts its load over.
      return (
        <CaseView key={route.label} label={route.label} index={index} casesIndex={casesIndex} data={data} />
      );
    case "studies":
      return <StudiesView index={index} data={data} />;
    case "memos":
      return <MemosView index={index} model={model} search={search} data={data} />;
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
