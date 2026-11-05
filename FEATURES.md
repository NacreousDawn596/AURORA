# Feature Register

Legend: [x] implemented; [~] partial/scaffolded; [ ] planned; [!] requires research validation.

## Stage 1 — Experimental workbench

- [x] Normalized build/test execution schema.
- [x] LRTS metadata and per-stage ZIP adapter.
- [x] Strict and permissive ingestion modes with explicit skipped-row reports.
- [x] Timestamp normalization to UTC.
- [x] Prior-only failure-age history features.
- [x] Per-project chronological splits that keep timestamp ties together.
- [x] Input-order and seeded-random baselines.
- [x] Fastest-first and recent-failure-first baselines.
- [x] Coverage-first and change-impact-first baselines.
- [x] Fixed wall-clock budget replay.
- [x] Test-failure recall at budget (explicitly not causal regression recall).
- [x] Distinct known-fault recall and APFDc when external fault IDs exist.
- [x] Time-to-first-failure metric.
- [x] SHA-256 experiment manifests.
- [x] LRTS inspection/replay CLI.
- [~] Historical replay on the full upstream dataset (requires external dataset acquisition).
- [ ] Reproduce published DANTE baseline and other recent comparison methods.
- [ ] Controlled fault injection and independent regression labels.
- [ ] Rolling-origin and leave-one-project-out evaluation.

## Stage 2 — Repository intelligence

- [x] Unified-diff file/addition/deletion statistics parser.
- [x] Safe Git revision resolution and diff ingestion.
- [x] Python AST import, function/class/method and call-expression extraction (no execution).
- [x] Python import graph with absolute and relative import resolution.
- [x] Reverse dependency traversal and impacted Python path enumeration.
- [x] Conservative candidate-test report.
- [x] analyze-repo JSON CLI.
- [x] Per-test coverage.py JSON context ingestion.
- [x] Test-to-source-file graph with executed line numbers and report checksum.
- [x] Changed-file lookup against observed coverage contexts.
- [ ] Java/TypeScript and other language frontends.
- [ ] Runtime call graph extraction.
- [ ] Temporal graph snapshots and feature provenance.
- [ ] Framework-aware test discovery and execution adapters.
- [!] Validate static impact recall against real historical revisions and ground-truth test coverage.

## Stage 3 — Probabilistic evidence model

- [ ] Outcome-label adjudication protocol.
- [ ] Multi-class outcome predictor.
- [ ] Probability calibration and uncertainty estimation.
- [ ] Cold-start and cross-project transfer.
- [ ] Model ablations and calibration reports.

## Stage 4 — Adaptive and interaction-aware scheduler

- [ ] Conditional marginal diagnostic-value estimator.
- [ ] Sequential evidence updates.
- [ ] Contextual-bandit/sequential policy comparisons.
- [ ] Test-interaction graph and safe concurrency constraints.
- [ ] Order-dependence experiments.

## Stage 5 — Containerized CI platform

- [x] Container build/test workflow in GitHub Actions.
- [ ] Isolated workers and resource/network quotas.
- [ ] pytest, JUnit and Vitest execution adapters.
- [ ] Structured logs, traces and artifact collection.
- [ ] SBOM and vulnerability scanning.
- [ ] Staging deployment and policy-controlled rollback.

## Stage 6 — Bounded agentic orchestration

- [ ] Typed tool contracts and policy gateway.
- [ ] Repository analyst and pipeline planner agents.
- [ ] Test investigator and build/container agents.
- [ ] Security and release agents.
- [ ] Autonomy-level evaluation.

## Interface and operations

- [ ] FastAPI service.
- [ ] PostgreSQL persistence.
- [ ] Event queue and worker lifecycle.
- [ ] React dashboard.
- [ ] Metrics and OpenTelemetry integration.
- [ ] Model and experiment registry.
