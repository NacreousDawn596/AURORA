import pytest

from aurora.benchmark.replay import compare_strategies, replay
from aurora.benchmark.schema import TestExecution, TestOutcome
from aurora.benchmark.strategies import Strategy


def _tests() -> list[TestExecution]:
    return [
        TestExecution("slow-fail", 5, TestOutcome.FAILED, detected_faults=frozenset({"f1"})),
        TestExecution("fast-pass", 1, TestOutcome.PASSED),
        TestExecution("medium-fail", 2, TestOutcome.FAILED, detected_faults=frozenset({"f2"})),
    ]


def test_replay_reports_order_execution_and_deferred_tests() -> None:
    result = replay(_tests(), Strategy.FASTEST_FIRST, budget_seconds=3)
    assert result.ordered_test_ids == ("fast-pass", "medium-fail", "slow-fail")
    assert result.executed_test_ids == ("fast-pass", "medium-fail")
    assert result.deferred_test_ids == ("slow-fail",)
    assert result.consumed_seconds == 3
    assert result.observed_failed_tests == 2
    assert result.detected_failed_tests == 1
    assert result.test_failure_recall == 0.5


def test_replay_can_report_apfdc_for_known_faults() -> None:
    result = replay(_tests(), "fastest_first", budget_seconds=20, known_faults={"f1", "f2"})
    assert result.apfdc_value is not None


def test_replay_is_deterministic_with_seed() -> None:
    first = replay(_tests(), "random", budget_seconds=3, seed=12)
    second = replay(_tests(), "random", budget_seconds=3, seed=12)
    assert first.ordered_test_ids == second.ordered_test_ids


def test_replay_rejects_negative_budget() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        replay(_tests(), "fastest_first", budget_seconds=-1)


def test_compare_strategies_uses_same_budget_and_seed() -> None:
    results = compare_strategies(
        _tests(),
        [Strategy.INPUT_ORDER, Strategy.FASTEST_FIRST],
        budget_seconds=4,
        seed=7,
    )
    assert len(results) == 2
    assert all(item.budget_seconds == 4 for item in results)
