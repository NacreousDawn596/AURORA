"""Command-line demonstration for the initial scheduler baseline."""

from aurora.models import SchedulerWeights, TestCandidate
from aurora.scheduler import prioritize


def main() -> int:
    candidates = [
        TestCandidate("test_auth_integration", 0.92, 0.30, 8.0, 1.0, 0.05),
        TestCandidate("test_session_expiry", 0.81, 0.55, 5.0, 0.5, 0.10),
        TestCandidate("test_permissions", 0.74, 0.40, 12.0, 1.0, 0.05),
        TestCandidate("test_frontend_snapshot", 0.18, 0.10, 20.0, 2.0, 0.00),
        TestCandidate("test_schema_contract", 0.63, 0.50, 7.0, 0.8, 0.05, mandatory=True),
    ]
    result = prioritize(
        candidates,
        budget_seconds=25.0,
        weights=SchedulerWeights(information_gain=0.25, interference_penalty=0.1),
    )
    print("AURORA v0.1 — illustrative greedy scheduling baseline")
    print("These scores are demo inputs, not trained predictions.")
    print(f"Estimated selected duration: {result.total_duration_seconds:.1f}s")
    print("Selected:")
    for candidate in result.selected:
        marker = " [mandatory]" if candidate.mandatory else ""
        print(f"  - {candidate.test_id}{marker}")
    print("Deferred:")
    for candidate in result.deferred:
        print(f"  - {candidate.test_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
