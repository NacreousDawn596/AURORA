from datetime import UTC, datetime

import pytest

from aurora.benchmark.schema import BuildRecord, BuildRun, TestExecution, TestOutcome


def test_test_execution_normalizes_outcomes_and_fault_ids() -> None:
    item = TestExecution("suite.Test", 1.5, "failed", detected_faults=frozenset({" bug-1 ", ""}))
    assert item.outcome is TestOutcome.FAILED
    assert item.detected_faults == frozenset({"bug-1"})


@pytest.mark.parametrize("duration", [-1.0, float("nan"), float("inf"), float("-inf")])
def test_test_execution_rejects_invalid_duration(duration: float) -> None:
    with pytest.raises(ValueError, match="duration_seconds"):
        TestExecution("suite.Test", duration, TestOutcome.PASSED)


@pytest.mark.parametrize("score_name", ["coverage_score", "change_relevance"])
@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_test_execution_rejects_scores_outside_unit_interval(
    score_name: str, score: float
) -> None:
    values = {"coverage_score": 0.0, "change_relevance": 0.0}
    values[score_name] = score
    with pytest.raises(ValueError, match=score_name):
        TestExecution("suite.Test", 1.0, TestOutcome.PASSED, **values)


def test_test_execution_rejects_empty_id_and_negative_failure_age() -> None:
    with pytest.raises(ValueError, match="test_id"):
        TestExecution(" ", 1.0, TestOutcome.PASSED)
    with pytest.raises(ValueError, match="last_failure_age_builds"):
        TestExecution("suite.Test", 1.0, TestOutcome.PASSED, last_failure_age_builds=-1)


def test_build_record_requires_timezone_and_nonempty_identity() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        BuildRecord("p", "pr", "1", "0", datetime(2024, 1, 1))
    with pytest.raises(ValueError, match="project"):
        BuildRecord("", "pr", "1", "0", datetime.now(UTC))


def test_build_record_has_stable_composite_id() -> None:
    record = BuildRecord("kafka", "PR-1", "42", "2", datetime.now(UTC))
    assert record.record_id == "kafka/PR-1/42/2"


def test_build_run_rejects_duplicate_test_ids() -> None:
    record = BuildRecord("p", "pr", "1", "0", datetime.now(UTC))
    tests = (
        TestExecution("same", 1, TestOutcome.PASSED),
        TestExecution("same", 2, TestOutcome.FAILED),
    )
    with pytest.raises(ValueError, match="duplicate"):
        BuildRun(record, tests)


def test_build_run_summary_properties() -> None:
    record = BuildRecord("p", "pr", "1", "0", datetime.now(UTC))
    run = BuildRun(
        record,
        (
            TestExecution("a", 1.0, TestOutcome.FAILED),
            TestExecution("b", 2.0, TestOutcome.PASSED),
        ),
    )
    assert run.test_count == 2
    assert run.failed_test_count == 1
    assert run.observed_duration_seconds == 3.0
