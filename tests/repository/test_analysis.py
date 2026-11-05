import subprocess
from pathlib import Path

import pytest

from aurora.repository.analysis import analyze_repository
from aurora.repository.git import GitAnalysisError


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_project(repo: Path) -> tuple[str, str]:
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "AURORA tests")
    _git(repo, "config", "user.email", "aurora-tests@example.invalid")
    files = {
        "src/app/core.py": "VALUE = 1\n",
        "src/app/service.py": "from app.core import VALUE\n",
        "tests/test_service.py": "from app.service import VALUE\ndef test_value():\n    assert VALUE\n",
    }
    for name, source in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "src/app/core.py").write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "change core")
    head = _git(repo, "rev-parse", "HEAD")
    return base, head


def test_analyze_repository_reports_diff_and_test_impact(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    base, head = _init_project(repo)

    report = analyze_repository(repo, base, head)

    assert report.base_commit == base
    assert report.head_commit == head
    assert report.changed_file_count == 1
    assert report.additions == 1
    assert report.deletions == 1
    assert report.changed_files[0].path == "src/app/core.py"
    assert "src/app/service.py" in report.impacted_python_paths
    assert report.candidate_test_paths == ("tests/test_service.py",)
    payload = report.to_dict()
    assert payload["analysis_kind"] == "static-python-import-impact"
    assert payload["limitations"]

def test_analysis_rejects_dirty_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    base, head = _init_project(repo)
    (repo / "src/app/core.py").write_text("VALUE = 99\n", encoding="utf-8")

    with pytest.raises(GitAnalysisError, match="not clean"):
        analyze_repository(repo, base, head)
