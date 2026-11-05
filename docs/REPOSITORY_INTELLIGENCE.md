# Repository Intelligence (Python-first)

## Purpose

The first repository-intelligence slice turns a Git revision range into an auditable, conservative list of Python test files worth considering. It is designed as an evidence collector for later AURORA scheduling, not a replacement for a real test runner or runtime coverage tool.

## CLI

```bash
aurora-benchmark analyze-repo \
  --repo-path /path/to/project \
  --base origin/main \
  --head HEAD \
  --output results/impact.json
```

The command resolves both refs to commit object IDs, asks Git for a no-external-diff unified patch, parses changed paths, scans Python source and writes a JSON report.

Additional safety/scale controls:

- `--timeout-seconds`: timeout for each Git command (default 30 seconds).
- `--max-files`: maximum number of scanned Python files (default 10,000).
- `--max-file-bytes`: maximum size of an individual Python source file (default 1,000,000 bytes).
- `--output -`: write JSON to stdout.

The command does not require the external LRTS dataset.

## Git revision handling

The Git adapter:

1. accepts a repository directory and two revision strings;
2. resolves each revision to a verified commit object using `git rev-parse`;
3. uses Git's end-of-options delimiter so a revision beginning with a dash is not parsed as a command option;
4. calls `git diff` using the resolved SHA values and an argv list, never a shell command string;
5. applies a finite timeout and reports Git failures as structured CLI errors.

For reproducibility, analysis requires the working tree to be clean and its checked-out `HEAD` to equal the requested `--head` commit. Ignored, untracked Python source files are also rejected because they could otherwise contaminate the dependency graph.

Git is only asked to read repository metadata and diffs. The analyzer does not check out, build or execute the target revision.

## Python AST extraction

The AST adapter uses Python's standard `ast` module. It extracts:

- absolute and relative imports (including imported names and line numbers);
- top-level functions, async functions, classes, methods and qualified names;
- call expressions and source line numbers;
- syntax errors as report data.

AST parsing does not import or execute the analyzed Python source. Syntax-invalid files are retained as parse issues and excluded from the dependency-edge extraction.

## Dependency graph

The graph is file-level and directed from importer to dependency. It handles:

- `import package.module`;
- `from package.module import Name`;
- relative imports such as `from .helpers import build`;
- parent package initializers along dotted import paths;
- common `src/` layouts;
- package initializer files;
- cycles, using a visited set during reverse traversal.

External imports with no matching repository module are ignored. The scanner skips common generated/vendor directories, avoids following symlinks and applies file-count and source-size limits. Skipped oversized or unreadable files are reported as scan warnings.

## Candidate-test selection

Given changed paths, AURORA:

1. marks changed Python modules that exist in the scanned repository;
2. follows reverse import edges to find modules that depend directly or transitively on them;
3. includes impacted files under `tests/`, plus conventional `test_*.py` and `*_test.py` names;
4. includes changed test files directly even if the changed file is not a Python module;
5. returns candidate test paths and a short rationale.

The result is deliberately called a *candidate* list. Static imports do not prove runtime execution paths, dynamic imports, test coverage or whether a test detects a particular defect. A future stage should join this graph with real coverage and observed test execution data.

## Report interpretation

The JSON report contains:

- resolved base/head commit IDs;
- changed files and per-file additions/deletions;
- Python module and dependency edge counts;
- impacted Python paths;
- candidate test paths;
- syntax errors and scan warnings;
- rationale and explicit analysis limitations.

An empty candidate list does not mean no tests are affected. It can mean the change is outside Python, dependencies are dynamic, imports are unresolved, or no conventional tests were found.

## Known limitations

- Python only; no Java, Kotlin, JavaScript, TypeScript, Go or Rust frontends yet.
- No full Python name-binding or type analysis.
- No runtime coverage or call graph.
- Relative import resolution is conservative and limited to modules present in the scanned tree.
- Namespace packages and unusual package roots may need explicit configuration.
- Generated import code, plugin registries and dynamic imports may be missed.
- Test file naming is heuristic; framework collection behavior is not queried.
- Git submodules are not traversed as independent repositories.

These limitations are reported rather than silently translated into a claim that unlisted tests are safe to skip.
