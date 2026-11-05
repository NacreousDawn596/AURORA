"""Transparent greedy scheduler baseline."""

from __future__ import annotations

from dataclasses import dataclass

from aurora.models import SchedulerWeights, TestCandidate


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    selected: tuple[TestCandidate, ...]
    deferred: tuple[TestCandidate, ...]
    total_duration_seconds: float
    total_resource_cost: float


def _score(candidate: TestCandidate, weights: SchedulerWeights) -> float:
    numerator = (
        candidate.regression_value
        + weights.information_gain * candidate.information_gain
        - weights.interference_penalty * candidate.interference_risk
    )
    denominator = candidate.duration_seconds + weights.resource_cost * candidate.resource_cost
    return numerator / max(denominator, weights.epsilon)


def prioritize(
    candidates: list[TestCandidate],
    *,
    budget_seconds: float,
    weights: SchedulerWeights | None = None,
) -> ScheduleResult:
    """Greedily prioritize under a duration budget.

    Mandatory tests are reserved first and never silently dropped. If their estimated
    duration exceeds the budget, the result reports that over-budget mandatory set.
    """
    if budget_seconds < 0:
        raise ValueError("budget_seconds must be non-negative")
    weights = weights or SchedulerWeights()
    ids = [candidate.test_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("test_id values must be unique")

    mandatory = sorted(
        (candidate for candidate in candidates if candidate.mandatory),
        key=lambda candidate: candidate.test_id,
    )
    optional = [candidate for candidate in candidates if not candidate.mandatory]
    selected = list(mandatory)
    remaining = budget_seconds - sum(item.duration_seconds for item in mandatory)

    if remaining >= 0:
        ordered = sorted(optional, key=lambda item: (-_score(item, weights), item.test_id))
        for candidate in ordered:
            if candidate.duration_seconds <= remaining:
                selected.append(candidate)
                remaining -= candidate.duration_seconds

    selected_ids = {candidate.test_id for candidate in selected}
    deferred = [candidate for candidate in candidates if candidate.test_id not in selected_ids]
    return ScheduleResult(
        selected=tuple(selected),
        deferred=tuple(deferred),
        total_duration_seconds=sum(item.duration_seconds for item in selected),
        total_resource_cost=sum(item.resource_cost for item in selected),
    )
