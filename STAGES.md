# Development Stages

This roadmap is evidence-driven. Later stages depend on measured results; dates are not commitments.

## Stage 0 — Research foundation

**Status:** Complete as a repository foundation; related-work and preregistration work remain ongoing.

- [x] Establish identity, scope and research questions.
- [x] Establish documentation, Python package, baseline tests and CI.
- [x] Record architecture, experiment protocol and security principles.
- [ ] Complete verified related-work matrix.
- [ ] Finalize dataset provenance and preregistered protocol.

## Stage 1 — Experimental workbench

**Status:** Implementation substantially complete; external-data evaluation remains open.

- [x] Dataset ingestion interface and normalized schema.
- [x] LRTS metadata and test-class ZIP adapter.
- [x] UTC timestamp parsing and validation.
- [x] Prior-only history features.
- [x] Per-project chronological splits and timestamp-tie protection.
- [x] Basic ordering baselines.
- [x] Fixed-budget replay.
- [x] Test-failure recall, known-fault recall, APFDc and TTFF metrics.
- [x] Experiment manifest and data checksum.
- [x] LRTS inspection and replay CLI.
- [x] Unit tests for feature behavior and edge cases.
- [ ] Run against the downloaded full LRTS artifact and archive actual experiment outputs.
- [ ] Reproduce recent published baselines, including DANTE, under compatible conditions.

**Exit:** baseline methods run under the same chronological evaluation harness on the actual dataset, with a reproducible result bundle. The code is ready for that evaluation; the full-data exit criterion is not yet met because the external dataset is not stored in this repository.

## Stage 2 — Repository intelligence

**Status:** First primitive implemented.

- [x] Unified-diff file and line-change statistics parser.
- [ ] Git diff and commit metadata ingestion.
- [ ] Test discovery and framework metadata.
- [ ] Static dependency/call graph.
- [ ] Dynamic coverage mapping.
- [ ] Temporal graph snapshots and feature provenance.

**Exit:** features can be reconstructed for a historical revision without future information.

## Stage 3 — Probabilistic evidence model

- [ ] Define outcome labels and adjudication protocol.
- [ ] Establish regression/flaky/infrastructure/unrelated/pass datasets.
- [ ] Train interpretable baseline models.
- [ ] Add graph and change features.
- [ ] Evaluate calibration and per-class metrics.
- [ ] Evaluate cold-start and cross-project behavior.

**Exit:** predictive value and calibration are measured against simple baselines.

## Stage 4 — Adaptive and interaction-aware scheduler

- [ ] Conditional marginal diagnostic-value estimation.
- [ ] Sequential evidence updates.
- [ ] Runtime/resource budgets.
- [ ] Test interaction graph and concurrency constraints.
- [ ] Greedy, contextual-bandit and sequential policy comparisons.
- [ ] Order-dependence and ablation experiments.

**Exit:** gains, overhead and order-related effects are measured on held-out data.

## Stage 5 — Containerized CI platform

- [x] Container image build and smoke validation in CI.
- [ ] OCI build/execution workers and isolation.
- [ ] pytest, JUnit and Vitest adapters.
- [ ] Structured execution evidence and image digests.
- [ ] CI provider integration, security checks and SBOM.

## Stage 6 — Bounded agentic orchestration

- [ ] Typed tools and policy gateway.
- [ ] Repository analysis, pipeline planning and failure investigation.
- [ ] Human approvals and audit trail.
- [ ] L0/L1/L2/L3 autonomy experiments.
- [ ] Staging, monitoring and controlled rollback.

## Stage 7 — Evaluation and publication

- [ ] Historical CI replay, real defect benchmarks and controlled fault injection.
- [ ] Flakiness/order-dependence experiments.
- [ ] Temporal and leave-one-project-out evaluation.
- [ ] Ablations and statistical analysis.
- [ ] Reproducible artifact release and paper submission, contingent on results.

## Change control

Update this file and CHANGELOG.md when scope, acceptance criteria or stage status changes.
