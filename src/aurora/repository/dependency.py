"""Python import graph and conservative impacted-test candidate analysis."""

from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from aurora.repository.python_ast import (
    ImportReference,
    PythonModuleAnalysis,
    analyze_python_source,
    module_name_from_path,
)


DEFAULT_IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "dist",
    }
)


class RepositoryScanError(ValueError):
    """Raised when repository scanning exceeds safety limits or path constraints."""


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    importer_path: str
    dependency_path: str
    line: int
    import_name: str


@dataclass(frozen=True, slots=True)
class RepositoryGraph:
    root: Path
    modules: tuple[PythonModuleAnalysis, ...]
    edges: tuple[DependencyEdge, ...]
    syntax_errors: tuple[str, ...]
    scan_warnings: tuple[str, ...]

    def module_paths(self) -> frozenset[str]:
        return frozenset(module.path for module in self.modules)


@dataclass(frozen=True, slots=True)
class ImpactResult:
    changed_paths: tuple[str, ...]
    impacted_python_paths: tuple[str, ...]
    candidate_test_paths: tuple[str, ...]
    rationale: tuple[str, ...]


def _is_test_path(path: str) -> bool:
    name = PurePosixPath(path).name
    return name.startswith("test_") or name.endswith("_test.py")


def _module_name(path: Path | PurePosixPath) -> str:
    """Respect the conventional src/ package root while keeping paths repo-relative."""
    module_path = path.relative_to("src") if path.parts and path.parts[0] == "src" else path
    return module_name_from_path(module_path.as_posix())


def _python_files(
    root: Path,
    *,
    max_files: int,
    max_file_bytes: int,
) -> tuple[tuple[Path, ...], tuple[str, ...]]:
    discovered: list[Path] = []
    warnings: list[str] = []
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if name not in DEFAULT_IGNORED_DIRECTORIES
            and not (Path(current) / name).is_symlink()
        )
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            file_path = Path(current) / filename
            if file_path.is_symlink():
                continue
            try:
                relative = file_path.relative_to(root)
                resolved = file_path.resolve(strict=True)
                resolved.relative_to(root)
                file_size = resolved.stat().st_size
            except (OSError, ValueError):
                continue
            if file_size > max_file_bytes:
                warnings.append(
                    f"{relative.as_posix()}: skipped because source exceeds "
                    f"the {max_file_bytes}-byte scan limit"
                )
                continue
            discovered.append(relative)
            if len(discovered) > max_files:
                raise RepositoryScanError(
                    f"repository exceeds the configured Python file limit ({max_files})"
                )
    return (
        tuple(sorted(discovered, key=lambda item: item.as_posix())),
        tuple(sorted(warnings)),
    )


def _module_index(
    paths: tuple[Path, ...],
) -> tuple[dict[str, str], dict[str, str]]:
    module_to_path: dict[str, str] = {}
    path_to_module: dict[str, str] = {}
    for path in paths:
        relative = path.as_posix()
        module_name = _module_name(path)
        path_to_module[relative] = module_name
        if module_name != "__root__":
            module_to_path[module_name] = relative
    return module_to_path, path_to_module


def _relative_base(
    module_name: str,
    importer_path: str,
    level: int,
    module: str | None,
) -> str | None:
    parts = module_name.split(".")
    is_package_initializer = PurePosixPath(importer_path).name == "__init__.py"
    package = parts if is_package_initializer else parts[:-1]
    if not package or level < 1 or level > len(package):
        return None
    anchor = package[: len(package) - (level - 1)]
    if module:
        anchor.extend(part for part in module.split(".") if part)
    return ".".join(anchor)


def _import_module_names(
    module: PythonModuleAnalysis,
    reference: ImportReference,
) -> tuple[str, ...]:
    """Resolve the expected dotted module names even when a target file is missing."""
    if reference.level:
        base = _relative_base(
            module.module_name,
            module.path,
            reference.level,
            reference.module,
        )
        if base is None:
            return ()
    else:
        base = reference.module or ""

    if not base:
        return ()
    names = {base}
    names.update(f"{base}.{imported_name}" for imported_name in reference.names)
    return tuple(sorted(names))


def _resolve_import_targets(
    module: PythonModuleAnalysis,
    reference: ImportReference,
    module_to_path: dict[str, str],
) -> tuple[str, ...]:
    candidates: set[str] = set()
    for imported_module in _import_module_names(module, reference):
        parts = imported_module.split(".")
        for index in range(1, len(parts) + 1):
            module_name = ".".join(parts[:index])
            if module_name in module_to_path:
                candidates.add(module_to_path[module_name])
    return tuple(sorted(candidates))


