from datetime import UTC, datetime

import pytest

from aurora.benchmark.schema import BuildRecord, BuildRun, TestExecution, TestOutcome
from aurora.benchmark.splits import TemporalSplitError, chronological_split


def _run(project: str, day: int, build_id: str | None = None) -> BuildRun:
    return BuildRun(
        BuildRecord(
            project, "PR-1", build_id or str(day), "0",
            datetime(2024, 1, day, tzinfo=UTC),
        ),
        (TestExecution(f"test-{day}", 1, TestOutcome.PASSED),),
    )


def test_chronological_split_is_per_project_and_ordered() -> None:
    runs = [_run("a", day) for day in range(1, 11)]
    runs += [_run("b", day) for day in range(1, 7)]
    splits = chronological_split(runs)
    assert set(splits) == {"a", "b"}
    for split in splits.values():
        assert max(x.build.timestamp for x in split.train) < min(
            x.build.timestamp for x in split.validation
        )
        assert max(x.build.timestamp for x in split.validation) < min(
            x.build.timestamp for x in split.test
        )


def test_equal_timestamps_are_never_split_across_partitions() -> None:
    runs = [_run("a", day, f"{day}-1") for day in range(1, 7)]
    runs += [_run("a", day, f"{day}-2") for day in range(1, 7)]
    split = chronological_split(runs)["a"]
    partitions = (split.train, split.validation, split.test)
    for timestamp in {item.build.timestamp for item in runs}:
        counts = [sum(item.build.timestamp == timestamp for item in part) for part in partitions]
        assert sum(value > 0 for value in counts) == 1


def test_empty_dataset_is_rejected() -> None:
    with pytest.raises(TemporalSplitError, match="empty"):
        chronological_split([])


def test_project_with_fewer_than_three_distinct_timestamps_is_rejected() -> None:
    with pytest.raises(TemporalSplitError, match="three distinct"):
        chronological_split([_run("a", 1), _run("a", 2)])


@pytest.mark.parametrize(
    "fractions",
    [
        (0, 0.5, 0.5),
        (0.5, 0, 0.5),
        (0.5, 0.5, 0),
        (0.5, 0.3, 0.3),
    ],
)
def test_invalid_split_fractions_are_rejected(fractions: tuple[float, float, float]) -> None:
    with pytest.raises(ValueError):
        chronological_split(
            [_run("a", day) for day in range(1, 7)],
            train_fraction=fractions[0],
            validation_fraction=fractions[1],
            test_fraction=fractions[2],
        )


def test_split_keeps_all_rows() -> None:
    runs = [_run("a", day) for day in range(1, 8)]
    split = chronological_split(runs)["a"]
    assert len(split.train) + len(split.validation) + len(split.test) == len(runs)
