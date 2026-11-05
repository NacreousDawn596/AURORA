"""Non-executing Python AST extraction for repository intelligence."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True, slots=True)
class ImportReference:
    module: str | None
    names: tuple[str, ...]
    level: int
    line: int


@dataclass(frozen=True, slots=True)
class SymbolReference:
    name: str
    qualified_name: str
    kind: str
    line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class CallReference:
    expression: str
    line: int


@dataclass(frozen=True, slots=True)
class PythonModuleAnalysis:
    path: str
    module_name: str
    imports: tuple[ImportReference, ...]
    symbols: tuple[SymbolReference, ...]
    calls: tuple[CallReference, ...]
    syntax_error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def module_name_from_path(path: str | PurePosixPath) -> str:
    """Convert a repository-relative Python path to a dotted module name."""
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Python module path must be repository-relative")
    parts = list(relative.parts)
    if not parts or relative.suffix != ".py":
        raise ValueError("Python module path must end in .py")
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = relative.stem
    if not parts:
        return "__root__"
    return ".".join(parts)


def _expression_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _expression_name(node.value)
        return f"{parent}.{node.attr}" if parent else None
    if isinstance(node, ast.Call):
        return _expression_name(node.func)
    return None


def _collect_symbols(
    body: list[ast.stmt],
    *,
    parent: tuple[str, ...] = (),
) -> list[SymbolReference]:
    symbols: list[SymbolReference] = []
    for node in body:
        if isinstance(node, ast.ClassDef):
            qualified = (*parent, node.name)
            symbols.append(
                SymbolReference(
                    name=node.name,
                    qualified_name=".".join(qualified),
                    kind="class",
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )
            symbols.extend(_collect_symbols(node.body, parent=qualified))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qualified = (*parent, node.name)
            kind = (
                "method"
                if parent
                else ("async_function" if isinstance(node, ast.AsyncFunctionDef) else "function")
            )
            if parent and isinstance(node, ast.AsyncFunctionDef):
                kind = "async_method"
            symbols.append(
                SymbolReference(
                    name=node.name,
                    qualified_name=".".join(qualified),
                    kind=kind,
                    line=node.lineno,
                    end_line=getattr(node, "end_lineno", node.lineno),
                )
            )
            symbols.extend(_collect_symbols(node.body, parent=qualified))
    return symbols


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[ImportReference] = []
        self.calls: list[CallReference] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ImportReference(module=alias.name, names=(), level=0, line=node.lineno)
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.imports.append(
            ImportReference(
                module=node.module,
                names=tuple(alias.name for alias in node.names),
                level=node.level,
                line=node.lineno,
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        expression = _expression_name(node.func)
        if expression:
            self.calls.append(CallReference(expression=expression, line=node.lineno))
        self.generic_visit(node)


def analyze_python_source(
    path: str | PurePosixPath,
    source: str,
    *,
    module_name: str | None = None,
) -> PythonModuleAnalysis:
    """Extract imports, definitions and call expressions without executing code.

    Syntax errors are returned as structured analysis data. Other unexpected errors
    are allowed to propagate so callers do not silently conceal implementation bugs.
    """
    relative_path = PurePosixPath(path)
    path_text = relative_path.as_posix()
    resolved_module_name = module_name or module_name_from_path(relative_path)
    try:
        tree = ast.parse(source, filename=path_text, type_comments=True)
    except SyntaxError as exc:
        location = f"{exc.msg} (line {exc.lineno or 0}, column {exc.offset or 0})"
        return PythonModuleAnalysis(
            path=path_text,
            module_name=resolved_module_name,
            imports=(),
            symbols=(),
            calls=(),
            syntax_error=location,
        )

    visitor = _ImportVisitor()
    visitor.visit(tree)
    return PythonModuleAnalysis(
        path=path_text,
        module_name=resolved_module_name,
        imports=tuple(sorted(visitor.imports, key=lambda item: (item.line, item.module or ""))),
        symbols=tuple(
            sorted(_collect_symbols(tree.body), key=lambda item: (item.line, item.qualified_name))
        ),
        calls=tuple(sorted(visitor.calls, key=lambda item: (item.line, item.expression))),
    )
