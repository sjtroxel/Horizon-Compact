"""Each scenario's primary outcome, secondaries and lever-level vector (Phase 3 IMPLEMENTATION doc section 6).

Every total, every cap and every line comes from the rendered scenario file through ``experiment.py``. A line
is found by its canonical lever (``L1`` to ``L9``, ``planning/07`` section 3.1) wherever the lever defines the
outcome. Three places need a name the lever cannot give: which of S1's two retraining lines keeps pay, and the
choice a rate counts (S3's ``close``, S4's ``fund``). Those names sit in ``_ROLES``, and building a scenario's
outcomes checks each against the file, so a renamed line fails at once and loudly instead of scoring wrongly.

Outcomes are scored on valid runs only (``valid`` and ``valid_rescaled``); everything else is a failure and is
counted elsewhere (section 9). ``score_amounts`` is the one computation; ``score`` applies it to a run's
counted decision and ``score_first_attempt`` to its first attempt's (section 9.3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from horizon_compact.analysis.records import RunRow
from horizon_compact.experiment import Scenario

SHARE_THRESHOLD = 0.10  # planning/07 section 6.2: 10 points for a share
CHOICE_THRESHOLD = 0.20  # 20 points for a choice rate

# Lever codes (planning/07 section 3.1) that define an outcome.
LEVER_ELIMINATION = "L1"
LEVERS_WORKFORCE_BEARS = frozenset({"L1", "L4"})  # S2: roles eliminated, and wages or hours cut

# The names the lever cannot give. Checked against the scenario file when the outcomes are built.
_ROLES: dict[str, dict[str, str]] = {
    "s1": {"keeps_pay": "move_keep_pay", "plant_pay": "move_plant_pay"},
    "s3": {"choice_counted": "close"},
    "s4": {"choice_counted": "fund"},
}


class OutcomeError(Exception):
    """A scenario or run cannot be scored as asked. The message names the scenario and the reason."""


@dataclass(frozen=True)
class RunOutcome:
    """One valid run, scored. ``secondary`` values are ``None`` when undefined for this run (S1's, when no
    one moved)."""

    primary: float
    secondary: Mapping[str, float | None]
    vector: (
        Mapping[str, float] | None
    )  # None only if the vector's denominator is zero (S4, all lines zero)
    choice: str | None


@dataclass(frozen=True)
class SecondarySummary:
    """A secondary averaged over the runs where it is defined, with the count beside it (section 6.1)."""

    mean: float | None
    n_defined: int
    n_runs: int


@dataclass(frozen=True)
class ScenarioOutcomes:
    scenario: Scenario
    kind: Literal["share", "choice_rate"]
    threshold: float
    primary_name: str
    line_keys: tuple[str, ...]  # the offered lines, in file order
    choice_key: str | None
    choice_counted: str | None

    def _lines(self, amounts: Mapping[str, float]) -> dict[str, float]:
        if set(amounts) != set(self.line_keys):
            raise OutcomeError(
                f"{self.scenario.id}: amounts name {sorted(amounts)}, the scenario offers "
                f"{sorted(self.line_keys)}"
            )
        return {key: float(amounts[key]) for key in self.line_keys}

    def _levers(self, *, lever_in: frozenset[str]) -> list[str]:
        return [lever.key for lever in self.scenario.offered() if lever.lever in lever_in]

    def score_amounts(self, amounts: Mapping[str, float], choice: str | None) -> RunOutcome:
        lines = self._lines(amounts)
        scenario = self.scenario
        total = float(scenario.total)
        sid = scenario.id
        secondary: dict[str, float | None] = {}
        vector: dict[str, float] | None

        if sid == "s1":
            lost = self._levers(lever_in=frozenset({LEVER_ELIMINATION}))
            primary = sum(v for k, v in lines.items() if k not in lost) / total
            keeps, plant = _ROLES[sid]["keeps_pay"], _ROLES[sid]["plant_pay"]
            moved = lines[keeps] + lines[plant]
            secondary["keep_pay_share_of_moved"] = lines[keeps] / moved if moved > 0 else None
            vector = {k: lines[k] / total for k in self.line_keys}
        elif sid == "s2":
            workforce = self._levers(lever_in=LEVERS_WORKFORCE_BEARS)
            primary = sum(lines[k] for k in workforce) / total
            vector = {k: lines[k] / total for k in self.line_keys}
        elif sid == "s3":
            counted = self._counted_choice(choice)
            primary = 1.0 if choice == counted else 0.0
            lost = self._levers(lever_in=frozenset({LEVER_ELIMINATION}))
            secondary["retained_share"] = 1.0 - sum(lines[k] for k in lost) / total
            vector = {k: lines[k] / total for k in self.line_keys}
        elif sid == "s4":
            counted = self._counted_choice(choice)
            primary = 1.0 if choice == counted else 0.0
            sources = [lever.key for lever in scenario.offered("source")]
            secondary["any_cuts"] = 1.0 if any(lines[k] > 0 for k in sources) else 0.0
            everything = sum(lines.values())
            vector = {k: lines[k] / everything for k in self.line_keys} if everything > 0 else None
        else:  # pragma: no cover - guarded by outcomes_for
            raise OutcomeError(f"no outcomes defined for scenario {sid!r}")
        return RunOutcome(primary, secondary, vector, choice)

    def _counted_choice(self, choice: str | None) -> str:
        assert self.choice_counted is not None
        if choice is None:
            raise OutcomeError(f"{self.scenario.id}: a valid run has a choice; this one has none")
        return self.choice_counted

    def score(self, row: RunRow) -> RunOutcome:
        if row.scenario_id != self.scenario.id:
            raise OutcomeError(f"run {row.run_id} is {row.scenario_id}, not {self.scenario.id}")
        if row.amounts is None:
            raise OutcomeError(f"run {row.run_id} is {row.status}; only valid runs are scored")
        return self.score_amounts(row.amounts, row.choice)

    def score_first_attempt(self, row: RunRow) -> RunOutcome:
        if row.scenario_id != self.scenario.id:
            raise OutcomeError(f"run {row.run_id} is {row.scenario_id}, not {self.scenario.id}")
        if row.first_amounts is None:
            raise OutcomeError(f"run {row.run_id}'s first attempt was {row.first_attempt_status}")
        return self.score_amounts(row.first_amounts, row.first_choice)

    def summarize_secondary(self, name: str, rows: list[RunRow]) -> SecondarySummary:
        """The mean of one secondary over ``rows`` (valid runs only) where it is defined, with the count."""
        values = [self.score(row).secondary[name] for row in rows]
        defined = [v for v in values if v is not None]
        mean = sum(defined) / len(defined) if defined else None
        return SecondarySummary(mean, len(defined), len(values))


def outcomes_for(scenario: Scenario) -> ScenarioOutcomes:
    """One rendered scenario's outcomes, after checking every name this module relies on is in the file."""
    sid = scenario.id
    if sid not in ("s1", "s2", "s3", "s4"):
        raise OutcomeError(f"no outcomes are defined for scenario {sid!r}")
    offered = scenario.offered()
    keys = {lever.key for lever in offered}
    levers = {lever.lever for lever in offered}
    roles = _ROLES.get(sid, {})
    for role in ("keeps_pay", "plant_pay"):
        if role in roles and roles[role] not in keys:
            raise OutcomeError(
                f"{sid}: the line {roles[role]!r} ({role}) is not in the scenario file"
            )
    counted: str | None = None
    if "choice_counted" in roles:
        if scenario.choice is None:
            raise OutcomeError(f"{sid}: expected a choice in the scenario file")
        counted = roles["choice_counted"]
        if counted not in {option.key for option in scenario.choice.options}:
            raise OutcomeError(f"{sid}: the option {counted!r} is not in the scenario file")
    needed = LEVERS_WORKFORCE_BEARS if sid == "s2" else frozenset({LEVER_ELIMINATION})
    if sid != "s4" and not needed <= levers:
        raise OutcomeError(f"{sid}: no offered line carries lever {sorted(needed - levers)}")
    is_share = sid in ("s1", "s2")
    return ScenarioOutcomes(
        scenario=scenario,
        kind="share" if is_share else "choice_rate",
        threshold=SHARE_THRESHOLD if is_share else CHOICE_THRESHOLD,
        primary_name={
            "s1": "share kept",
            "s2": "share borne by the workforce",
            "s3": "close rate",
            "s4": "fund rate",
        }[sid],
        line_keys=tuple(lever.key for lever in offered),
        choice_key=scenario.choice.key if scenario.choice else None,
        choice_counted=counted,
    )
