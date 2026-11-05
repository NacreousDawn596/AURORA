# Development Stages

This roadmap is evidence-driven. Later stages depend on measured results; dates are not commitments.

## Stage 0 — Research foundation (in progress)

- [x] Establish identity, scope and research questions.
- [x] Establish documentation, Python package, baseline tests and CI.
- [ ] Complete verified related-work matrix.
- [ ] Record dataset versions, licenses and access constraints.
- [ ] Preregister evaluation protocol and leakage controls.

**Exit:** reproducible baseline plan, data provenance and agreed protocol.

## Stage 1 — Experimental workbench (next)

- [ ] Dataset ingestion interfaces and normalized schema.
- [ ] LRTS historical CI adapter.
- [ ] Temporal train/validation/test splits.
- [ ] Random, fastest-first, recent-failure-first, coverage and change-impact baselines.
- [ ] Replay engine with fixed compute budgets.
- [ ] Metrics: recall@budget, APFDc, TTFR and cost.
- [ ] Reproducible run manifests and result artifacts.

**Exit:** baseline methods run under the same chronological evaluation harness.

## Stage 2 — Repository intelligence

- [ ] Git diff and commit metadata extraction.
- [ ] Test discovery and framework metadata.
- [ ] Static dependency graph and dynamic coverage mapping.
- [ ] Temporal graph snapshots and feature provenance.

**Exit:** features can be reconstructed for a historical revision without future information.

## Stage 3 — Probabilistic evidence model

- [ ] Define outcome labels and adjudication protocol.
- [ ] Establish regression/flaky/infrastructure/unrelated/pass data.
- [ ] Train interpretable baseline models.
- [ ] Add graph and change features.
- [ ] Evaluate calibration and per-class metrics.
- [ ] Evaluate cold-start and cross-project behavior.

**Exit:** predictive value and calibration measured against simple baselines.

## Stage 4 — Adaptive and interaction-aware scheduler

- [ ] Marginal diagnostic-value estimation.
- [ ] Sequential evidence updates.
- [ ] Runtime/resource budgets.
- [ ] Test interaction graph and concurrency constraints.
- [ ] Greedy, contextual-bandit and sequential policy comparisons.
- [ ] Order-dependence and ablation experiments.

**Exit:** gains, overhead and order-related effects measured on held-out data.

## Stage 5 — Containerized CI platform

- [ ] OCI build/execution workers and isolation.
- [ ] pytest, JUnit and Vitest adapters.
- [ ] Structured execution evidence and image digests.
- [ ] CI provider integration, security checks and SBOM.

**Exit:** reproducible build/test runs with complete evidence records.

## Stage 6 — Bounded agentic orchestration

- [ ] Typed tools and policy gateway.
- [ ] Repository analysis, pipeline planning and failure investigation.
- [ ] Human approvals and audit trail.
- [ ] L0/L1/L2/L3 autonomy experiments.
- [ ] Staging, monitoring and controlled rollback.

**Exit:** autonomy comparison reports tool errors, policy violations, interventions and recovery.

## Stage 7 — Evaluation and publication

- [ ] Historical CI replay, real defect benchmarks and controlled fault injection.
- [ ] Flakiness/order-dependence experiments.
- [ ] Temporal and leave-one-project-out evaluation.
- [ ] Ablations and statistical analysis.
- [ ] Reproducible artifact release and paper submission, contingent on results.

**Exit:** every paper claim is directly supported by reproducible results.

## Change control

Update this file and CHANGELOG.md when scope, acceptance criteria or stage status changes.
