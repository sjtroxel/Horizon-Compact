import { lazy } from "react";
import { explorerLabels } from "./copy";
import type { CasesIndex, DataApi, DataIndex } from "./data";
import type { Route } from "./route";
import { hrefOf } from "./route";

// Each route's view is its own chunk, loaded on the first visit to it (Phase 6 IMPLEMENTATION doc section 17, C6 part
// A). The specifiers below are checked against view-modules.mjs by a test, which is what `check-dist` reads to know
// which chunk belongs to which path: add a view here and there together.
const Story = lazy(() => import("./Story").then((m) => ({ default: m.Story })));
const ScenarioView = lazy(() => import("./ScenarioView").then((m) => ({ default: m.ScenarioView })));
const CasesView = lazy(() => import("./Cases").then((m) => ({ default: m.CasesView })));
const CaseView = lazy(() => import("./Cases").then((m) => ({ default: m.CaseView })));
const StudiesView = lazy(() => import("./Studies").then((m) => ({ default: m.StudiesView })));
const MemosView = lazy(() => import("./MemoReader").then((m) => ({ default: m.MemosView })));

export interface ViewProps {
  route: Route;
  index: DataIndex;
  casesIndex: CasesIndex;
  model: string;
  /** The URL's query string (with its "?", or empty): the memo reader's choices are in it. */
  search: string;
  data: DataApi;
  /** Called once when the story has every beat's data (loaded or failed); the shell reveals a hash after it. */
  onStorySettled?: (() => void) | undefined;
}

/**
 * Each route's view. The scenario view and the section for results against the thesis are C4; the memo reader, the
 * real cases and the studies are C5. The story is C6's (nine beats, part B). A view is a lazy component: the shell holds the `Suspense` and the
 * error boundary around this one.
 */
export function View({ route, index, casesIndex, model, search, data, onStorySettled }: ViewProps) {
  switch (route.kind) {
    case "story":
      // The story ignores `model`: it shows both models by design.
      return <Story index={index} casesIndex={casesIndex} data={data} onSettled={onStorySettled} />;
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
