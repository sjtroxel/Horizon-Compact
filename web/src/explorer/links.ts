/** The repository, and the tag the experiment was pre-registered under (protocol 15.1). */
export const REPOSITORY = "https://github.com/sjtroxel/horizon-compact";
export const PREREG_TAG = "prereg-v1";

/** The repository path of the file the harness renders a scenario's prompt from (protocol 4.2). */
export function scenarioTextPath(scenarioId: string): string {
  return `experiment/company/scenarios/${scenarioId}.toml`;
}

/** The full scenario text, as the model saw it, on GitHub at the pre-registered tag. */
export function scenarioTextUrl(scenarioId: string): string {
  return `${REPOSITORY}/blob/${PREREG_TAG}/${scenarioTextPath(scenarioId)}`;
}

/** The protocol, at the pre-registered tag, with an anchor when one is asked for (GitHub's heading anchors). */
export function protocolUrl(anchor?: string): string {
  return `${REPOSITORY}/blob/${PREREG_TAG}/experiment/protocol/protocol-v1.md${anchor === undefined ? "" : `#${anchor}`}`;
}

/** Protocol section 9.5 (the thinking sub-study) and section 9.6 (the awareness probe). */
export const THINKING_ANCHOR = "95-thinking";
export const AWARENESS_ANCHOR = "96-the-awareness-probe";

/**
 * The two public selection logs for the real cases, on the main branch (they were committed after the tag). The
 * first is the pre-registered search's, the second the exploratory selection's.
 */
export const SELECTION_LOGS: ReadonlyArray<{ id: "preregistered" | "exploratory"; path: string }> = [
  { id: "preregistered", path: "docs/phases/evidence/phase-5/selection-public.json" },
  { id: "exploratory", path: "docs/phases/evidence/phase-5/exploratory-public.json" },
];

export function selectionLogUrl(path: string): string {
  return `${REPOSITORY}/blob/main/${path}`;
}

/** The ids of the studies page's two parts, so a link from another page can name one. */
export const STUDIES_THINKING_ID = "thinking-sub-study";
export const STUDIES_AWARENESS_ID = "awareness-probes";
