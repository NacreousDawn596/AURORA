# Repository Intelligence (Python-first)

## Purpose

The repository-intelligence layer combines two deliberately separate evidence sources:

1. Static Python imports propose files and tests that may depend on a change.
2. Per-test runtime coverage contexts show which source lines were observed during an actual test execution.

Neither source is complete. Static imports can miss dynamic dependencies, while line coverage does not prove semantic dependence or fault detection.

## Static analysis CLI

    aurora-benchmark analyze-repo \
      --repo-path /path/to/project \
      --base origin/main \
      --head HEAD \
      --output results/impact.json

The command resolves both refs to commit object IDs, asks Git for a no-external-diff unified patch, parses changed paths, scans Python source and writes a JSON report.

Additional safety/scale controls:

- --timeout-seconds: timeout for each Git command (default 30 seconds).
- --max-files: maximum number of scanned Python files (default 10,000).
- --max-file-bytes: maximum size of an individual Python source file (default 1,000,000 bytes).
- --output -: write JSON to stdout.

The command does not require the external LRTS dataset.

## Dynamic coverage CLI

Configure coverage.py with per-test dynamic contexts, run your tests, and export contexts:

    coverage json --show-contexts -o /tmp/coverage.json

Then map the contexts to source lines at a clean checkout:

    aurora-benchmark map-coverage \
      --repo-path /path/to/project \
      --revision HEAD \
      --coverage-json /tmp/coverage.json \
      --changed-path src/package/service.py \
      --output results/coverage-graph.json

Repeat --changed-path for each changed file. The result reports all observed test-context-to-file edges, their executed line numbers, a SHA-256 checksum of the coverage JSON, and context IDs that covered each supplied path.

The adapter requires coverage.py's per-line contexts. Aggregate line coverage is not sufficient to attribute code to a test and is rejected. Context labels are preserved as opaque IDs; configure them to identify individual tests. AURORA does not infer framework test IDs.

The revision argument is resolved to a commit SHA and the command requires a clean worktree at that exact commit. This is only an operator attestation: coverage.py's JSON output does not independently prove which Git revision ran. The report says so explicitly.

See COVERAGE_EVIDENCE.md for the report format and limitations.

## Git revision handling

The Git adapter:

1. accepts a repository directory and two revision strings;
2. resolves each revision to a verified commit object using git rev-parse;
3. uses Git's end-of-options delimiter so a revision beginning with a dash is not parsed as a command option;
4. calls git diff using the resolved SHA values and an argv list, never a shell command string;
5. applies a finite timeout and reports Git failures as structured CLI errors.

For static analysis, the working tree must be clean and its checked-out HEAD must equal the requested --head commit. Ignored, untracked Python source files are also rejected because they could otherwise contaminate the dependency graph.

Git is only asked to read repository metadata and diffs. The analyzer does not check out, build or execute the target revision.

## Python AST extraction

The AST adapter uses Python's standard ast module. It extracts:

- absolute and relative imports (including imported names and line numbers);
- top-level functions, async functions, classes, methods and qualified names;
- call expressions and source line numbers;
- syntax errors as report data.

AST parsing does not import or execute the analyzed Python source. Syntax-invalid files are retained as parse issues and excluded from dependency-edge extraction.

## Dependency graph

The graph is file-level and directed from importer to dependency. It handles:

- import package.module;
- from package.module import Name;
- relative imports such as from .helpers import build;
- parent package initializers along dotted import paths;
- common src/ layouts;
- package initializer files;
- cycles, using a visited set during reverse traversal.

External imports with no matching repository module are ignored. The scanner skips common generated/vendor directories, avoids following symlinks and applies file-count and source-size limits. Skipped oversized or unreadable files are reported as scan warnings.

## Candidate-test selection

Given changed paths, AURORA:

1. marks changed Python modules that exist in the scanned repository;
2. follows reverse import edges to find modules that depend directly or transitively on them;
3. includes impacted files under tests/, plus conventional test_*.py and *_test.py names;
4. includes changed test files directly even if the changed file is not a Python module;
5. returns candidate test paths and a short rationale.

The result is deliberately called a candidate list. Static imports do not prove runtime execution paths, dynamic imports, test coverage or whether a test detects a particular defect. Runtime coverage is a separate measured signal.

## Report interpretation

The static JSON report contains resolved base/head commit IDs, changed files and per-file additions/deletions, Python module and dependency edge counts, impacted Python paths, candidate test paths, syntax errors, scan warnings, rationale and explicit analysis limitations.

The coverage graph report contains a revision attestation, coverage.py format version, report timestamp when available, SHA-256 report checksum, test contexts, source paths, per-edge executed lines, and an optional lookup from changed paths to observed test contexts.

An empty dynamic lookup means the supplied path was not observed under the contexts in the report. It does not prove no test can reach or affect that path. Missing instrumentation, unconfigured contexts, subprocess boundaries and environment differences can all reduce coverage evidence.

## Known limitations

- Python AST/import analysis only; no Java, Kotlin, JavaScript, TypeScript, Go or Rust frontends yet.
- No full Python name-binding or type analysis.
- No runtime call graph.
- Relative import resolution is conservative and limited to modules present in the scanned tree.
- Namespace packages and unusual package roots may need explicit configuration.
- Generated import code, plugin registries and dynamic imports may be missed.
- Test file naming is heuristic; framework collection behavior is not queried.
- Coverage contexts are treated as opaque strings; test framework semantics are not inferred.
- coverage.py JSON does not cryptographically attest the Git revision supplied by the operator.
- The graph is a point-in-time snapshot; historical graph storage, temporal replay and quality evaluation remain open.
- Git submodules are not traversed as independent repositories.

These limitations are reported rather than silently translated into a claim that unlisted tests are safe to skip.
