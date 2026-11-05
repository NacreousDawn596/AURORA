import json
from pathlib import Path

import pytest

from aurora.repository.coverage import CoverageReportError, load_coverage_graph


def _write_report(path: Path, *, files: dict[str, object] | None = None) -> Path:
    payload = {
        "meta": {"version": 3, "show_contexts": True, "timestamp": "2026-11-05T12:00:00Z"},
        "files": files
        if files is not None
        else {
            "src/app/service.py": {
                "executed_lines": [10, 11, 12],
                "contexts": {
                    "10": ["tests.test_service.test_get", "tests.test_service.test_post"],
                    "11": ["tests.test_service.test_get"],
                },
            },
            "src/app/model.py": {
                "executed_lines": [4],
                "contexts": {"4": ["tests.test_service.test_get"]},
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_coverage_graph_builds_test_to_code_edges(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "src/app").mkdir(parents=True)
    report = _write_report(tmp_path / "coverage.json")

    graph = load_coverage_graph(report, repository, "a" * 40)

    assert graph.test_contexts == (
        "tests.test_service.test_get",
        "tests.test_service.test_post",
    )
    assert graph.source_paths == ("src/app/model.py", "src/app/service.py")
    assert graph.tests_for_paths(["src/app/service.py"]) == graph.test_contexts
    assert graph.executed_line_count == 4
    assert len(graph.edges) == 3
    payload = graph.to_dict()
    assert payload["analysis_kind"] == "coverage-context-test-code-graph"
    assert payload["revision_attestation"].startswith("The revision is")


def test_load_coverage_graph_accepts_absolute_paths_inside_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    source = repository / "src/app.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    report = _write_report(
        tmp_path / "coverage.json",
        files={
            str(source): {
                "executed_lines": [1],
                "contexts": {"1": ["tests.test_app.test_value"]},
            }
        },
    )

    graph = load_coverage_graph(report, repository, "b" * 40)

    assert graph.source_paths == ("src/app.py",)


def test_load_coverage_graph_requires_contexts(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    report = tmp_path / "coverage.json"
    report.write_text(
        json.dumps({"meta": {"show_contexts": False}, "files": {}}),
        encoding="utf-8",
    )

    with pytest.raises(CoverageReportError, match="--show-contexts"):
        load_coverage_graph(report, repository, "a" * 40)


@pytest.mark.parametrize("raw_path", ["../outside.py", "/etc/passwd", "src\\\\outside.py"])
def test_load_coverage_graph_rejects_unsafe_paths(tmp_path: Path, raw_path: str) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    report = _write_report(
        tmp_path / "coverage.json",
        files={
            raw_path: {
                "executed_lines": [1],
                "contexts": {"1": ["tests.test_app.test_value"]},
            }
        },
    )

    with pytest.raises(CoverageReportError):
        load_coverage_graph(report, repository, "a" * 40)


def test_load_coverage_graph_rejects_context_for_unexecuted_line(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    report = _write_report(
        tmp_path / "coverage.json",
        files={
            "src/app.py": {
                "executed_lines": [1],
                "contexts": {"2": ["tests.test_app.test_value"]},
            }
        },
    )

    with pytest.raises(CoverageReportError, match="not an executed line"):
        load_coverage_graph(report, repository, "a" * 40)


def test_load_coverage_graph_enforces_report_size_limit(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    report = _write_report(tmp_path / "coverage.json")

    with pytest.raises(CoverageReportError, match="size limit"):
        load_coverage_graph(report, repository, "a" * 40, max_report_bytes=1)


def test_tests_for_paths_rejects_path_traversal(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    report = _write_report(tmp_path / "coverage.json")
    graph = load_coverage_graph(report, repository, "a" * 40)

    with pytest.raises(ValueError, match="repository-relative"):
        graph.tests_for_paths(["../outside.py"])


def test_load_coverage_graph_rejects_invalid_revision(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    report = _write_report(tmp_path / "coverage.json")

    with pytest.raises(ValueError, match="revision"):
        load_coverage_graph(report, repository, "")
