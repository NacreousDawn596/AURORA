from aurora.benchmark.schema import TestExecution, TestOutcome
from aurora.benchmark.strategies import Strategy, order_tests


def _test(
    name: str,
    duration: float,
    *,
    outcome: TestOutcome = TestOutcome.PASSED,
    age: int | None = None,
    previous: TestOutcome | None = None,
    coverage: float = 0,
    relevance: float = 0,
) -> TestExecution:
    return TestExecution(
        name,
        duration,
        outcome,
        previous_outcome=previous,
        last_failure_age_builds=age,
        coverage_score=coverage,
        change_relevance=relevance,
    )


def test_input_order_preserves_given_order() -> None:
    tests = [_test("b", 1), _test("a", 1)]
    assert [item.test_id for item in order_tests(tests, Strategy.INPUT_ORDER)] == ["b", "a"]


def test_random_order_is_reproducible_for_seed() -> None:
    tests = [_test(str(index), 1) for index in range(20)]
    first = order_tests(tests, Strategy.RANDOM, seed=91)
    second = order_tests(tests, Strategy.RANDOM, seed=91)
    assert [item.test_id for item in first] == [item.test_id for item in second]


def test_fastest_first_uses_test_id_for_ties() -> None:
    tests = [_test("z", 1), _test("a", 1), _test("middle", 0.5)]
    assert [item.test_id for item in order_tests(tests, "fastest_first")] == ["middle", "a", "z"]


def test_recent_failure_first_uses_prior_failure_age() -> None:
    tests = [
        _test("never", 1),
        _test("older", 1, age=4),
        _test("recent", 1, age=1),
        _test("immediate", 1, previous=TestOutcome.FAILED),
    ]
    assert [item.test_id for item in order_tests(tests, "recent_failure_first")] == [
        "immediate",
        "recent",
        "older",
        "never",
    ]


def test_coverage_and_change_impact_rank_descending() -> None:
    tests = [
        _test("a", 1, coverage=0.2, relevance=0.9),
        _test("b", 1, coverage=0.9, relevance=0.1),
    ]
    assert order_tests(tests, "coverage_first")[0].test_id == "b"
    assert order_tests(tests, "change_impact_first")[0].test_id == "a"


def test_current_outcome_is_not_a_ranking_feature() -> None:
    tests = [
        _test("a", 2, outcome=TestOutcome.FAILED),
        _test("b", 1, outcome=TestOutcome.PASSED),
    ]
    assert [item.test_id for item in order_tests(tests, "fastest_first")] == ["b", "a"]
