# Contributing

AURORA is both a software project and a research artifact. Contributions must preserve reproducibility and distinguish implemented behavior from proposed research.

## Setup

Requires Python 3.11+.

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -e ".[dev]"
    pytest

## Quality checks

    ruff check .
    ruff format --check .
    mypy
    pytest --cov=aurora --cov-report=term-missing
    aurora-benchmark --help

## Working with LRTS

Do not commit downloaded research datasets. Follow docs/DATASETS.md, keep the exact dataset version and license/provenance notes, and store result artifacts outside source control unless they are small and explicitly approved.

Use strict ingestion by default. If you use permissive mode, preserve the skipped-record report in the experiment output.

## Guidelines

- Keep core scheduling logic deterministic where possible.
- Test edge cases, invariants and failure paths.
- Do not silently convert missing evidence into zero risk.
- Keep predictions separate from confirmed labels.
- Preserve timestamps and provenance for historical features.
- Never use future evidence during replay.
- Record random seeds and environment identifiers.
- Do not commit credentials or sensitive execution data.
- Treat evaluated repository code as untrusted.
- Use typed interfaces between agents and execution tools.
- Document assumptions and limitations.

## Pull requests

Explain the problem, design, alternatives, tests/experiments, schema/reproducibility impact and security implications. State whether claims are measured or illustrative. CI must pass before merge. Research hypothesis, metric or split changes must update the research documentation and changelog.
