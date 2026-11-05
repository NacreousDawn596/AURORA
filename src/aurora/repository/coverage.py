"""Import per-test execution evidence from coverage.py JSON reports.

The adapter consumes coverage.py JSON produced with --show-contexts. Context labels
are preserved as opaque test identifiers; AURORA does not infer framework semantics.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class CoverageReportError(ValueError):
    """Raised when a coverage report is malformed or unsafe to ingest."""


@dataclass(frozen=True, slots=True)
class CoverageEdge:
    """A test context observed executing lines in one source file."""

    test_context: str
    source_path: str
    executed_lines: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TestCodeCoverageGraph:
    """A revision-scoped, file-and-line test-to-code evidence graph."""

    repository: str
    revision: str
    report_version: str
    report_timestamp: str | None
    report_sha256: str
    edges: tuple[CoverageEdge, ...]

    @property
    def test_contexts(self) -> tuple[str, ...]:
        return tuple(sorted({edge.test_context for edge in self.edges}))

    @property
    def source_paths(self) -> tuple[str, ...]:
        return tuple(sorted({edge.source_path for edge in self.edges}))

    @property
    def executed_line_count(self) -> int:
        return sum(len(edge.executed_lines) for edge in self.edges)

    def tests_for_paths(self, changed_paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        """Return contexts that executed any line in one of the changed files."""
        normalized: set[str] = set()
        for raw_path in changed_paths:
            candidate = PurePosixPath(raw_path)
            if (
                not raw_path
                or candidate.is_absolute()
                or ".." in candidate.parts
                or "\\" in raw_path
                or "\x00" in raw_path
            ):
                raise ValueError("changed paths must be safe repository-relative paths")
            normalized.add(candidate.as_posix())
        return tuple(
            sorted({edge.test_context for edge in self.edges if edge.source_path in normalized})
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "analysis_kind": "coverage-context-test-code-graph",
            "repository": self.repository,
            "revision": self.revision,
            "revision_attestation": (
                "The revision is the clean checkout supplied to AURORA; "
                "coverage.py JSON does not independently attest the Git revision."
            ),
            "report_version": self.report_version,
            "report_timestamp": self.report_timestamp,
            "report_sha256": self.report_sha256,
            "test_context_count": len(self.test_contexts),
            "source_file_count": len(self.source_paths),
            "edge_count": len(self.edges),
            "executed_line_edge_count": self.executed_line_count,
            "test_contexts": list(self.test_contexts),
            "source_paths": list(self.source_paths),
            "edges": [edge.to_dict() for edge in self.edges],
        }


def _source_path(repository: Path, raw_path: object) -> str:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise CoverageReportError("coverage file paths must be non-empty strings")
    if "\x00" in raw_path or "\\" in raw_path:
        raise CoverageReportError(f"unsafe coverage file path: {raw_path!r}")

    candidate = Path(raw_path)
    if not candidate.is_absolute():
        relative = PurePosixPath(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise CoverageReportError(f"coverage path escapes the repository: {raw_path!r}")
        candidate = repository.joinpath(*relative.parts)

    resolved = candidate.resolve()
    try:
        relative_path = resolved.relative_to(repository)
    except ValueError as exc:
        raise CoverageReportError(
            f"coverage path resolves outside the repository: {raw_path!r}"
        ) from exc
    if not relative_path.parts:
        raise CoverageReportError("coverage entry must identify a file, not the repository root")
    return PurePosixPath(*relative_path.parts).as_posix()


def load_coverage_graph(
    report_path: str | Path,
    repository: str | Path,
    revision: str,
    *,
    max_report_bytes: int = 50_000_000,
) -> TestCodeCoverageGraph:
    """Load a coverage.py JSON report and build a test-context-to-source graph.

    Generate a per-test report with coverage json --show-contexts. Configure
    coverage dynamic contexts (for example, test-function contexts) before running
    tests. Context names are treated as opaque IDs and are never split or rewritten.
    """
    if max_report_bytes < 1:
        raise ValueError("max_report_bytes must be positive")
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("revision must be a non-empty commit identifier")

    root = Path(repository).expanduser().resolve()
    if not root.is_dir():
        raise CoverageReportError(f"repository path is not a directory: {root}")
    path = Path(report_path).expanduser()
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        raise CoverageReportError(f"could not read coverage report: {exc}") from exc
    if len(raw_bytes) > max_report_bytes:
        raise CoverageReportError(f"coverage report exceeds the {max_report_bytes}-byte size limit")
    try:
        payload: Any = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoverageReportError(f"coverage report is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise CoverageReportError("coverage report root must be a JSON object")

    metadata = payload.get("meta")
    if not isinstance(metadata, dict):
        raise CoverageReportError("coverage report is missing its meta object")
    if metadata.get("show_contexts") is not True:
        raise CoverageReportError(
            "coverage report must include per-line contexts; rerun with --show-contexts"
        )
    files = payload.get("files")
    if not isinstance(files, dict):
        raise CoverageReportError("coverage report files must be a JSON object")

    lines_by_edge: dict[tuple[str, str], set[int]] = defaultdict(set)
    for raw_file, file_data in files.items():
        if not isinstance(file_data, dict):
            raise CoverageReportError(f"coverage data for {raw_file!r} must be an object")
        source_path = _source_path(root, raw_file)
        executed_lines = file_data.get("executed_lines")
        contexts = file_data.get("contexts")
        if not isinstance(executed_lines, list) or not isinstance(contexts, dict):
            raise CoverageReportError(
                f"coverage data for {raw_file!r} needs executed_lines and contexts"
            )
        executed: set[int] = set()
        for line in executed_lines:
            if type(line) is not int or line < 1:
                raise CoverageReportError(
                    f"coverage data for {raw_file!r} contains an invalid executed line"
                )
            executed.add(line)

        for raw_line, raw_contexts in contexts.items():
            if not isinstance(raw_line, str) or not raw_line.isdecimal():
                raise CoverageReportError(
                    f"coverage data for {raw_file!r} contains an invalid context line key"
                )
            line = int(raw_line)
            if line < 1 or line not in executed:
                raise CoverageReportError(
                    f"context line {raw_line!r} for {raw_file!r} is not an executed line"
                )
            if not isinstance(raw_contexts, list):
                raise CoverageReportError(
                    f"contexts for line {raw_line!r} in {raw_file!r} must be a list"
                )
            for context in raw_contexts:
                if not isinstance(context, str) or not context.strip():
                    raise CoverageReportError("test context identifiers must be non-empty strings")
                lines_by_edge[(context, source_path)].add(line)

    edges = tuple(
        CoverageEdge(
            test_context=test_context,
            source_path=source_path,
            executed_lines=tuple(sorted(lines)),
        )
        for (test_context, source_path), lines in sorted(lines_by_edge.items())
    )
    timestamp = metadata.get("timestamp")
    return TestCodeCoverageGraph(
        repository=str(root),
        revision=revision.strip(),
        report_version=str(metadata.get("version", "unknown")),
        report_timestamp=timestamp if isinstance(timestamp, str) else None,
        report_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        edges=edges,
    )
