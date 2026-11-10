import { explorerLabels } from "./copy";
import type { ModelEntry } from "./data";

/** The name a model is called on the page, from the labels; the key itself when the labels do not know it. */
export function modelName(key: string): string {
  return explorerLabels.models.find((model) => model.key === key)?.name ?? key;
}

/**
 * The data's models in the order the labels give (Haiku 5.5 first, the default). A model the labels do not know
 * follows, in the data's order; a test ties the labels' keys to the data's, so that case fails a test and is not
 * left to show a bare key.
 */
export function orderedModels(entries: readonly ModelEntry[]): ModelEntry[] {
  const rank = (key: string) => {
    const at = explorerLabels.models.findIndex((model) => model.key === key);
    return at === -1 ? explorerLabels.models.length : at;
  };
  return [...entries].sort((a, b) => rank(a.model_key) - rank(b.model_key));
}
