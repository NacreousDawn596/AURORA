import math

import pytest

from aurora.benchmark.metrics import (
    apfdc,
    fault_recall_at_budget,
    observed_failure_recall_at_budget,
    time_to_first_failure,
)
from aurora.benchmark.schema import TestExecution, TestOutcome


def _test(
    name: str,
    duration: float,
    outcome: TestOutcome = TestOutcome.PASSED,
    faults: frozenset[str] = frozenset(),
) -> TestExecution:
    return TestExecution(name, duration, outcome, detected_faults=faults)


def test_observed_failure_recall_counts_tests_executed_within_budget() -> None:
    tests = [
        _test("pass", 2),
        _test("failed-a", 1, TestOutcome.FAILED),
        _test("failed-b", 2, TestOutcome.FAILED),
    ]
    assert observed_failure_recall_at_budget(tests, 3) == 0.5
    assert observed_failure_recall_at_budget(tests, 5) == 1.0


def test_observed_failure_recall_is_undefined_without_failures() -> None:
    assert observed_failure_recall_at_budget([_test("ok", 1)], 1) is None


def test_failure_recall_rejects_invalid_budget_even_when_undefined() -> None:
    for invalid in (-0.1, math.nan, math.inf):
        with pytest.raises(ValueError, match="finite"):
            observed_failure_recall_at_budget([], invalid)


def test_fault_recall_requires_known_fault_labels() -> None:
    tests = [
        _test("a", 1, faults=frozenset({"f1"})),
        _test("b", 2, faults=frozenset({"f2"})),
    ]
    assert fault_recall_at_budget(tests, {"f1", "f2"}, 1) == 0.5
    assert fault_recall_at_budget(tests, set(), 1) is None
    with pytest.raises(ValueError, match="finite"):
        fault_recall_at_budget(tests, set(), math.nan)


def test_apfdc_uses_duration_and_distinct_fault_ids() -> None:
    tests = [
        _test("a", 1, faults=frozenset({"f1"})),
        _test("b", 1, faults=frozenset({"f1", "f2"})),
    ]
    assert apfdc(tests) == pytest.approx(0.5)


def test_apfdc_accepts_external_fault_universe_and_undefined_cases() -> None:
    tests = [_test("a", 1, faults=frozenset({"f1"}))]
    assert apfdc(tests, {"f1", "f2"}) == pytest.approx(0.25)
    assert apfdc(tests, set()) is None
    assert apfdc([_test("zero", 0, faults=frozenset({"f1"}))]) is None


def test_time_to_first_failure_includes_failing_test_duration() -> None:
    tests = [
        _test("a", 2),
        _test("b", 3, TestOutcome.FAILED),
        _test("c", 4, TestOutcome.FAILED),
    ]
    assert time_to_first_failure(tests) == 5
    assert time_to_first_failure([_test("pass", 1)]) is None
