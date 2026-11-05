# Normalized Benchmark Data Format

The initial internal schema is implemented with immutable Python dataclasses in `aurora.benchmark.schema`.

## BuildRecord

One observation per project, pull request, build and CI stage:

| Field | Type | Meaning |
|---|---|---|
| project | string | Dataset project slug |
| pr_name | string | Pull request identifier |
| build_id | string | CI build identifier |
| stage_id | string | CI stage identifier |
| timestamp | aware datetime | Build timestamp normalized to UTC |
| test_suite_duration_seconds | optional float | Upstream total when supplied |

The composite record identifier is `project/pr_name/build_id/stage_id`.

## TestExecution

| Field | Type | Meaning |
|---|---|---|
| test_id | string | Stable test-class or test identifier |
| duration_seconds | finite non-negative float | Observed test duration |
| outcome | enum | passed, failed, skipped, unknown |
| previous_outcome | optional enum | Prior observed outcome |
| last_failure_age_builds | optional integer | Number of observed timestamp buckets since last failure |
| coverage_score | float in [0,1] | Optional external coverage feature |
| change_relevance | float in [0,1] | Optional external change-impact feature |
| detected_faults | set of strings | Independently established fault IDs; empty for LRTS import |

The schema intentionally keeps observed outcome separate from causal fault attribution.

## ExperimentManifest

A JSON manifest records schema version, dataset name, metadata path and SHA-256, test-results root, strategy, budget, seed, code revision and UTC creation time.

The metadata checksum does not checksum every referenced per-stage ZIP. Preserve the source archive checksum or an immutable dataset release identifier separately when archiving a complete experiment.
