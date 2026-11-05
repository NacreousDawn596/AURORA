# Architecture

## Architectural planes

### Intelligence

- Change-impact analyzer.
- Temporal repository/test graph.
- Multi-outcome probabilistic predictor.
- Calibration and uncertainty estimator.
- Conditional marginal-value estimator.
- Sequential scheduler.
- Test-interaction model.

### Orchestration

- Repository analyst.
- Pipeline planner.
- Test investigator.
- Build/container worker coordinator.
- Security/release coordinators.
- Supervisor and policy gateway.

Agents request operations through typed interfaces. They do not receive unrestricted host access or direct control over release policy.

### Execution

- Build and dependency resolution.
- OCI image build and execution.
- Test framework adapters.
- Service dependencies and fixtures.
- Artifact collection and signing.
- Staging, monitoring and rollback adapters.

### Evidence and governance

- Append-only execution decision records.
- Versioned model and feature metadata.
- Experiment/run manifests.
- Policy decisions and approval records.
- Logs, metrics and traces.

## Current implementation modules

### Benchmark workbench

Implemented under src/aurora/benchmark/:

| Module | Responsibility |
|---|---|
| schema.py | Immutable normalized build and test-execution records |
| lrts.py | LRTS metadata/ZIP ingestion, outcome normalization and prior-only history features |
| splits.py | Per-project chronological partitions with equal timestamps held together |
| strategies.py | Deterministic ordering baselines |
| metrics.py | Budget-aware test-failure and known-fault metrics |
| replay.py | Offline fixed-budget strategy replay |
| manifest.py | Dataset metadata checksum and reproducibility manifest |
| cli.py | Dataset inspection, replay and repository analysis commands |
| change.py | Unified-diff file and line statistics |

### Repository intelligence

Implemented under src/aurora/repository/:

| Module | Responsibility |
|---|---|
| git.py | Resolve base/head refs to commit IDs and extract safe Git diffs |
| python_ast.py | Parse Python source without execution; extract imports, symbols and call expressions |
| dependency.py | Scan Python files, resolve static imports and build importer-to-dependency edges |
| analysis.py | Combine Git changes and Python dependency evidence into a candidate-test report |

The initial analyzer understands standard src/ layouts and ordinary Python packages. It skips common generated/vendor directories, ignores symlinked Python files, applies file-count and file-size limits, reports parse/scan issues, and handles cycles during reverse dependency traversal.

This is not a full semantic analyzer. It does not execute code, infer dynamic imports, derive runtime coverage, guarantee test reachability or prove that a candidate test detects a fault. It currently analyzes Python source only.

## Target data flow

1. Receive a commit or pull-request revision.
2. Resolve the exact source revision and build context.
3. Parse changes and collect prior-only repository evidence.
4. Construct or update graph snapshots.
5. Discover tests and mandatory constraints.
6. Predict outcome distributions and uncertainty.
7. Select the next test or safe batch.
8. Execute in an isolated worker and collect evidence.
9. Update beliefs and recompute marginal values.
10. Continue, request diagnostics, run mandatory tests or stop with an incomplete-evidence report.
11. Apply security and release policies.
12. Store immutable artifacts and auditable decision traces.

## Data contracts

A test candidate has a stable ID, framework, target revision, duration/resource estimates, impact/coverage evidence, interaction constraints and mandatory status.

A prediction has model/version IDs, class probabilities, calibration metadata, uncertainty, feature provenance and an abstention state.

An execution result has test ID, revision, image digest, environment/configuration digest, timestamps, exit status, structured outcome, log references and retry/order context.

A scheduling decision has candidate set, selected test/batch, score components, remaining budget, considered constraints, evidence references and scheduler version.

## Safety boundaries

- Untrusted code executes in isolated, unprivileged workers.
- Workers have resource quotas and network disabled by default.
- No untrusted job receives the host container socket.
- Secrets are not exposed to build/test jobs unless required.
- Use short-lived, least-privilege credentials.
- Images and artifacts use immutable digests.
- Mandatory tests and policy checks cannot be bypassed by an agent.
- Production actions remain approval-gated during research.
- LLM diagnosis is a hypothesis until supported by evidence.

## Implementation status

The repository contains the Stage 1 experimental workbench and an initial Python static repository-intelligence layer. Predictive ML, dynamic coverage, multi-language analysis, adaptive sequential scheduling, agentic orchestration and production deployment remain planned.
