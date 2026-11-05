from pathlib import Path

from aurora.repository.python_ast import analyze_python_source, module_name_from_path


def test_module_name_from_source_layout_paths() -> None:
    assert module_name_from_path("aurora/repository/git.py") == "aurora.repository.git"
    assert module_name_from_path("aurora/repository/__init__.py") == "aurora.repository"
    assert module_name_from_path("__init__.py") == "__root__"


def test_module_name_rejects_absolute_and_parent_paths() -> None:
    import pytest

    with pytest.raises(ValueError, match="repository-relative"):
        module_name_from_path("/tmp/module.py")
    with pytest.raises(ValueError, match="repository-relative"):
        module_name_from_path("../module.py")
    with pytest.raises(ValueError, match="end in .py"):
        module_name_from_path("module.txt")


def test_ast_extracts_imports_symbols_and_calls_without_execution(tmp_path: Path) -> None:
    sentinel = tmp_path / "executed.txt"
    source = f"""
import os as operating_system
from .helpers import build, CONSTANT
from package.submodule import Thing

class Worker:
    def run(self, value):
        return operating_system.path.join(value, "x")

async def fetch():
    return await build()

def side_effect():
    open({str(sentinel)!r}, "w").write("bad")
"""
    result = analyze_python_source("pkg/worker.py", source)

    assert result.syntax_error is None
    assert [(item.module, item.names, item.level) for item in result.imports] == [
        ("os", (), 0),
        ("helpers", ("build", "CONSTANT"), 1),
        ("package.submodule", ("Thing",), 0),
    ]
    symbol_names = {(item.qualified_name, item.kind) for item in result.symbols}
    assert ("Worker", "class") in symbol_names
    assert ("Worker.run", "method") in symbol_names
    assert ("fetch", "async_function") in symbol_names
    assert ("side_effect", "function") in symbol_names
    calls = {item.expression for item in result.calls}
    assert "operating_system.path.join" in calls
    assert "open" in calls
    assert not sentinel.exists()


def test_ast_reports_syntax_error_as_data() -> None:
    result = analyze_python_source("broken.py", "def incomplete(:\n    pass\n")
    assert result.syntax_error is not None
    assert "line 1" in result.syntax_error
    assert result.imports == ()
    assert result.symbols == ()


def test_ast_records_line_numbers_and_qualified_names() -> None:
    source = "class A:\n    class B:\n        def method(self):\n            return target.call()\n"
    result = analyze_python_source("a.py", source)
    assert [(item.qualified_name, item.line, item.end_line) for item in result.symbols] == [
        ("A", 1, 4),
        ("A.B", 2, 4),
        ("A.B.method", 3, 4),
    ]
    assert result.calls[0].expression == "target.call"
    assert result.calls[0].line == 4


def test_ast_result_serializes_to_json_compatible_data() -> None:
    result = analyze_python_source("a.py", "import json\njson.loads('{}')\n")
    payload = result.to_dict()
    assert payload["module_name"] == "a"
    assert payload["imports"][0]["module"] == "json"
    assert payload["calls"][0]["expression"] == "json.loads"
