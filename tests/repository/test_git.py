import shutil
import subprocess
from pathlib import Path

import pytest

from aurora.repository.git import (
    GitAnalysisError,
    compare_revisions,
    ensure_clean_head,
    resolve_commit,
)

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="Git is not installed")


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(repo: Path) -> str:
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "AURORA tests")
    _git(repo, "config", "user.email", "aurora-tests@example.invalid")
    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    return _git(repo, "rev-parse", "HEAD")


def test_resolve_commit_returns_full_sha_and_supports_tags(tmp_path: Path) -> None:
    repo = tmp_path / "repo with spaces"
    commit = _init_repo(repo)
    _git(repo, "tag", "v1")
    assert resolve_commit(repo, "HEAD") == commit
    assert resolve_commit(repo, "v1") == commit


def test_compare_revisions_returns_diff_without_shell_interpolation(tmp_path: Path) -> None:
    repo = tmp_path / "repo with spaces"
    base = _init_repo(repo)
    (repo / "src" / "module.py").write_text("VALUE = 2\nNEW = True\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "change")
    head = _git(repo, "rev-parse", "HEAD")

    comparison = compare_revisions(repo, base, head)

    assert comparison.base_revision == base
    assert comparison.head_revision == head
    assert "VALUE = 2" in comparison.diff_text
    assert "NEW = True" in comparison.diff_text


def test_missing_and_option_like_revisions_are_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    with pytest.raises(GitAnalysisError):
        resolve_commit(repo, "does-not-exist")
    with pytest.raises(GitAnalysisError):
        resolve_commit(repo, "--help")


def test_non_repository_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(GitAnalysisError, match="not a directory"):
        resolve_commit(tmp_path / "missing", "HEAD")


def test_empty_revision_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    with pytest.raises(GitAnalysisError, match="non-empty"):
        resolve_commit(repo, "   ")


def test_invalid_repository_path_is_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(GitAnalysisError, match="not a directory"):
        resolve_commit(file_path, "HEAD")


def test_invalid_timeout_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    for timeout in (0, -1, float("inf"), float("nan")):
        with pytest.raises(GitAnalysisError, match="timeout_seconds"):
            resolve_commit(repo, "HEAD", timeout_seconds=timeout)


def test_clean_head_requires_exact_revision_and_clean_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    head = _init_repo(repo)
    ensure_clean_head(repo, head)

    with pytest.raises(GitAnalysisError, match="must match"):
        ensure_clean_head(repo, "0" * 40)

    (repo / "src" / "module.py").write_text("VALUE = 99\n", encoding="utf-8")
    with pytest.raises(GitAnalysisError, match="not clean"):
        ensure_clean_head(repo, head)


def test_clean_head_rejects_ignored_untracked_python_sources(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / ".gitignore").write_text("generated.py\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-m", "ignore generated source")
    head = _git(repo, "rev-parse", "HEAD")
    (repo / "generated.py").write_text("VALUE = 2\n", encoding="utf-8")

    with pytest.raises(GitAnalysisError, match="ignored, untracked Python"):
        ensure_clean_head(repo, head)


def test_revision_with_nul_byte_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    with pytest.raises(GitAnalysisError, match="NUL"):
        resolve_commit(repo, "HEAD" + chr(0) + "--help")
