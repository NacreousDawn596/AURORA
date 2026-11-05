"""Safe Git revision comparison used by repository analysis."""

from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitAnalysisError(RuntimeError):
    """Raised when the requested Git comparison cannot be completed."""


@dataclass(frozen=True, slots=True)
class GitComparison:
    repository: Path
    base_revision: str
    head_revision: str
    diff_text: str


def _run_git(
    repository: Path,
    args: list[str],
    *,
    timeout_seconds: float,
) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise GitAnalysisError("Git executable was not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitAnalysisError(f"Git command timed out after {timeout_seconds:g}s") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown Git error"
        raise GitAnalysisError(detail)
    return completed.stdout


def resolve_commit(
    repository: str | Path,
    revision: str,
    *,
    timeout_seconds: float = 15.0,
) -> str:
    """Resolve an arbitrary Git revision to a verified commit SHA.

    The revision is passed as one argv value and is separated from options by
    --end-of-options, so a value beginning with a dash cannot become a Git flag.
    """
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise GitAnalysisError("timeout_seconds must be finite and positive")
    root = Path(repository).expanduser().resolve()
    if not root.is_dir():
        raise GitAnalysisError(f"repository path is not a directory: {root}")
    if not isinstance(revision, str) or not revision.strip():
        raise GitAnalysisError("revision must be a non-empty string")
    if "\x00" in revision:
        raise GitAnalysisError("revision contains a NUL byte")
    spec = f"{revision.strip()}^{{commit}}"
    output = _run_git(
        root,
        ["rev-parse", "--verify", "--end-of-options", spec],
        timeout_seconds=timeout_seconds,
    )
    sha = output.strip().splitlines()[-1] if output.strip() else ""
    if len(sha) not in {40, 64} or any(char not in "0123456789abcdefABCDEF" for char in sha):
        raise GitAnalysisError(f"Git returned an invalid commit identifier for {revision!r}")
    return sha.lower()


def ensure_clean_head(
    repository: str | Path,
    expected_head: str,
    *,
    timeout_seconds: float = 15.0,
) -> None:
    """Require a clean working tree checked out at the requested head commit."""
    root = Path(repository).expanduser().resolve()
    actual_head = resolve_commit(root, "HEAD", timeout_seconds=timeout_seconds)
    if actual_head != expected_head:
        raise GitAnalysisError(
            "working tree HEAD must match the requested --head revision; "
            "check out that revision before analysis"
        )
    status = _run_git(
        root,
        ["status", "--porcelain", "--untracked-files=all"],
        timeout_seconds=timeout_seconds,
    )
    if status.strip():
        raise GitAnalysisError(
            "working tree is not clean; commit, stash or remove local changes before analysis"
        )
    ignored_python = _run_git(
        root,
        ["ls-files", "--others", "--ignored", "--exclude-standard", "--", "*.py"],
        timeout_seconds=timeout_seconds,
    )
    if ignored_python.strip():
        raise GitAnalysisError(
            "ignored, untracked Python source files are present; remove them before analysis"
        )


def compare_revisions(
    repository: str | Path,
    base_revision: str,
    head_revision: str,
    *,
    timeout_seconds: float = 30.0,
) -> GitComparison:
    """Resolve two revisions and return their no-external-diff unified patch."""
    root = Path(repository).expanduser().resolve()
    base_sha = resolve_commit(root, base_revision, timeout_seconds=timeout_seconds)
    head_sha = resolve_commit(root, head_revision, timeout_seconds=timeout_seconds)
    diff_text = _run_git(
        root,
        [
            "diff",
            "--no-ext-diff",
            "--no-color",
            "--unified=0",
            "--find-renames",
            base_sha,
            head_sha,
            "--",
        ],
        timeout_seconds=timeout_seconds,
    )
    return GitComparison(
        repository=root,
        base_revision=base_sha,
        head_revision=head_sha,
        diff_text=diff_text,
    )
