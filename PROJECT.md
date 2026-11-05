# AURORA — Project Definition

## Summary

AURORA (Adaptive, Uncertainty-aware Release Orchestration and Regression Analysis) is a research-first framework for intelligent software delivery. It combines repository analysis, probabilistic machine learning, graph reasoning, sequential decision-making and bounded LLM-agent orchestration.

## Problem

Conventional CI pipelines often execute fixed suites or apply static selection rules. As repositories and tests grow, this can increase feedback latency and compute cost. Static rankings can also ignore the distinction between a regression, a flaky test, a pre-existing failure and infrastructure malfunction.

AURORA investigates how a pipeline can use project-specific evidence and a proposed change to decide which tests to execute next, then revise that decision as evidence arrives.

## Research objective

Determine whether **evidence-calibrated, interaction-aware adaptive test orchestration** can improve regression detection under constrained execution budgets while maintaining reliable failure attribution and safe release decisions.

## Intended outcomes

1. Reproducible benchmark and experiment harness.
2. Project-aware model of source, dependency, test and execution relationships.
3. Calibrated multi-outcome failure model.
4. Sequential scheduler accounting for marginal diagnostic value, runtime, resources and test interactions.
5. Containerized execution and evidence collection platform.
6. Bounded agentic workflow for build, test, diagnosis and delivery coordination.
7. Public research artifact and, subject to results, a scientific paper.

## Scope

### In scope

- Git change analysis and repository metadata.
- Static and dynamic dependency/coverage evidence.
- Test discovery and framework adapters.
- Historical CI execution ingestion.
- Regression, flaky, infrastructure and unrelated-failure attribution.
- Test prioritization and sequential scheduling.
- Test-order and shared-resource interaction modeling.
- Reproducible containerized execution.
- Build, artifact, security and deployment orchestration.
- Audit trails and experiment reproducibility.

### Out of scope for the first prototype

- Replacing established CI services.
- Building a foundation model.
- Unrestricted autonomous production deployment.
- Treating LLM-generated diagnoses as ground truth.
- Skipping tests solely because a model assigns low risk.

## Design principles

- **Evidence before confidence:** predictions must be calibrated and traceable.
- **Conservative uncertainty:** insufficient evidence means more testing or an inconclusive result.
- **Separation of concerns:** LLMs coordinate; statistical models predict; deterministic policy code authorizes.
- **Reproducibility:** every result is tied to revision, image digest, configuration and execution record.
- **Safety by default:** untrusted code runs in isolated workers with limited permissions.
- **Incremental complexity:** start with interpretable baselines and add complexity only when experiments justify it.
- **Honest evaluation:** negative results and limitations are reported.

## Autonomy model

- **L0 — Deterministic:** fixed pipeline and static test policy.
- **L1 — Predictive:** ML-assisted test ranking and scheduling, no LLM tool control.
- **L2 — Agent-assisted:** agents coordinate through validated tools and deterministic policies.
- **L3 — Policy-bounded:** agents orchestrate approved staging, monitoring and recovery operations within explicit constraints.

Production deployment remains approval-gated during research. No autonomy level overrides mandatory tests, security controls or repository policy.

## Success criteria

Report regression recall at fixed compute budgets, APFDc, time to first confirmed regression, probability calibration, failure attribution, order-induced failures, compute overhead, false release blocks, escaped regressions, human interventions and agentic errors. Thresholds must be preregistered; no target is presented as an achieved result.

## Current status

The repository is at the research-foundation stage. The first implementation is a small Python package and transparent greedy scheduling baseline. It establishes development conventions before dataset ingestion and model training.
