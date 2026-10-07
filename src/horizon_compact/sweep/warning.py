"""The spend warning shown before an OpenRouter key is asked for (Phase 2.5 IMPLEMENTATION doc section 17
step 10, his request of 2026-10-07).

OpenRouter is the one route that spends his own money, so a run on it says what it is expected to cost and
asks first. Nothing here calls a model or reads a key: it is arithmetic on the plan and on what the store
already holds, and the text it makes is printed by the command line.
"""

from __future__ import annotations

from dataclasses import dataclass

from horizon_compact.experiment import Experiment
from horizon_compact.sweep.classify import MAX_MODEL_ATTEMPTS
from horizon_compact.sweep.plan import SweepPlan, worst_case_per_attempt_usd
from horizon_compact.sweep.prompt import build_tool, render_prompt
from horizon_compact.sweep.runner import finished_run_ids, sweep_prefix
from horizon_compact.sweep.spend import estimate_input_tokens
from horizon_compact.sweep.store import Store

# Output tokens assumed for the likely figure. A tool call's arguments are short; the worst case uses the
# whole allowance instead.
ASSUMED_OUTPUT_TOKENS = 1000
# Measured on the probes, 2026-10-07: 20 calls, $0.0062, on the OpenRouter development model.
MEASURED_USD_PER_CALL = 0.0003


@dataclass(frozen=True)
class SpendEstimate:
    what: str  # what a call is here: "runs not yet finished", "probe repeats not yet recorded"
    calls: int
    likely_usd: float
    worst_usd: float
    worst_basis: str


def likely_call_usd(input_tokens: int, input_price: float, output_price: float) -> float:
    return (input_tokens * input_price + ASSUMED_OUTPUT_TOKENS * output_price) / 1_000_000


def sweep_estimate(experiment: Experiment, plan: SweepPlan, store: Store) -> SpendEstimate:
    prefix = sweep_prefix(plan.experiment, plan.sweep_id)
    done = finished_run_ids(store, prefix)
    pending = [run for run in plan.runs if run.run_id not in done]
    prices = experiment.model(plan.model_key).prices
    objectives = {o.id: o for o in experiment.objectives}
    tools = {sid: build_tool(experiment.get_scenario(sid)) for sid in plan.scenarios}
    likely = 0.0
    for run in pending:
        prompt = render_prompt(
            experiment,
            experiment.get_scenario(run.scenario_id),
            objectives[run.objective_id],
            run.wording_id,
            run.menu_order_seed,
        )
        tokens = estimate_input_tokens(prompt.system, prompt.user, tools[run.scenario_id])
        likely += likely_call_usd(tokens, prices.input, prices.output)
    worst = len(pending) * MAX_MODEL_ATTEMPTS * worst_case_per_attempt_usd(experiment, plan)
    return SpendEstimate(
        what="runs not yet finished",
        calls=len(pending),
        likely_usd=likely,
        worst_usd=worst,
        worst_basis=f"{MAX_MODEL_ATTEMPTS} attempts per run, each at the full output allowance",
    )


def format_warning(model_key: str, estimate: SpendEstimate, cap_usd: float) -> str:
    """The text printed before the key prompt. It states the assumptions, not only the totals."""
    return "\n".join(
        [
            f"This run spends your own OpenRouter credit ({model_key}).",
            f"  calls planned:  {estimate.calls} ({estimate.what})",
            f"  likely cost:    ${estimate.likely_usd:.4f}  (one call each, the estimated input tokens "
            f"plus {ASSUMED_OUTPUT_TOKENS:,} output tokens)",
            f"  worst case:     ${estimate.worst_usd:.4f}  ({estimate.worst_basis})",
            f"  cap:            ${cap_usd:.2f}",
            f"  measured so far: about ${MEASURED_USD_PER_CALL} a call (the probes, 2026-10-07: "
            "20 calls, $0.0062)",
        ]
    )
