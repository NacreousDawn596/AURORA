"""Chronological project-wise benchmark splits."""

from __future__ import annotations

import math
from dataclasses import dataclass

from aurora.benchmark.schema import BuildRun


class TemporalSplitError(ValueError):
    """Raised when a project cannot be split without temporal leakage."""


@dataclass(frozen=True, slots=True)
class TemporalSplit:
    train: tuple[BuildRun, ...]
    validation: tuple[BuildRun, ...]
    test: tuple[BuildRun, ...]

    def __post_init__(self) -> None:
        if not self.train or not self.validation or not self.test:
            raise TemporalSplitError("train, validation and test partitions must all be non-empty")
        if max(item.build.timestamp for item in self.train) >= min(
            item.build.timestamp for item in self.validation
        ):
            raise TemporalSplitError("training data must be strictly earlier than validation data")
        if max(item.build.timestamp for item in self.validation) >= min(
            item.build.timestamp for item in self.test
        ):
            raise TemporalSplitError("validation data must be strictly earlier than test data")


def chronological_split(
    runs: tuple[BuildRun, ...] | list[BuildRun],
    *,
    train_fraction: float = 0.6,
    validation_fraction: float = 0.2,
    test_fraction: float = 0.2,
) -> dict[str, TemporalSplit]:
    """Split each project by timestamp, keeping equal-timestamp records together."""
    fractions = (train_fraction, validation_fraction, test_fraction)
    if any(not math.isfinite(value) or value <= 0 or value >= 1 for value in fractions):
        raise ValueError("each split fraction must be finite and between 0 and 1")
    if abs(sum(fractions) - 1.0) > 1e-9:
        raise ValueError("split fractions must sum to 1")

    grouped: dict[str, list[BuildRun]] = {}
    for run in runs:
        grouped.setdefault(run.build.project, []).append(run)
    if not grouped:
        raise TemporalSplitError("cannot split an empty dataset")

    results: dict[str, TemporalSplit] = {}
    for project, project_runs in grouped.items():
        project_runs.sort(key=lambda item: (item.build.timestamp, item.build.record_id))
        timestamps = sorted({item.build.timestamp for item in project_runs})
        if len(timestamps) < 3:
            raise TemporalSplitError(
                f"project {project!r} needs at least three distinct timestamps"
            )

        train_end = max(1, min(len(timestamps) - 2, int(len(timestamps) * train_fraction)))
        validation_end = max(
            train_end + 1,
            min(
                len(timestamps) - 1,
                int(len(timestamps) * (train_fraction + validation_fraction)),
            ),
        )
        train_times = set(timestamps[:train_end])
        validation_times = set(timestamps[train_end:validation_end])
        test_times = set(timestamps[validation_end:])

        train = tuple(item for item in project_runs if item.build.timestamp in train_times)
        validation = tuple(
            item for item in project_runs if item.build.timestamp in validation_times
        )
        test = tuple(item for item in project_runs if item.build.timestamp in test_times)
        results[project] = TemporalSplit(train=train, validation=validation, test=test)
    return results
