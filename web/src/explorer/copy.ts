/**
 * Every word the explorer shows lives here or in his.json, except data values and the name "Horizon Compact".
 *
 * BOTH OBJECTS ARE UNAPPROVED. `explorerHis` is a set of marked placeholders (`[his: ...]`) naming what he writes;
 * `explorerLabels` is Claude-drafted and unapproved until the Phase 6 IMPLEMENTATION doc section 14, step 8, where he
 * approves it word for word. The gate that fails on an unwritten explorer word is Phase 6.5's go-live, not this
 * file's tests: the placeholder page's test `his words are written` (src/copy.test.ts) is not widened to these.
 *
 * His words live in his.json (not in this file) because the build's write-paths script, which is plain Node, reads
 * the same titles and descriptions for each path's HTML file.
 *
 * This file may import from ../copy; nothing the placeholder entry (src/main.tsx) imports may import this file.
 */
import type { Pages } from "./page-meta.mjs";
import hisJson from "./his.json";

export { PLACEHOLDER_MARK, isPlaceholder } from "../copy";

export interface ExplorerHis {
  landingQuestion: string;
  scopeSentence: string;
  pages: Pages;
}

export const explorerHis: ExplorerHis = hisJson;

export const explorerLabels = {
  skipToContent: "Skip to the content",
  navLabel: "Sections",
  navStory: "The story",
  navScenario: (id: string) => `Scenario ${id}`,
  navCases: "Real cases",
  navStudies: "Studies",
  navMemos: "Memos",
  modelSwitch: "Model",
  seeDetails: "See the details",
  scenario: "Scenario",
  primaryOutcome: "Primary outcome",
  exploratory: "exploratory",
  loading: "Loading the data",
  loadFailed: "The data did not load. Reload the page to try again.",
  notFoundTitle: "Page not found",
  notFoundText: "Nothing is at this address.",
  backToStory: "Back to the story",
};
