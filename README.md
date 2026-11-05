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

Historical LRTS failing-test recall is an observed test-failure proxy, not causal regression-fault recall.

### Repository intelligence (Python-first)

- Safe local Git revision resolution and unified-diff extraction.
- Non-executing Python AST extraction for imports, symbols and call expressions.
- Static Python import/dependency graph, including relative imports.
- Reverse dependency traversal to propose impacted Python test candidates.
- JSON report through `aurora-benchmark analyze-repo`.

This is conservative static analysis, not runtime coverage, a complete call graph or proof that a candidate test will detect a fault. It currently analyzes Python source only.

### Engineering foundation

- Python package and command-line tools.
- Granular tests for ingestion, history, splitting, ordering, replay, metrics, manifests, diff parsing, Git comparison, AST extraction, dependency resolution and CLI behavior.
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

Inspect benchmark commands:

```bash
aurora-benchmark --help
```

Analyze a local repository revision range:

```bash
aurora-benchmark analyze-repo \
  --repo-path /path/to/project \
  --base main \
  --head HEAD \
  --output aurora-impact.json
```

The report includes changed files, additions/deletions, parsed Python module count, dependency edge count, impacted Python paths, candidate test paths and static-analysis limitations. The repository must be checked out at the requested `--head` with a clean worktree; ignored untracked Python files are rejected too. The analyzer does not execute repository code or run tests.

## LRTS dataset

AURORA does not vendor the external dataset. Follow [docs/DATASETS.md](docs/DATASETS.md) to obtain the processed LRTS artifact and run its inspection/replay adapter.

## Documentation

- [Project definition](PROJECT.md)
- [Feature register](FEATURES.md)
- [Development stages](STAGES.md)
- [Changelog](CHANGELOG.md)
- [Research plan](docs/RESEARCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Repository intelligence](docs/REPOSITORY_INTELLIGENCE.md)
- [Experiment protocol](docs/EXPERIMENTS.md)
- [Benchmark strategies and metrics](docs/BENCHMARKS.md)
- [Dataset acquisition](docs/DATASETS.md)
- [Normalized data format](docs/DATA_FORMAT.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Licensed under Apache-2.0. See [LICENSE](LICENSE).
