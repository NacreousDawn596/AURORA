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
- aurora-benchmark analyze-repo command and repository-intelligence documentation.
- coverage.py JSON context ingestion and test-to-source-file graph.
- aurora-benchmark map-coverage command with changed-path lookup, source-path validation and report checksum.
- Coverage graph tests and dynamic-coverage documentation.

### Notes
- Test-failure recall on LRTS is an observed failing-test proxy, not causal regression-fault recall.
- Full LRTS replay still requires external dataset acquisition; the repository does not vendor the data.
- Static impacted-test candidates are heuristic suggestions, not proof of coverage or fault detection.
- Coverage contexts are opaque labels; they must be configured per test. coverage.py JSON does not cryptographically attest the Git revision.
- Repository intelligence currently analyzes Python source only; multi-language support, runtime call graphs, temporal snapshots and historical quality evaluation remain planned.
- No adaptive ML predictor, agentic orchestration or production deployment is implemented.

## [0.1.0] - 2026-11-05

### Added
- Research foundation bootstrap.
