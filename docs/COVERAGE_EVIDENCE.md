# Dynamic Coverage Evidence

## Purpose

The Stage 2 static import graph identifies plausible test files. This adapter adds a
separate runtime evidence layer: per-test execution contexts mapped to source files
and executed line numbers. It does not replace static impact analysis; the two signals
answer different questions.

## Produce a per-test coverage report

AURORA consumes coverage.py JSON with per-line contexts. Configure coverage.py to
record a dynamic context for each test function (for example, by setting
dynamic_context = test_function in the run configuration), run the tests, then export:

    coverage json --show-contexts -o /tmp/coverage.json

The report must have meta.show_contexts = true and each file must include
executed_lines and a contexts mapping from line numbers to context labels.
Aggregate coverage reports without contexts are intentionally rejected: they cannot
tell AURORA which test executed a line.

Context strings are preserved exactly. AURORA does not parse pytest node IDs, infer
test framework semantics, or split context labels. Configure contexts so that each
label identifies the execution unit you want to schedule.

## Build the graph

Run the adapter against a clean checkout of the exact revision that produced the
coverage data:

    aurora-benchmark map-coverage \
      --repo-path /path/to/project \
      --revision HEAD \
      --coverage-json /tmp/coverage.json \
      --changed-path src/package/service.py \
      --output coverage-graph.json

The command resolves the supplied revision to a commit SHA and requires a clean
working tree at that exact SHA. Repeat --changed-path for additional changed files.
The output includes test-context-to-source-file edges, executed line numbers,
a SHA-256 checksum of the coverage report, and the test contexts that covered each
supplied changed path.

The revision is an operator-supplied attestation: coverage.py JSON does not itself
prove which Git revision was running when the report was collected. AURORA therefore
records this limitation in the output rather than claiming cryptographic provenance.

## Evidence semantics and limitations

- A graph edge means a named coverage context executed one or more lines in a source
  file during the recorded run.
- A missing edge does not prove that a test is irrelevant. Contexts may be configured
  incorrectly, subprocesses may not be measured, or instrumentation may be incomplete.
- A covered line does not prove assertion quality, fault detection, semantic dependence,
  or causal regression relevance.
- Coverage contexts are opaque identifiers, not guaranteed framework test IDs.
- This first adapter is language-agnostic at the file-path layer but relies on
  coverage.py's Python instrumentation; it does not add JavaScript/Vitest support.
- The graph is a point-in-time snapshot. Historical graph storage, test outcome joins,
  changed-line ranking, and temporal replay remain future work.

The adapter reads JSON as data and never imports or executes repository source code.
Input size and repository path boundaries are checked before graph construction.

## References

- https://coverage.readthedocs.io/en/latest/commands/cmd_json.html
- https://coverage.readthedocs.io/en/latest/config.html
