import csv
import io
import json
import zipfile
from pathlib import Path

import pytest

from aurora.benchmark.cli import main


def _fixture_dataset(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "processed_test_result"
    folder = root / "kafka" / "PR-1_build1" / "stage_0"
    folder.mkdir(parents=True)
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer, fieldnames=["testclass", "duration", "outcome", "last_outcome"]
    )
    writer.writeheader()
    writer.writerows(
        [
            {"testclass": "pkg.Fast", "duration": "1", "outcome": "0", "last_outcome": "0"},
            {"testclass": "pkg.Slow", "duration": "5", "outcome": "1", "last_outcome": "0"},
        ]
    )
    with zipfile.ZipFile(folder / "test_class.csv.zip", "w") as archive:
        archive.writestr("test_class.csv", csv_buffer.getvalue())

    metadata = tmp_path / "dataset.csv"
    with metadata.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "project", "pr_name", "build_id", "stage_id", "build_timestamp",
                "test_suite_duration_s",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "project": "kafka",
                "pr_name": "PR-1",
                "build_id": "1",
                "stage_id": "0",
                "build_timestamp": "1700000000",
                "test_suite_duration_s": "6",
            }
        )
    return metadata, root


def test_inspect_lrts_writes_json_summary(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    metadata, root = _fixture_dataset(tmp_path)
    assert main(
        ["inspect-lrts", "--metadata", str(metadata), "--test-results-root", str(root)]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dataset"] == "LRTS"
    assert payload["build_stage_runs"] == 1
    assert payload["test_executions"] == 2
    assert payload["failed_test_executions"] == 1


def test_replay_lrts_writes_results_and_manifest(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    metadata, root = _fixture_dataset(tmp_path)
    manifest = tmp_path / "runs" / "manifest.json"
    assert main(
        [
            "replay-lrts",
            "--metadata", str(metadata),
            "--test-results-root", str(root),
            "--strategy", "fastest_first",
            "--budget-seconds", "1",
            "--seed", "9",
            "--manifest", str(manifest),
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["strategy"] == "fastest_first"
    assert payload["runs"][0]["executed_test_ids"] == ["pkg.Fast"]
    assert payload["runs"][0]["test_failure_recall"] == 0.0
    assert json.loads(manifest.read_text(encoding="utf-8"))["seed"] == 9


def test_project_filter_without_matches_is_a_cli_error(tmp_path: Path) -> None:
    metadata, root = _fixture_dataset(tmp_path)
    with pytest.raises(SystemExit) as error:
        main(
            [
                "inspect-lrts",
                "--metadata", str(metadata),
                "--test-results-root", str(root),
                "--project", "does-not-exist",
            ]
        )
    assert error.value.code == 2


def test_replay_rejects_negative_budget(tmp_path: Path) -> None:
    metadata, root = _fixture_dataset(tmp_path)
    with pytest.raises(SystemExit) as error:
        main(
            [
                "replay-lrts",
                "--metadata", str(metadata),
                "--test-results-root", str(root),
                "--budget-seconds", "-1",
            ]
        )
    assert error.value.code == 2
