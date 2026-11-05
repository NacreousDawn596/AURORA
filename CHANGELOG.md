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
- Extensive unit tests for schema, ingestion, history, splits, strategies, metrics, replay, manifests, CLI and diff parsing.
- Dataset acquisition, normalized data-format and benchmark-metric documentation.

### Notes
- Test-failure recall on LRTS is an observed failing-test proxy, not causal regression-fault recall.
- Full LRTS replay still requires external dataset acquisition; the repository does not vendor the data.
- No adaptive ML predictor, agentic orchestration or production deployment is implemented.

## [0.1.0] - 2026-11-05

### Added
- Research foundation bootstrap.
