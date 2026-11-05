"""Normalized, dependency-free benchmark records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from math import isfinite
from typing import ClassVar


class TestOutcome(StrEnum):
    """Normalized outcome; excluded from pytest's test-class discovery."""

    __test__: ClassVar[bool] = False

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TestExecution:
    """One observed test execution in a CI stage."""

    __test__: ClassVar[bool] = False

    test_id: str
    duration_seconds: float
    outcome: TestOutcome
    previous_outcome: TestOutcome | None = None
    last_failure_age_builds: int | None = None
    coverage_score: float = 0.0
    change_relevance: float = 0.0
    detected_faults: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.test_id.strip():
            raise ValueError("test_id must not be empty")
        if not isfinite(self.duration_seconds) or self.duration_seconds < 0:
            raise ValueError("duration_seconds must be finite and non-negative")
        if not isfinite(self.coverage_score) or not 0.0 <= self.coverage_score <= 1.0:
            raise ValueError("coverage_score must be finite and between 0 and 1")
        if not isfinite(self.change_relevance) or not 0.0 <= self.change_relevance <= 1.0:
            raise ValueError("change_relevance must be finite and between 0 and 1")
        if self.last_failure_age_builds is not None and (
            isinstance(self.last_failure_age_builds, bool) or self.last_failure_age_builds < 0
        ):
            raise ValueError("last_failure_age_builds must be a non-negative integer")
        try:
            object.__setattr__(self, "outcome", TestOutcome(self.outcome))
            if self.previous_outcome is not None:
                object.__setattr__(self, "previous_outcome", TestOutcome(self.previous_outcome))
        except ValueError as exc:
            raise ValueError(f"unsupported test outcome: {exc}") from exc
        cleaned_faults = frozenset(item.strip() for item in self.detected_faults if item.strip())
        object.__setattr__(self, "detected_faults", cleaned_faults)


@dataclass(frozen=True, slots=True)
class BuildRecord:
    """Identity and timestamp for one project/PR/build/stage observation."""

    project: str
    pr_name: str
    build_id: str
    stage_id: str
    timestamp: datetime
    test_suite_duration_seconds: float | None = None

    def __post_init__(self) -> None:
        for name in ("project", "pr_name", "build_id", "stage_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        if self.test_suite_duration_seconds is not None:
            value = self.test_suite_duration_seconds
            if not isfinite(value) or value < 0:
                raise ValueError("test_suite_duration_seconds must be finite and non-negative")

    @property
    def record_id(self) -> str:
        return f"{self.project}/{self.pr_name}/{self.build_id}/{self.stage_id}"


@dataclass(frozen=True, slots=True)
class BuildRun:
    """A stage-level build record together with its observed test executions."""

    build: BuildRecord
    tests: tuple[TestExecution, ...]

    def __post_init__(self) -> None:
        ids = [item.test_id for item in self.tests]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate test identifiers in build run {self.build.record_id}")

    @property
    def test_count(self) -> int:
        return len(self.tests)

    @property
    def failed_test_count(self) -> int:
        return sum(item.outcome is TestOutcome.FAILED for item in self.tests)

    @property
    def observed_duration_seconds(self) -> float:
        return sum(item.duration_seconds for item in self.tests)
