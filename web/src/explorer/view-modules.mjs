// Which source module is each route kind's view: the one `views.tsx` loads with `React.lazy` for that kind of path.
// Plain ES module with a .d.mts beside it, like page-meta.mjs, so the build's check-dist script (plain Node) and the
// explorer's tests read the same map. A test reads views.tsx and fails if its `import("./...")` specifiers are not
// exactly these files, so the two cannot drift apart.
//
// `not_found` has no entry: it is drawn inline by the shell and has no chunk of its own. The `case` and `cases` kinds
// share one module on purpose (two views, one chunk).

/** Route kind to the view's source path, relative to the web/ folder (how Vite's manifest names a module). */
export const VIEW_MODULES = {
  story: "src/explorer/Story.tsx",
  scenario: "src/explorer/ScenarioView.tsx",
  cases: "src/explorer/Cases.tsx",
  case: "src/explorer/Cases.tsx",
  studies: "src/explorer/Studies.tsx",
  memos: "src/explorer/MemoReader.tsx",
};
