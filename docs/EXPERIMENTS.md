# Experimental Protocol

## Purpose

Define a fair and reproducible evaluation. Record final split boundaries, exclusions, metrics and statistical tests before inspecting final test-set outcomes.

## Experimental units

Distinguish project, commit/build, test class or method (preserving source dataset granularity), execution, known defect scenario and pipeline run. Correlated executions within one project are not independent projects.

## Data tracks

- **Historical CI:** versioned long-running CI data where licensing and availability permit. Preserve native granularity.
- **Real defects:** reproducible buggy/fixed revisions and triggering tests. Record benchmark version, project/language coverage and limitations.
- **Controlled faults:** mutation operators and verified fault injections. Record source diff, expected behavior and verified detecting tests. Report mutants separately from real bugs.
- **Flaky/order behavior:** repeated trials under controlled seeds, clean environments, orders and resource conditions. A single failure is not proof of flakiness.

## Leakage prevention

- Split chronologically within each project.
- Use only history preceding the evaluated revision.
- Fit transforms, calibration and thresholds on training/validation only.
- Evaluate on untouched future revisions.
- Run leave-one-project-out validation.
- Evaluate cold-start at zero, 10 and 50 prior builds where possible.
- Record graph snapshot time and feature provenance.

## Replay procedure

For each held-out revision: resolve source and parent; reconstruct prior evidence; identify candidates and mandatory tests; initialize budget; select next test; reveal only the selected result; update scheduler state; continue until budget/policy stop; compute fault detection, cost and reliability metrics.

Historical replay does not fully model order-dependent or resource-contention effects. Validate policies using live controlled execution.

## Baselines

Full suite, random, fastest-first, recently-failed-first, coverage, change-impact, reproducible recent publications and simple supervised models. All use equivalent candidate sets, evidence, budgets and environment assumptions.

## Metrics

Primary: distinct known-fault recall at 10/25/50/75% full-suite cost, APFDc and time to first confirmed regression.

Secondary: Brier, log loss, ECE, per-class precision/recall, macro-F1, confusion matrix, wall time, CPU, memory, scheduler overhead, order-induced failure rate, false release blocks, escaped regressions, interventions and tool errors.

## Ablations

Remove graph, history, semantic change, calibration, attribution, feedback, marginal overlap adjustment, information gain, uncertainty bonus, interaction constraints and LLM orchestration one at a time.

## Statistics

Use paired per-commit comparisons, aggregate by project, report effect sizes and confidence intervals, correct multiple comparisons and consider project-clustered bootstrap intervals. Choose inferential tests after pilot data and preregister them. Run power analysis from pilot variance.

## Reproducibility manifest

Record dataset/version/license/checksum; project/revision; split boundaries; code commit; model/calibration versions; seeds; environment and image digests; scheduler configuration and budgets; raw result references; metric implementation version.

## Reporting

Report negative results, per-project variation, missing data, exclusions, compute overhead and limitations. Model scores are not causal ground truth.
