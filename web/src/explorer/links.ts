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
