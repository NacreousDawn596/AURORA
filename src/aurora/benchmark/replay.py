"""Offline replay of test-ordering strategies under fixed wall-clock budgets."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from aurora.benchmark.metrics import (
    apfdc,
    observed_failure_recall_at_budget,
    time_to_first_failure,
)
from aurora.benchmark.schema import TestExecution, TestOutcome
from aurora.benchmark.strategies import Strategy, order_tests


@dataclass(frozen=True, slots=True)
class ReplayResult:
    strategy: str
    budget_seconds: float
    ordered_test_ids: tuple[str, ...]
    executed_test_ids: tuple[str, ...]
    deferred_test_ids: tuple[str, ...]
    consumed_seconds: float
    observed_failed_tests: int
    detected_failed_tests: int
    test_failure_recall: float | None
    time_to_first_failure_seconds: float | None
    apfdc_value: float | None


def replay(
    tests: Sequence[TestExecution],
    strategy: Strategy | str,
    *,
    budget_seconds: float,
    seed: int = 0,
    known_faults: set[str] | None = None,
) -> ReplayResult:
    """Rank and simulate tests under a budget using observed outcomes as replay labels."""
    if not math.isfinite(budget_seconds) or budget_seconds < 0:
        raise ValueError("budget_seconds must be finite and non-negative")
    ids = [test.test_id for test in tests]
    if len(ids) != len(set(ids)):
        raise ValueError("test identifiers must be unique for replay")
    ordered = order_tests(tests, strategy, seed=seed)
    executed: list[TestExecution] = []
    elapsed = 0.0
    for test in ordered:
        if elapsed + test.duration_seconds > budget_seconds:
            break
        executed.append(test)
        elapsed += test.duration_seconds

    executed_ids = {test.test_id for test in executed}
    failed_total = sum(test.outcome is TestOutcome.FAILED for test in tests)
    failed_detected = sum(test.outcome is TestOutcome.FAILED for test in executed)
    return ReplayResult(
        strategy=Strategy(strategy).value,
        budget_seconds=budget_seconds,
        ordered_test_ids=tuple(test.test_id for test in ordered),
        executed_test_ids=tuple(test.test_id for test in executed),
        deferred_test_ids=tuple(
            test.test_id for test in ordered if test.test_id not in executed_ids
        ),
        consumed_seconds=elapsed,
        observed_failed_tests=failed_total,
        detected_failed_tests=failed_detected,
        test_failure_recall=observed_failure_recall_at_budget(ordered, budget_seconds),
        time_to_first_failure_seconds=time_to_first_failure(executed),
        apfdc_value=apfdc(ordered, known_faults),
    )


def compare_strategies(
    tests: Sequence[TestExecution],
    strategies: Sequence[Strategy | str],
    *,
    budget_seconds: float,
    seed: int = 0,
) -> tuple[ReplayResult, ...]:
    """Evaluate multiple strategies with identical tests, budget and seed."""
    return tuple(
        replay(tests, strategy, budget_seconds=budget_seconds, seed=seed)
        for strategy in strategies
    )
