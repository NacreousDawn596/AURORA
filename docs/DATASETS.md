# Dataset Acquisition and Provenance

## LRTS

AURORA's first historical CI adapter targets the public Long-Running Test Suites (LRTS) artifact maintained by the dataset authors:

- Upstream repository: https://github.com/lrtsuser/LRTS
- Paper: *Revisiting Test-Case Prioritization on Long-Running Test Suites*, ISSTA 2024.
- The upstream README describes metadata, per-PR/build information, source-change information and compressed per-stage test results.
- Consult the upstream README for the current processed-dataset download instructions and terms.

Do not commit the downloaded dataset to this repository. It is large, third-party research data; keep it outside the source tree and record the exact version, source URL, date obtained, license/terms and checksum in experiment manifests.

### Expected layout

The processed dataset is expected to contain:

```text
lrts-data/
├── metadata/
│   └── dataset.csv
└── processed_test_result/
    └── <project>/
        └── <pr_name>_build<build_id>/
            └── stage_<stage_id>/
                └── test_class.csv.zip
```

Each metadata row represents a project/PR/build/stage record. The AURORA adapter requires:

- `project`
- `pr_name`
- `build_id`
- `stage_id`
- `build_timestamp`

It optionally reads `test_suite_duration_s`.

The per-stage archive must contain one unambiguous test-class CSV. The processed LRTS artifact uses these core fields:

- `testclass`: test class identifier;
- `duration`: execution duration in seconds;
- `outcome`: observed outcome (the upstream artifact uses 0 for pass and 1 for fail);
- `last_outcome`: previous observed outcome when present.

AURORA also accepts common textual outcome aliases, but unknown labels are rejected rather than silently coerced.

### Running the adapter

Install the package and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Inspect the downloaded dataset:

```bash
aurora-benchmark inspect-lrts \
  --metadata /path/to/lrts-data/metadata/dataset.csv \
  --test-results-root /path/to/lrts-data/processed_test_result
```

Run a historical-ordering replay:

```bash
aurora-benchmark replay-lrts \
  --metadata /path/to/lrts-data/metadata/dataset.csv \
  --test-results-root /path/to/lrts-data/processed_test_result \
  --project kafka \
  --strategy recent_failure_first \
  --budget-seconds 3600 \
  --seed 42 \
  --output results/kafka-replay.json \
  --manifest results/kafka-replay.manifest.json
```

Use `--skip-missing` only when intentionally working with an incomplete collection. Skipped rows are reported in the output. Strict loading is the default.

### Granularity and causal-label limitations

The processed dataset adapter uses **test-class-within-build-stage** granularity. It does not claim method-level visibility where the processed artifact provides class-level results.

An observed failing test is not automatically a regression introduced by the current commit. Historical LRTS outcomes are suitable for test-failure prioritization and replay, but a causal regression-fault metric requires independently known fault identifiers, for example from a reproducible buggy/fixed revision or controlled fault injection.

The command therefore reports test-failure recall and calls it a test-failure proxy. It does not label that metric regression recall.

### Dataset-version discipline

The upstream repository README and the original ISSTA 2024 evaluation paper describe different dataset snapshots and counts. Record the exact downloaded artifact revision/version; do not combine summary statistics from different snapshots without an explicit reconciliation.

## Future datasets

Defects4J, BugsInPy and controlled mutation/fault-injection datasets are planned. Their adapters must preserve their native granularity, provenance, licenses and defect/fault semantics.
