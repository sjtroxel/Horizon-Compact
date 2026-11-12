import { useId } from "react";
import type { ModelEntry } from "./data";
import { explorerLabels } from "./copy";
import { modelName, orderedModels } from "./models";

/**
 * The page's one model switch (layout 2, Phase 6 IMPLEMENTATION doc section 24.2): one button per model, the current
 * one `aria-pressed`, pinned to the top on scroll, in a labelled region. It never offers "both": the two models are never pooled. The order
 * and the names come from `explorerLabels.models` (Haiku 5.5 first, the default), because the data carries only a
 * model's key; a test ties that list to the index's models. The choice is reported by key.
 */
export function ModelSwitch({
  models,
  current,
  onChoose,
}: {
  models: readonly ModelEntry[];
  current: string;
  onChoose: (modelKey: string) => void;
}) {
  const labelId = useId();
  return (
    // The bar is its own labelled region, so no content sits outside a landmark (axe's `region` rule), and it is on the
    // header's dark band, pinned to the top on scroll.
    <div className="switch-bar" role="region" aria-labelledby={labelId}>
      <div className="switch">
        <span className="switch-label" id={labelId}>
          {explorerLabels.modelSwitch}
        </span>
        {orderedModels(models).map((model) => (
          <button
            key={model.model_key}
            type="button"
            aria-pressed={model.model_key === current}
            onClick={() => onChoose(model.model_key)}
          >
            {modelName(model.model_key)}
          </button>
        ))}
      </div>
    </div>
  );
}

/** The space the bar takes, held before the data has arrived (so nothing moves when it does): the same box, empty. */
export function ModelSwitchSpace() {
  return <div className="switch-bar switch-space" aria-hidden="true" />;
}
