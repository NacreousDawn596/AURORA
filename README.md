# AURORA

**Adaptive, Uncertainty-aware Release Orchestration and Regression Analysis**

AURORA is a research-first, agentic DevOps system. Its central research question is whether calibrated, project-specific evidence and feedback-driven scheduling can improve regression detection under constrained CI budgets without weakening release safety.

> **Status:** Research prototype. No performance, prediction-quality or safety claim is made until supported by reproducible experiments.

## Research focus

The proposed research contribution is evidence-calibrated, interaction-aware adaptive test orchestration:

- distinguish observed regression evidence from flaky, infrastructure and unrelated failures;
- estimate the conditional marginal value of tests;
- adapt test ordering as execution evidence arrives;
- account for test interactions and constrained execution resources;
- preserve deterministic release and security policies.

## Current implementation

### Experimental workbench

- LRTS processed-dataset adapter (test-class within build-stage granularity).
- Normalized immutable build and test execution records.
- UTC timestamp normalization and per-project chronological splits.
- Prior-only historical failure-age features.
- Deterministic baselines: input order, seeded random, fastest-first, recent-failure-first, coverage-first and change-impact-first.
- Budget-constrained offline replay.
- Test-failure recall, distinct known-fault recall, APFDc and time-to-first-failure metrics.
- Reproducibility manifests with metadata SHA-256.
- Unified-diff file/addition/deletion statistics.

The LRTS adapter does not invent causal regression labels. Historical failing-test recall is reported as a proxy, not regression-fault recall.

### Engineering foundation

- Python package and command-line tools.
- Unit tests for validation, ingestion, history, splitting, ordering, replay, metrics, manifests and diff parsing.
- GitHub Actions CI on every push and pull request.
- OCI container build and smoke validation.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
mypy
```

Run the scheduler demo:

```bash
python -m aurora
```

Run the benchmark CLI:

```bash
aurora-benchmark --help
```

## LRTS dataset

AURORA does not vendor the external dataset. Follow [docs/DATASETS.md](docs/DATASETS.md) to obtain the processed LRTS artifact and run its inspection/replay adapter.

## Documentation

- [Project definition](PROJECT.md)
- [Feature register](FEATURES.md)
- [Development stages](STAGES.md)
- [Changelog](CHANGELOG.md)
- [Research plan](docs/RESEARCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Experiment protocol](docs/EXPERIMENTS.md)
- [Benchmark strategies and metrics](docs/BENCHMARKS.md)
- [Dataset acquisition](docs/DATASETS.md)
- [Normalized data format](docs/DATA_FORMAT.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Licensed under Apache-2.0. See [LICENSE](LICENSE).
