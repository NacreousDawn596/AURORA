import json
import subprocess
from pathlib import Path

import pytest

from aurora.benchmark.cli import main


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _repo(repo: Path) -> tuple[str, str]:
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "AURORA tests")
    _git(repo, "config", "user.email", "aurora-tests@example.invalid")
    source = repo / "src" / "pkg.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test = repo / "tests" / "test_pkg.py"
    test.parent.mkdir(parents=True)
    test.write_text("from pkg import VALUE\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    base = _git(repo, "rev-parse", "HEAD")
    source.write_text("VALUE = 2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "change")
    return base, _git(repo, "rev-parse", "HEAD")


def test_analyze_repo_cli_writes_json_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "project"
    base, head = _repo(repo)
    assert (
        main(
            [
                "analyze-repo",
                "--repo-path",
                str(repo),
                "--base",
                base,
                "--head",
                head,
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["changed_file_count"] == 1
    assert payload["candidate_test_paths"] == ["tests/test_pkg.py"]


def test_analyze_repo_cli_rejects_bad_ref(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    _repo(repo)
    with pytest.raises(SystemExit) as error:
        main(
            [
                "analyze-repo",
                "--repo-path",
                str(repo),
                "--base",
                "does-not-exist",
                "--head",
                "HEAD",
            ]
        )
    assert error.value.code == 2


def test_analyze_repo_cli_can_write_report_to_file(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    base, head = _repo(repo)
    output = tmp_path / "reports" / "impact.json"

    assert (
        main(
            [
                "analyze-repo",
                "--repo-path",
                str(repo),
                "--base",
                base,
                "--head",
                head,
                "--output",
                str(output),
            ]
        )
        == 0
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["base_commit"] == base
    assert payload["head_commit"] == head
