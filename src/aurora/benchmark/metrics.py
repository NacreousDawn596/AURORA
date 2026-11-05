"""Budget-aware metrics with explicit separation of test failures and known faults."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from aurora.benchmark.schema import TestExecution, TestOutcome


def _validate_budget(budget_seconds: float) -> None:
    if not math.isfinite(budget_seconds) or budget_seconds < 0:
        raise ValueError("budget_seconds must be finite and non-negative")


def _executed_prefix(
    ordered_tests: Sequence[TestExecution], budget_seconds: float
) -> tuple[TestExecution, ...]:
    _validate_budget(budget_seconds)
    executed: list[TestExecution] = []
    elapsed = 0.0
    for test in ordered_tests:
        if elapsed + test.duration_seconds > budget_seconds:
            break
        executed.append(test)
        elapsed += test.duration_seconds
    return tuple(executed)


def test_failure_recall_at_budget(
    ordered_tests: Sequence[TestExecution], budget_seconds: float
) -> float | None:
    """Fraction of observed failing tests executed within the budget.

    This is a historical test-failure proxy, not causal regression-fault recall.
    Return None when the full run contains no failed tests.
    """
    _validate_budget(budget_seconds)
    failed = {test.test_id for test in ordered_tests if test.outcome is TestOutcome.FAILED}
    if not failed:
        return None
    executed = _executed_prefix(ordered_tests, budget_seconds)
    detected = {test.test_id for test in executed if test.outcome is TestOutcome.FAILED}
    return len(detected & failed) / len(failed)


def fault_recall_at_budget(
    ordered_tests: Sequence[TestExecution],
    known_faults: Iterable[str],
    budget_seconds: float,
) -> float | None:
    """Distinct known-fault recall; requires externally established fault labels."""
    _validate_budget(budget_seconds)
    faults = {fault.strip() for fault in known_faults if fault.strip()}
    if not faults:
        return None
    executed = _executed_prefix(ordered_tests, budget_seconds)
    detected = set().union(*(test.detected_faults for test in executed)) if executed else set()
    return len(detected & faults) / len(faults)


def apfdc(
    ordered_tests: Sequence[TestExecution],
    known_faults: Iterable[str] | None = None,
) -> float | None:
    """Cost-aware fault-detection area using execution durations.

    The curve assumes a fault is detected uniformly during the duration of its
    detecting test (trapezoidal area). Returns None when no faults or no cost exist.
    """
    if known_faults is not None:
        faults = {fault.strip() for fault in known_faults if fault.strip()}
    elif ordered_tests:
        faults = set().union(*(test.detected_faults for test in ordered_tests))
    else:
        faults = set()
    total_cost = sum(test.duration_seconds for test in ordered_tests)
    if not faults or total_cost <= 0:
        return None

    detected: set[str] = set()
    area = 0.0
    for test in ordered_tests:
        newly_detected = (set(test.detected_faults) & faults) - detected
        area += test.duration_seconds * (
            len(detected) + len(newly_detected) / 2.0
        ) / len(faults)
        detected.update(newly_detected)
    return area / total_cost


def time_to_first_failure(ordered_tests: Sequence[TestExecution]) -> float | None:
    """Elapsed execution time through the first failing test, or None."""
    elapsed = 0.0
    for test in ordered_tests:
        elapsed += test.duration_seconds
        if test.outcome is TestOutcome.FAILED:
            return elapsed
    return None
