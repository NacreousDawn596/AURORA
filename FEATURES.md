# Feature Register

Legend: [x] implemented; [~] scaffolded/partial; [ ] planned; [!] requires research validation.

## Research core

- [~] Deterministic greedy test scheduler baseline.
- [ ] Historical CI ingestion and temporal feature extraction.
- [ ] Repository change analyzer.
- [ ] Static dependency and call graph extraction.
- [ ] Dynamic coverage ingestion.
- [ ] Test-to-code coverage graph.
- [ ] Test interaction graph.
- [ ] Multi-class outcome predictor: regression, flaky, infrastructure, unrelated failure, pass.
- [ ] Probability calibration and uncertainty estimation.
- [ ] Conditional marginal diagnostic-value estimator.
- [ ] Bayesian/sequential evidence updating.
- [ ] Contextual bandit and alternative sequential policies.
- [ ] Cold-start behavior and cross-project transfer.
- [!] Validate interaction-aware scheduling against real test-order effects.

## Repository intelligence

- [ ] Git commit and diff ingestion.
- [ ] AST parsing adapters.
- [ ] Dependency manifest adapters.
- [ ] Test discovery adapters.
- [ ] Coverage adapters.
- [ ] Temporal graph snapshots.
- [ ] Evidence provenance and replay.

## Execution and DevOps

- [~] Container build/test workflow in GitHub Actions.
- [ ] Build plan and dependency caching.
- [ ] OCI image metadata and digest tracking.
- [ ] Isolated test workers and resource quotas.
- [ ] pytest, JUnit and Vitest adapters.
- [ ] Structured test result schema.
- [ ] Logs, traces and artifact collection.
- [ ] SBOM and vulnerability scanning.
- [ ] Staging deployment adapter.
- [ ] Health checks and policy-controlled rollback.

## Agentic orchestration

- [ ] Repository analyst and pipeline planner agents.
- [ ] Test investigator and build/container agents.
- [ ] Security and release agents.
- [ ] Typed tool contracts and policy gateway.
- [ ] Agent decision and tool-call audit records.
- [ ] Human approval workflows.
- [!] Compare L0–L3 autonomy modes.

## Interface and operations

- [ ] FastAPI service.
- [ ] PostgreSQL persistence.
- [ ] Event queue and worker lifecycle.
- [ ] React dashboard.
- [ ] Metrics and OpenTelemetry integration.
- [ ] Model and experiment registry.

## Research reproducibility

- [ ] LRTS, Defects4J and BugsInPy adapters.
- [ ] Controlled fault-injection harness.
- [ ] Flakiness and order-dependence harness.
- [ ] Baseline implementations and replay.
- [ ] Temporal and leave-one-project-out evaluation.
- [ ] Ablation study and statistical report generation.
