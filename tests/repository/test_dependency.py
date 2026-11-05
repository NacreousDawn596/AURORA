from pathlib import Path

import pytest

from aurora.repository.dependency import (
    RepositoryScanError,
    build_python_graph,
    compute_test_impact,
)


def _write(root: Path, relative: str, source: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


def _sample_repository(root: Path) -> None:
    _write(root, "src/pkg/__init__.py", "from .core import Core\n")
    _write(root, "src/pkg/core.py", "from .base import Base\nfrom . import helper\nclass Core(Base):\n    pass\n")
    _write(root, "src/pkg/base.py", "class Base:\n    pass\n")
    _write(root, "src/pkg/helper.py", "from .core import Core\n")
    _write(root, "src/app/service.py", "from pkg.core import Core\n")
    _write(root, "tests/test_service.py", "from app.service import Service\ndef test_service():\n    pass\n")
    _write(root, "tests/test_core.py", "from pkg.core import Core\ndef test_core():\n    pass\n")
    _write(root, "tests/helpers.py", "VALUE = 1\n")
    _write(root, ".venv/lib/ignored.py", "raise RuntimeError('must never execute')\n")
    _write(root, "node_modules/pkg/ignored.py", "this is not python!!!\n")


def test_graph_resolves_src_root_relative_and_absolute_imports_and_cycles(tmp_path: Path) -> None:
    _sample_repository(tmp_path)

    graph = build_python_graph(tmp_path)

    edges = {(edge.importer_path, edge.dependency_path) for edge in graph.edges}
    assert ("src/pkg/__init__.py", "src/pkg/core.py") in edges
    assert ("src/pkg/core.py", "src/pkg/base.py") in edges
    assert ("src/pkg/core.py", "src/pkg/helper.py") in edges
    assert ("src/pkg/helper.py", "src/pkg/core.py") in edges
    assert ("src/app/service.py", "src/pkg/core.py") in edges
    assert ("tests/test_service.py", "src/app/service.py") in edges
    assert ("tests/test_core.py", "src/pkg/core.py") in edges
    assert not any("ignored.py" in module.path for module in graph.modules)
    assert graph.syntax_errors == ()


def test_impact_walks_transitive_importers_and_selects_related_tests(tmp_path: Path) -> None:
    _sample_repository(tmp_path)
    graph = build_python_graph(tmp_path)

    impact = compute_test_impact(graph, ["src/pkg/base.py"])

    assert set(impact.impacted_python_paths) >= {
        "src/pkg/base.py",
        "src/pkg/core.py",
        "src/pkg/helper.py",
        "src/pkg/__init__.py",
        "src/app/service.py",
        "tests/test_core.py",
        "tests/test_service.py",
    }
    assert set(impact.candidate_test_paths) == {
        "tests/test_core.py",
        "tests/test_service.py",
    }
    assert any("transitively" in item for item in impact.rationale)


def test_changed_test_file_is_included_directly_even_without_import_edges(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "src/app/module.py", "VALUE = 1\n")
    graph = build_python_graph(tmp_path)

    impact = compute_test_impact(graph, ["tests/test_lonely.py"])

    assert impact.candidate_test_paths == ("tests/test_lonely.py",)
    assert "Changed test files are included directly." in impact.rationale


def test_syntax_errors_are_reported_and_graph_still_builds(tmp_path: Path) -> None:
    _write(tmp_path, "src/good.py", "VALUE = 1\n")
    _write(tmp_path, "src/broken.py", "def broken(:\n")
    graph = build_python_graph(tmp_path)

    assert len(graph.modules) == 2
    assert len(graph.syntax_errors) == 1
    assert "src/broken.py" in graph.syntax_errors[0]
    assert any("incomplete" in item for item in compute_test_impact(graph, ["src/good.py"]).rationale)


def test_max_file_limit_is_enforced(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "A = 1\n")
    _write(tmp_path, "b.py", "B = 2\n")
    with pytest.raises(RepositoryScanError, match="file limit"):
        build_python_graph(tmp_path, max_files=1)


def test_file_size_limit_skips_large_source(tmp_path: Path) -> None:
    _write(tmp_path, "small.py", "A = 1\n")
    _write(tmp_path, "large.py", "x = '" + "a" * 100 + "'\n")
    graph = build_python_graph(tmp_path, max_file_bytes=20)
    assert {item.path for item in graph.modules} == {"small.py"}
    assert len(graph.scan_warnings) == 1
    assert "large.py" in graph.scan_warnings[0]


def test_dependency_scan_rejects_invalid_root_and_limits(tmp_path: Path) -> None:
    with pytest.raises(RepositoryScanError, match="not a directory"):
        build_python_graph(tmp_path / "missing")
    with pytest.raises(ValueError, match="positive"):
        build_python_graph(tmp_path, max_files=0)
    with pytest.raises(ValueError, match="positive"):
        build_python_graph(tmp_path, max_file_bytes=0)


@pytest.mark.parametrize(
    "bad_path",
    ["../outside.py", "/absolute.py", "src/../../outside.py", r"src\\..\\outside.py"],
)
def test_impact_rejects_paths_outside_repository(tmp_path: Path, bad_path: str) -> None:
    graph = build_python_graph(tmp_path)
    with pytest.raises(ValueError, match="within the repository"):
        compute_test_impact(graph, [bad_path])


def test_symlinked_python_files_are_not_followed(tmp_path: Path) -> None:
    _write(tmp_path, "real.py", "VALUE = 1\n")
    link = tmp_path / "linked.py"
    try:
        link.symlink_to(tmp_path / "real.py")
    except OSError:
        pytest.skip("symlinks are not supported by this environment")
    graph = build_python_graph(tmp_path)
    assert {item.path for item in graph.modules} == {"real.py"}

def test_relative_import_above_top_level_is_not_added_to_graph(tmp_path: Path) -> None:
    _write(tmp_path, "module.py", "from .helper import VALUE\n")
    _write(tmp_path, "helper.py", "VALUE = 1\n")
    graph = build_python_graph(tmp_path)
    assert graph.edges == ()

def test_deleted_module_importers_are_still_candidate_tests(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/consumer.py", "from pkg.old_module import Removed\n")
    _write(tmp_path, "tests/test_consumer.py", "from pkg.consumer import Removed\n")
    graph = build_python_graph(tmp_path)

    impact = compute_test_impact(graph, ["src/pkg/old_module.py"])

    assert "src/pkg/consumer.py" in impact.impacted_python_paths
    assert impact.candidate_test_paths == ("tests/test_consumer.py",)

def test_dotted_import_tracks_parent_package_initializers(tmp_path: Path) -> None:
    _write(tmp_path, "src/pkg/__init__.py", "PACKAGE = True\n")
    _write(tmp_path, "src/pkg/sub/__init__.py", "SUBPACKAGE = True\n")
    _write(tmp_path, "src/pkg/sub/core.py", "VALUE = 1\n")
    _write(tmp_path, "src/app.py", "from pkg.sub.core import VALUE\n")

    graph = build_python_graph(tmp_path)
    edges = {(edge.importer_path, edge.dependency_path) for edge in graph.edges}

    assert ("src/app.py", "src/pkg/__init__.py") in edges
    assert ("src/app.py", "src/pkg/sub/__init__.py") in edges
    assert ("src/app.py", "src/pkg/sub/core.py") in edges
