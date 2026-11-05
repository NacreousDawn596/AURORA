"""End-to-end static repository impact report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from aurora.benchmark.change import ChangeSummary, parse_unified_diff
from aurora.repository.dependency import (
    ImpactResult,
    RepositoryGraph,
    build_python_graph,
    compute_test_impact,
)
from aurora.repository.git import compare_revisions, ensure_clean_head


@dataclass(frozen=True, slots=True)
class ChangedPathRecord:
    path: str
    old_path: str | None
    additions: int
    deletions: int
    is_binary: bool


@dataclass(frozen=True, slots=True)
class RepositoryAnalysisReport:
    repository: str
    base_commit: str
    head_commit: str
    changed_files: tuple[ChangedPathRecord, ...]
    python_module_count: int
    dependency_edge_count: int
    impacted_python_paths: tuple[str, ...]
    candidate_test_paths: tuple[str, ...]
    syntax_errors: tuple[str, ...]
    scan_warnings: tuple[str, ...]
    rationale: tuple[str, ...]

    @property
    def changed_file_count(self) -> int:
        return len(self.changed_files)

    @property
    def additions(self) -> int:
        return sum(item.additions for item in self.changed_files)

    @property
    def deletions(self) -> int:
        return sum(item.deletions for item in self.changed_files)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["changed_file_count"] = self.changed_file_count
        payload["additions"] = self.additions
        payload["deletions"] = self.deletions
        payload["analysis_kind"] = "static-python-import-impact"
        payload["limitations"] = [
            "Python source files only; other languages are not analyzed.",
            "Import relationships approximate dependencies and do not prove runtime use.",
            "Candidate tests are suggestions, not guaranteed fault-detecting tests.",
            "Syntax errors, skipped files and dynamic imports can make the graph incomplete.",
        ]
        return payload


def _changed_paths(summary: ChangeSummary) -> tuple[str, ...]:
    paths: set[str] = set()
    for item in summary.files:
        paths.add(item.path)
        if item.old_path:
            paths.add(item.old_path)
    return tuple(sorted(paths))


def analyze_repository(
    repository: str | Path,
    base_revision: str,
    head_revision: str,
    *,
    timeout_seconds: float = 30.0,
    max_files: int = 10_000,
    max_file_bytes: int = 1_000_000,
) -> RepositoryAnalysisReport:
    """Analyze Git changes and compute conservative Python impacted-test candidates."""
    comparison = compare_revisions(
        repository,
        base_revision,
        head_revision,
        timeout_seconds=timeout_seconds,
    )
    summary = parse_unified_diff(comparison.diff_text)
    ensure_clean_head(
        comparison.repository,
        comparison.head_revision,
        timeout_seconds=timeout_seconds,
    )
    graph: RepositoryGraph = build_python_graph(
        comparison.repository,
        max_files=max_files,
        max_file_bytes=max_file_bytes,
    )
    impact: ImpactResult = compute_test_impact(graph, _changed_paths(summary))
    changed_records = tuple(
        ChangedPathRecord(
            path=item.path,
            old_path=item.old_path,
            additions=item.additions,
            deletions=item.deletions,
            is_binary=item.is_binary,
        )
        for item in summary.files
    )
    return RepositoryAnalysisReport(
        repository=str(comparison.repository),
        base_commit=comparison.base_revision,
        head_commit=comparison.head_revision,
        changed_files=changed_records,
        python_module_count=len(graph.modules),
        dependency_edge_count=len(graph.edges),
        impacted_python_paths=impact.impacted_python_paths,
        candidate_test_paths=impact.candidate_test_paths,
        syntax_errors=graph.syntax_errors,
        scan_warnings=graph.scan_warnings,
        rationale=impact.rationale,
    )
