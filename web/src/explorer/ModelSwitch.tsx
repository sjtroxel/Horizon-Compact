import { useId } from "react";
import type { ModelEntry } from "./data";
import { explorerLabels } from "./copy";

/**
 * The page's one model switch (layout 2, Phase 6 IMPLEMENTATION doc section 24.2): one button per model in the
 * index's order, the current one `aria-pressed`, pinned to the top on scroll. It never offers "both": the two
 * models are never pooled. The name shown is the model's key from the data, because the index carries no other name.
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
    <div className="switch-bar">
      <div className="switch" role="group" aria-labelledby={labelId}>
        <span className="switch-label" id={labelId}>
          {explorerLabels.modelSwitch}
        </span>
        {models.map((model) => (
          <button
            key={model.model_key}
            type="button"
            aria-pressed={model.model_key === current}
            onClick={() => onChoose(model.model_key)}
          >
            {model.model_key}
          </button>
        ))}
      </div>
    </div>
  );
}
