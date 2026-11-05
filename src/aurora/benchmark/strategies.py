"""Deterministic, training-free test ordering baselines."""

from __future__ import annotations

import random
from collections.abc import Sequence
from enum import StrEnum
from math import inf

from aurora.benchmark.schema import TestExecution, TestOutcome


class Strategy(StrEnum):
    """Supported test-ordering policies."""

    INPUT_ORDER = "input_order"
    RANDOM = "random"
    FASTEST_FIRST = "fastest_first"
    RECENT_FAILURE_FIRST = "recent_failure_first"
    COVERAGE_FIRST = "coverage_first"
    CHANGE_IMPACT_FIRST = "change_impact_first"


def order_tests(
    tests: Sequence[TestExecution],
    strategy: Strategy | str,
    *,
    seed: int = 0,
) -> tuple[TestExecution, ...]:
    """Return a stable ordering. Current-run outcomes are never ranking features."""
    selected_strategy = Strategy(strategy)
    ordered = list(tests)
    if selected_strategy is Strategy.INPUT_ORDER:
        return tuple(ordered)
    if selected_strategy is Strategy.RANDOM:
        random.Random(seed).shuffle(ordered)
        return tuple(ordered)
    if selected_strategy is Strategy.FASTEST_FIRST:
        ordered.sort(key=lambda item: (item.duration_seconds, item.test_id))
    elif selected_strategy is Strategy.RECENT_FAILURE_FIRST:

        def failure_key(item: TestExecution) -> tuple[int, int | float, float, str]:
            age = item.last_failure_age_builds
            if age is None and item.previous_outcome is TestOutcome.FAILED:
                age = 0
            if age is None:
                return (1, inf, item.duration_seconds, item.test_id)
            return (0, age, item.duration_seconds, item.test_id)

        ordered.sort(key=failure_key)
    elif selected_strategy is Strategy.COVERAGE_FIRST:
        ordered.sort(key=lambda item: (-item.coverage_score, item.duration_seconds, item.test_id))
    elif selected_strategy is Strategy.CHANGE_IMPACT_FIRST:
        ordered.sort(key=lambda item: (-item.change_relevance, item.duration_seconds, item.test_id))
    return tuple(ordered)
