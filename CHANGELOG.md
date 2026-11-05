# Changelog

All notable changes are documented here. Dates use ISO 8601.

## [Unreleased]

### Added
- LRTS processed-dataset reader for metadata CSV and per-stage test-class ZIP archives.
- Immutable benchmark schemas and UTC timestamp normalization.
- Prior-only historical failure-age derivation with simultaneous timestamp buckets.
- Per-project chronological splitting with timestamp-tie protection.
- Deterministic input, random, fastest, recent-failure, coverage and change-impact baselines.
- Budget-aware offline replay and explicit test-failure/known-fault metrics.
- SHA-256 experiment manifests and an LRTS inspection/replay CLI.
- Unified-diff file and line-change statistics parser.
- Safe Git revision resolution and repository diff ingestion.
- Non-executing Python AST import/symbol/call extraction.
- Python import graph and transitive impacted-test candidate report.
- `aurora-benchmark analyze-repo` command and repository-intelligence documentation.
- Unit tests for schema, ingestion, history, splits, strategies, metrics, replay, manifests, CLI, Git, AST and dependency traversal.

### Notes
- Test-failure recall on LRTS is an observed failing-test proxy, not causal regression-fault recall.
- Full LRTS replay still requires external dataset acquisition; the repository does not vendor the data.
- Static impacted-test candidates are heuristic suggestions, not proof of coverage or fault detection.
- Repository intelligence currently analyzes Python source only; dynamic coverage, multi-language support and runtime call graphs remain planned.
- No adaptive ML predictor, agentic orchestration or production deployment is implemented.

## [0.1.0] - 2026-11-05

### Added
- Research foundation bootstrap.