def build_python_graph(
    repository: str | Path,
    *,
    max_files: int = 10_000,
    max_file_bytes: int = 1_000_000,
) -> RepositoryGraph:
    """Parse Python modules and construct an importer-to-dependency graph."""
    root = Path(repository).expanduser().resolve()
    if not root.is_dir():
        raise RepositoryScanError(f"repository path is not a directory: {root}")
    if max_files < 1 or max_file_bytes < 1:
        raise ValueError("max_files and max_file_bytes must be positive")

    paths, scan_warnings = _python_files(
        root, max_files=max_files, max_file_bytes=max_file_bytes
    )
    module_to_path, path_to_module = _module_index(paths)
    modules: list[PythonModuleAnalysis] = []
    syntax_errors: list[str] = []

    for relative in paths:
        try:
            source = (root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            scan_warnings = tuple(
                sorted((*scan_warnings, f"{relative.as_posix()}: could not read source: {exc}"))
            )
            continue
        analysis = analyze_python_source(
            relative.as_posix(),
            source,
            module_name=path_to_module[relative.as_posix()],
        )
        modules.append(analysis)
        if analysis.syntax_error:
            syntax_errors.append(f"{analysis.path}: {analysis.syntax_error}")

    edges: set[DependencyEdge] = set()
    for module in modules:
        if module.syntax_error:
            continue
        for reference in module.imports:
            for target in _resolve_import_targets(module, reference, module_to_path):
                if target == module.path:
                    continue
                edges.add(
                    DependencyEdge(
                        importer_path=module.path,
                        dependency_path=target,
                        line=reference.line,
                        import_name=reference.module or ".".join(reference.names),
                    )
                )

    return RepositoryGraph(
        root=root,
        modules=tuple(sorted(modules, key=lambda item: item.path)),
        edges=tuple(
            sorted(
                edges,
                key=lambda item: (
                    item.importer_path,
                    item.dependency_path,
                    item.line,
                ),
            )
        ),
        syntax_errors=tuple(sorted(syntax_errors)),
        scan_warnings=tuple(sorted(scan_warnings)),
    )


def compute_test_impact(
    graph: RepositoryGraph,
    changed_paths: tuple[str, ...] | list[str],
) -> ImpactResult:
    """Find changed modules and transitive importers, including likely test files.

    This is conservative static candidate selection. It does not prove runtime
    reachability, test coverage or that a candidate test will detect a regression.
    """
    normalized_changed: set[str] = set()
    for raw_path in changed_paths:
        if not raw_path:
            continue
        candidate = PurePosixPath(raw_path)
        if (
            candidate.is_absolute()
            or ".." in candidate.parts
            or "\\" in raw_path
            or "\x00" in raw_path
        ):
            raise ValueError("changed paths must remain within the repository")
        normalized_changed.add(candidate.as_posix())

    known_paths = graph.module_paths()
    impacted = {path for path in normalized_changed if path in known_paths}
    changed_module_names = {
        _module_name(PurePosixPath(path))
        for path in normalized_changed
        if PurePosixPath(path).suffix == ".py"
    }
    rationale: list[str] = []

    importer_index: dict[str, set[str]] = {}
    for edge in graph.edges:
        importer_index.setdefault(edge.dependency_path, set()).add(edge.importer_path)

    # A deleted/renamed module is absent from the head graph. Match unresolved
    # imports by their expected module name to retain its importer tests as candidates.
    for module in graph.modules:
        if module.syntax_error:
            continue
        if any(
            changed_module_names.intersection(_import_module_names(module, reference))
            for reference in module.imports
        ):
            impacted.add(module.path)

    queue = deque(sorted(impacted))
    while queue:
        dependency = queue.popleft()
        for importer in sorted(importer_index.get(dependency, ())):
            if importer not in impacted:
                impacted.add(importer)
                queue.append(importer)

    changed_test_paths = {path for path in normalized_changed if _is_test_path(path)}
    impacted_test_paths = {path for path in impacted if _is_test_path(path)}
    impacted_test_paths.update(changed_test_paths)

    if impacted:
        rationale.append(
            "Python importers were followed transitively from changed Python modules."
        )
    if changed_test_paths:
        rationale.append("Changed test files are included directly.")
    if graph.syntax_errors:
        rationale.append(
            "One or more Python files could not be parsed; static impact may be incomplete."
        )
    if graph.scan_warnings:
        rationale.append(
            "One or more Python files were skipped during scanning; static impact may be incomplete."
        )
    if not impacted_test_paths:
        rationale.append(
            "No test candidate was identified by the available Python import graph."
        )

    return ImpactResult(
        changed_paths=tuple(sorted(normalized_changed)),
        impacted_python_paths=tuple(sorted(impacted)),
        candidate_test_paths=tuple(sorted(impacted_test_paths)),
        rationale=tuple(rationale),
    )
