"""Dependency-free unified-diff statistics for repository-intelligence baselines."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath


_DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")


@dataclass(frozen=True, slots=True)
class ChangedFile:
    path: str
    old_path: str | None
    additions: int
    deletions: int
    is_binary: bool = False


@dataclass(frozen=True, slots=True)
class ChangeSummary:
    files: tuple[ChangedFile, ...]

    @property
    def changed_file_count(self) -> int:
        return len(self.files)

    @property
    def additions(self) -> int:
        return sum(item.additions for item in self.files)

    @property
    def deletions(self) -> int:
        return sum(item.deletions for item in self.files)

    @property
    def binary_file_count(self) -> int:
        return sum(item.is_binary for item in self.files)

    @property
    def change_size(self) -> int:
        return self.additions + self.deletions

    @property
    def extension_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for item in self.files:
            suffix = PurePosixPath(item.path).suffix.lower() or "<none>"
            counts[suffix] += 1
        return dict(sorted(counts.items()))


def parse_unified_diff(diff_text: str) -> ChangeSummary:
    """Extract per-file additions/deletions for ordinary Git unified diffs.

    This is a statistics parser, not an AST or semantic diff. Quoted Git paths and
    unusual path encodings should be normalized by the caller before this adapter.
    """
    files: list[ChangedFile] = []
    current_path: str | None = None
    old_path: str | None = None
    additions = 0
    deletions = 0
    is_binary = False
    in_hunk = False

    def finish() -> None:
        if current_path is not None:
            files.append(
                ChangedFile(
                    path=current_path,
                    old_path=old_path,
                    additions=additions,
                    deletions=deletions,
                    is_binary=is_binary,
                )
            )

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            finish()
            match = _DIFF_HEADER.match(line)
            if match is None:
                current_path = None
                old_path = None
            else:
                old_path = match.group(1)
                current_path = match.group(2)
            additions = 0
            deletions = 0
            is_binary = False
            in_hunk = False
            continue
        if current_path is None:
            continue
        if not in_hunk and line.startswith("rename from "):
            old_path = line.removeprefix("rename from ")
        elif not in_hunk and line.startswith("rename to "):
            current_path = line.removeprefix("rename to ")
        elif not in_hunk and line.startswith("--- "):
            value = line[4:].strip()
            if value == "/dev/null":
                old_path = None
            elif value.startswith("a/"):
                old_path = value[2:]
        elif not in_hunk and line.startswith("+++ "):
            value = line[4:].strip()
            if value.startswith("b/"):
                current_path = value[2:]
        elif line.startswith("@@"):
            in_hunk = True
        elif line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            is_binary = True
        elif in_hunk and line.startswith("+"):
            additions += 1
        elif in_hunk and line.startswith("-"):
            deletions += 1

    finish()
    return ChangeSummary(files=tuple(files))
