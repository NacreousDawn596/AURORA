# Benchmark Strategies and Metrics

## Implemented ordering baselines

All current baseline strategies are deterministic except seeded random ordering. They rank the available TestExecution records; they do not train a model.

| Strategy | Ordering rule | Evidence consumed |
|---|---|---|
| input_order | Preserve source order | None |
| random | Shuffle using explicit seed | Seed |
| fastest_first | Shortest duration first | Runtime |
| recent_failure_first | Smallest age since last observed failure first | Prior history only |
| coverage_first | Highest coverage score first | Supplied coverage feature |
| change_impact_first | Highest change-relevance score first | Supplied change feature |

The recent-failure baseline uses the derived prior-failure age when available. When only the source artifact's previous outcome is available, a previous failure is treated as the most recent observation. Current-run outcomes are never ranking features.

Coverage and change-impact scores default to zero in the LRTS adapter because those signals are not columns in the normalized test-class CSV. They are available for future adapters or explicitly joined feature tables.

These baselines are not implementations of DANTE or other published methods. Published comparisons require a faithful reproduction or the original implementation under compatible data and licenses.

## Replay semantics

Replay uses the complete observed run as its oracle record, orders tests using only ranking features, then simulates a prefix of that order under a wall-clock budget. A test is counted as executed only if its full recorded duration fits. Replay stops when the next test cannot fit.

This is an offline ranking evaluation. It is not a substitute for live execution, particularly for tests sensitive to order, shared state or resource contention.

## Metrics

### Test-failure recall at budget

Fraction of test classes observed to fail in the complete historical run that are reached within the budget.

This is a **test-failure proxy**. It does not establish that a failure was caused by the evaluated change.

### Distinct fault recall at budget

Fraction of externally supplied known fault IDs detected by selected tests. This metric is undefined when no known fault universe is supplied.

### APFDc

The implementation computes normalized trapezoidal area under the cumulative distinct-fault-detection curve, with test duration as the cost axis. It assumes detection occurs uniformly during the duration of its detecting test. Only use it when fault IDs have independent ground truth.

### Time to first failure

Elapsed recorded test duration through the first failing test in the selected order. It is not time to first confirmed regression.

## Comparability rules

- Use identical candidate test sets, labels, budgets and execution-cost definitions across strategies.
- Fix and record random seeds.
- Do not use current outcomes as ranking features.
- Never construct historical features from future builds.
- Report the full-suite baseline and scheduler overhead.
- Report per-project results, not only pooled averages.
- Do not compare a class-level metric with a method-level metric as though they were equivalent.
