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
- Normalized immutable build and test-execution records.
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
- Static Python import/dependency graph with reverse dependency traversal.
- Conservative candidate-test report through the analyze-repo command.
- Per-test dynamic coverage graph from coverage.py JSON contexts through the map-coverage command.

Static imports and dynamic line coverage are complementary evidence, not proof of semantic dependence or fault detection. Coverage contexts must be configured per test, and the report's Git revision is operator-attested rather than embedded in coverage.py JSON.

### Engineering foundation

- Python package and command-line tools.
- Granular tests for ingestion, history, splitting, ordering, replay, metrics, manifests, diff parsing, Git comparison, AST extraction, dependency resolution, coverage mapping and CLI behavior.
- GitHub Actions CI on every push and pull request.
- OCI container build and smoke validation.

## Quick start

Requires Python 3.11 or newer.

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[dev]"
    pytest
    ruff check .
    ruff format --check .
    mypy

Run the scheduler demo:

    python -m aurora

Inspect benchmark commands:

    aurora-benchmark --help

Analyze a local repository revision range:

    aurora-benchmark analyze-repo \
      --repo-path /path/to/project \
      --base main \
      --head HEAD \
      --output aurora-impact.json

Build a per-test coverage graph for a clean checkout:

    coverage json --show-contexts -o /tmp/coverage.json
    aurora-benchmark map-coverage \
      --repo-path /path/to/project \
      --revision HEAD \
      --coverage-json /tmp/coverage.json \
      --changed-path src/package/service.py \
      --output coverage-graph.json

The repository analyzer does not execute repository code or run tests. The coverage
adapter reads an existing coverage.py report; it does not run tests or fabricate
per-test attribution from aggregate coverage.

## LRTS dataset

AURORA does not vendor the external dataset. Follow docs/DATASETS.md to obtain the processed LRTS artifact and run its inspection/replay adapter.

## Documentation

- Project definition: PROJECT.md
- Feature register: FEATURES.md
- Development stages: STAGES.md
- Changelog: CHANGELOG.md
- Research plan: docs/RESEARCH.md
- Architecture: docs/ARCHITECTURE.md
- Repository intelligence: docs/REPOSITORY_INTELLIGENCE.md
- Coverage evidence: docs/COVERAGE_EVIDENCE.md
- Experiment protocol: docs/EXPERIMENTS.md
- Benchmark strategies and metrics: docs/BENCHMARKS.md
- Dataset acquisition: docs/DATASETS.md
- Normalized data format: docs/DATA_FORMAT.md
- Contribution guide: CONTRIBUTING.md
- Security policy: SECURITY.md

Licensed under Apache-2.0. See LICENSE.
