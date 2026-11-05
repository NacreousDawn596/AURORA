"""Small, dependency-free domain models for the initial scheduler baseline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TestCandidate:
    """A test and the evidence available to the baseline scheduler.

    Risk inputs in v0.1 are illustrative. They are not calibrated predictions.
    """

    test_id: str
    regression_value: float
    information_gain: float
    duration_seconds: float
    resource_cost: float = 0.0
    interference_risk: float = 0.0
    mandatory: bool = False

    def __post_init__(self) -> None:
        if not self.test_id.strip():
            raise ValueError("test_id must not be empty")
        for name in ("regression_value", "information_gain", "resource_cost", "interference_risk"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if not 0 <= self.interference_risk <= 1:
            raise ValueError("interference_risk must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class SchedulerWeights:
    """Weights for a transparent greedy baseline; tune on validation data only."""

    information_gain: float = 0.0
    resource_cost: float = 0.0
    interference_penalty: float = 0.0
    epsilon: float = 1e-9

    def __post_init__(self) -> None:
        if self.information_gain < 0 or self.resource_cost < 0:
            raise ValueError("cost and information weights must be non-negative")
        if self.interference_penalty < 0:
            raise ValueError("interference_penalty must be non-negative")
        if self.epsilon <= 0:
            raise ValueError("epsilon must be positive")
