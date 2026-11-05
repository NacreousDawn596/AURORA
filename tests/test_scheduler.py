from __future__ import annotations

import pytest

from aurora.models import SchedulerWeights, TestCandidate
from aurora.scheduler import prioritize


def test_prioritizes_value_per_unit_cost() -> None:
    candidates = [
        TestCandidate("slow", 0.8, 0, 10),
        TestCandidate("fast", 0.6, 0, 3),
    ]
    result = prioritize(candidates, budget_seconds=3)
    assert [item.test_id for item in result.selected] == ["fast"]
    assert [item.test_id for item in result.deferred] == ["slow"]


def test_mandatory_tests_are_never_dropped_even_over_budget() -> None:
    candidates = [
        TestCandidate("required", 0.1, 0, 8, mandatory=True),
        TestCandidate("optional", 0.9, 0, 1),
    ]
    result = prioritize(candidates, budget_seconds=2)
    assert [item.test_id for item in result.selected] == ["required"]
    assert [item.test_id for item in result.deferred] == ["optional"]
    assert result.total_duration_seconds == 8


def test_optional_tests_fit_remaining_budget() -> None:
    candidates = [
        TestCandidate("required", 0.1, 0, 4, mandatory=True),
        TestCandidate("a", 0.9, 0, 4),
        TestCandidate("b", 0.8, 0, 3),
    ]
    result = prioritize(candidates, budget_seconds=7)
    assert {item.test_id for item in result.selected} == {"required", "b"}
    assert result.total_duration_seconds == 7


def test_duplicate_ids_are_rejected() -> None:
    candidates = [TestCandidate("same", 0.5, 0, 1), TestCandidate("same", 0.4, 0, 1)]
    with pytest.raises(ValueError, match="unique"):
        prioritize(candidates, budget_seconds=10)


def test_invalid_budget_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        prioritize([], budget_seconds=-1)


def test_invalid_candidate_is_rejected() -> None:
    with pytest.raises(ValueError, match="test_id"):
        TestCandidate(" ", 0.5, 0, 1)
    with pytest.raises(ValueError, match="positive"):
        TestCandidate("bad-duration", 0.5, 0, 0)


def test_interference_penalty_changes_order() -> None:
    candidates = [
        TestCandidate("risky", 0.9, 0, 1, interference_risk=1.0),
        TestCandidate("safe", 0.7, 0, 1, interference_risk=0.0),
    ]
    result = prioritize(
        candidates,
        budget_seconds=1,
        weights=SchedulerWeights(interference_penalty=0.5),
    )
    assert result.selected[0].test_id == "safe"
