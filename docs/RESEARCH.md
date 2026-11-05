# Research Plan

## Working title

**Evidence-Calibrated and Interaction-Aware Adaptive Test Orchestration for Safe Autonomous CI/CD**

## Central question

Can a project-aware system sequentially select tests using calibrated regression evidence, conditional diagnostic value and test-interaction constraints, improving regression detection under fixed compute budgets without increasing order-induced failures or unsafe release decisions?

## Positioning

Test prioritization, historical failure prediction, change-impact analysis, graph-based selection, uncertainty calibration, information gain and agentic testing all have prior work. Their combination is not by itself claimed as novel. The investigation focuses on cause-aware outcome attribution, conditional marginal detection value with correlated coverage, sequential evidence updates, test interaction constraints and deterministic release-safety policies.

## Research questions

- **RQ1:** Can multi-source project evidence estimate regression-detection likelihood separately from flaky, infrastructure and unrelated failures?
- **RQ2:** Does conditional marginal diagnostic utility improve fault detection under fixed execution budgets?
- **RQ3:** Can test-interaction modeling reduce failures caused by reordering and parallel execution?
- **RQ4:** Does sequential evidence updating outperform static rankings?
- **RQ5:** How does calibrated uncertainty affect test reduction and release safety?
- **RQ6:** What benefits and risks arise from bounded agentic orchestration?

## Hypotheses

- **H1:** Change, graph, coverage and historical evidence improve prediction over history-only and change-only baselines.
- **H2:** Sequential scheduling improves cost-constrained fault detection over static ordering.
- **H3:** Multi-class attribution reduces false regression classifications compared with binary pass/fail models.
- **H4:** Interaction constraints reduce order-induced failures compared with unconstrained execution.
- **H5:** Explicit uncertainty and conservative fallback improve decisions on cold-start and out-of-distribution projects.
- **H6:** Agentic orchestration may reduce manual diagnosis effort but can introduce latency and tool-use errors; the net effect must be measured.

## Mathematical sketch

Let T be candidate tests and C potentially affected regression scenarios. For test t and scenario c, let q(t,c) estimate the probability that t detects c given the change and available evidence. Let w(c) be scenario severity. Under a simplifying conditional-independence approximation, expected undetected risk after tests S is:

`U(S) = sum_c w(c) * product_{t in S}(1 - q(t,c))`.

The marginal value of test t is `DeltaU(t | S) = U(S) - U(S union {t})`. This approximation must be stress-tested because tests can be correlated. Interaction models and learned conditional detection estimates may address some dependence.

A sequential policy chooses tests using marginal risk reduction, information gain, uncertainty, execution time, resource cost and interference risk, subject to budgets and mandatory-test constraints.

## Labeling and attribution

A failed test is not automatically a regression. Candidate classes: regression introduced by current change; flaky/nondeterministic failure; infrastructure/environment failure; pre-existing or unrelated deterministic failure; pass. Ground truth should use controlled parent/revision comparisons, reproducible reruns, environment health evidence, known defect triggers and independent adjudication. Ambiguous cases remain `unknown`.

## Evaluation tracks

1. Historical CI replay with prior-only evidence.
2. Real bugs with reproducible buggy/fixed revisions and triggering tests.
3. Controlled faults with known origins and verified detection.
4. Flakiness/order experiments under controlled seeds and isolated environments.
5. System experiments comparing deterministic and agentic autonomy levels.

## Baselines

Full suite, random, fastest-first, recently-failed-first, coverage-based, change-impact-based, published recent methods where reproducible, simple supervised classifiers and AURORA ablations. Methods must receive equivalent evidence and budgets.

## Metrics

- Distinct known-fault recall at 10%, 25%, 50% and 75% of full-suite cost.
- APFDc and time to first confirmed regression.
- Brier score, log loss, ECE and calibration curves.
- Per-class precision/recall, macro-F1 and confusion matrix.
- Order-induced/flaky failure rate.
- CPU-seconds, memory, wall time and scheduling overhead.
- False release blocks, escaped regressions, interventions and tool errors.

## Validity controls

Chronological and rolling-origin splits; leave-one-project-out generalization; cold-start evaluation; feature timestamps/provenance; no future graph, coverage or failure information; project-clustered confidence intervals; multiple-comparison correction; preregistered hypotheses and metrics; report negative results.

## Novelty gate

Perform a structured review across test prioritization, regression selection, flaky-test diagnosis, order-dependent testing, fault diagnosis, active learning and agentic DevOps. Maintain paper-by-paper comparisons. Existing components are treated as baselines or engineering choices, not claimed contributions.
