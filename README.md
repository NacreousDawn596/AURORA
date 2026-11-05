# AURORA

**Adaptive, Uncertainty-aware Release Orchestration and Regression Analysis**

AURORA is a research-first, agentic DevOps system. Its central research question is whether calibrated, project-specific evidence and feedback-driven scheduling can improve regression detection under constrained CI budgets without weakening release safety.

> **Status:** Research foundation / early prototype. The current implementation is intentionally small. No performance, prediction-quality, or safety claims are made yet.

## First steps

1. Read [PROJECT.md](PROJECT.md) for the problem statement and boundaries.
2. Read [FEATURES.md](FEATURES.md) for the capability map.
3. Follow [STAGES.md](STAGES.md) for the roadmap.
4. Review [docs/RESEARCH.md](docs/RESEARCH.md) for research questions and hypotheses.
5. Review [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the initial system design.
6. Use [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions.

## First prototype

The first batch includes project documentation, a Python package skeleton, a deterministic greedy scheduler baseline, unit tests, CI workflows and a container smoke test. This is not yet the adaptive ML system described in the research plan.

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
python -m aurora
```

## Current limitations

- Scheduler inputs are illustrative, not trained predictions.
- No LLM agent, graph database, CI provider integration, or production deployment integration is implemented.
- Container workflow validates image build and execution; it does not perform autonomous deployment.

## Documentation

- [Project definition](PROJECT.md)
- [Feature register](FEATURES.md)
- [Development stages](STAGES.md)
- [Changelog](CHANGELOG.md)
- [Research plan](docs/RESEARCH.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Experiment protocol](docs/EXPERIMENTS.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Licensed under Apache-2.0. See [LICENSE](LICENSE).
