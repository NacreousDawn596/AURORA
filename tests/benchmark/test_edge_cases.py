import csv
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aurora.benchmark.change import parse_unified_diff
from aurora.benchmark.lrts import DatasetIngestionError, load_lrts_dataset
from aurora.benchmark.metrics import fault_recall_at_budget
from aurora.benchmark.replay import replay
from aurora.benchmark.schema import BuildRecord, BuildRun, TestExecution, TestOutcome
from aurora.benchmark.splits import chronological_split
from aurora.benchmark.strategies import order_tests


def _write_metadata(path: Path, *, pr_name: str = "PR-1", timestamp: str = "1700000000") -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["project", "pr_name", "build_id", "stage_id", "build_timestamp"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "project": "kafka",
                "pr_name": pr_name,
                "build_id": "1",
                "stage_id": "0",
                "build_timestamp": timestamp,
            }
        )


def _write_zip(root: Path, csv_content: str, *, pr_name: str = "PR-1") -> None:
    folder = root / "kafka" / f"{pr_name}_build1" / "stage_0"
    folder.mkdir(parents=True)
    with zipfile.ZipFile(folder / "test_class.csv.zip", "w") as archive:
        archive.writestr("test_class.csv", csv_content)


@pytest.mark.parametrize(
    "csv_content",
    [
        "testclass,duration,outcome\nA,-1,0\n",
        "testclass,duration,outcome\nA,nan,0\n",
        "testclass,duration,outcome\nA,1,flaky-ish\n",
        "testclass,duration,outcome\n,1,0\n",
    ],
)
def test_lrts_rejects_invalid_test_rows(tmp_path: Path, csv_content: str) -> None:
    root = tmp_path / "results"
    _write_zip(root, csv_content)
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata)
    with pytest.raises(DatasetIngestionError):
        load_lrts_dataset(metadata, root)


def test_lrts_rejects_corrupt_or_empty_archives(tmp_path: Path) -> None:
    root = tmp_path / "results"
    folder = root / "kafka" / "PR-1_build1" / "stage_0"
    folder.mkdir(parents=True)
    archive_path = folder / "test_class.csv.zip"
    archive_path.write_bytes(b"not a zip")
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata)
    with pytest.raises(DatasetIngestionError, match="invalid ZIP"):
        load_lrts_dataset(metadata, root)

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("readme.txt", "not a CSV")
    with pytest.raises(DatasetIngestionError, match="found 0"):
        load_lrts_dataset(metadata, root)


def test_lrts_permissive_mode_keeps_valid_rows_and_reports_bad_rows(tmp_path: Path) -> None:
    root = tmp_path / "results"
    _write_zip(root, "testclass,duration,outcome\nA,1,0\n")
    metadata = tmp_path / "dataset.csv"
    with metadata.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["project", "pr_name", "build_id", "stage_id", "build_timestamp"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "project": "kafka",
                "pr_name": "PR-1",
                "build_id": "1",
                "stage_id": "0",
                "build_timestamp": "1700000000",
            }
        )
        writer.writerow(
            {
                "project": "kafka",
                "pr_name": "PR-2",
                "build_id": "2",
                "stage_id": "0",
                "build_timestamp": "1700000100",
            }
        )
    result = load_lrts_dataset(metadata, root, strict=False)
    assert len(result.runs) == 1
    assert len(result.skipped_records) == 1


def test_invalid_temporal_fractions_include_nan_and_infinity() -> None:
    runs = [
        BuildRun(
            BuildRecord("p", "pr", str(day), "0", datetime(2024, 1, day, tzinfo=UTC)),
            (TestExecution(f"t{day}", 1, TestOutcome.PASSED),),
        )
        for day in range(1, 5)
    ]
    for invalid in (float("nan"), float("inf")):
        with pytest.raises(ValueError, match="finite"):
            chronological_split(
                runs,
                train_fraction=invalid,
                validation_fraction=0.2,
                test_fraction=0.2,
            )


def test_replay_rejects_duplicate_test_ids_and_nonfinite_budget() -> None:
    item = TestExecution("same", 1, TestOutcome.PASSED)
    with pytest.raises(ValueError, match="unique"):
        replay([item, item], "input_order", budget_seconds=2)
    with pytest.raises(ValueError, match="finite"):
        replay([item], "input_order", budget_seconds=float("nan"))


def test_fault_recall_validates_budget_even_without_fault_labels() -> None:
    with pytest.raises(ValueError, match="finite"):
        fault_recall_at_budget([], set(), float("inf"))


def test_strategy_rejects_unknown_strategy() -> None:
    with pytest.raises(ValueError):
        order_tests([], "does_not_exist")


def test_unified_diff_counts_code_lines_starting_with_multiple_signs() -> None:
    diff = """diff --git a/ops.txt b/ops.txt
--- a/ops.txt
+++ b/ops.txt
@@ -1,2 +1,2 @@
---literal-old
+++literal-new
"""
    result = parse_unified_diff(diff)
    assert result.additions == 1
    assert result.deletions == 1
