import csv
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aurora.benchmark.lrts import (
    DatasetIngestionError,
    enrich_history_features,
    load_lrts_dataset,
    normalize_outcome,
    parse_timestamp,
)
from aurora.benchmark.schema import BuildRecord, BuildRun, TestExecution, TestOutcome


def _write_archive(
    root: Path,
    *,
    project: str = "kafka",
    pr_name: str = "PR-1",
    build_id: str = "1",
    stage_id: str = "0",
    rows: list[dict[str, str]] | None = None,
    csv_name: str = "test_class.csv",
) -> Path:
    folder = root / project / f"{pr_name}_build{build_id}" / f"stage_{stage_id}"
    folder.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["testclass", "duration", "outcome", "last_outcome"],
    )
    writer.writeheader()
    default_rows = [
        {
            "testclass": "pkg.TestA",
            "duration": "1.5",
            "outcome": "1",
            "last_outcome": "0",
        }
    ]
    writer.writerows(rows if rows is not None else default_rows)
    archive_path = folder / "test_class.csv.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(csv_name, buffer.getvalue())
    return archive_path


def _write_metadata(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "project",
        "pr_name",
        "build_id",
        "stage_id",
        "build_timestamp",
        "test_suite_duration_s",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _metadata_row(build_id: str = "1", timestamp: str = "1700000000") -> dict[str, str]:
    return {
        "project": "kafka",
        "pr_name": "PR-1",
        "build_id": build_id,
        "stage_id": "0",
        "build_timestamp": timestamp,
        "test_suite_duration_s": "1.5",
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1700000000", datetime.fromtimestamp(1700000000, tz=UTC)),
        ("1700000000000", datetime.fromtimestamp(1700000000, tz=UTC)),
        ("2024-01-01T00:00:00Z", datetime(2024, 1, 1, tzinfo=UTC)),
        ("2024-01-01T01:00:00+01:00", datetime(2024, 1, 1, tzinfo=UTC)),
        ("2024-01-01 00:00:00", datetime(2024, 1, 1, tzinfo=UTC)),
    ],
)
def test_parse_timestamp_normalizes_to_utc(raw: str, expected: datetime) -> None:
    assert parse_timestamp(raw) == expected


@pytest.mark.parametrize("raw", ["", "nan", "inf", "not-a-date", "1e100"])
def test_parse_timestamp_rejects_invalid_values(raw: str) -> None:
    with pytest.raises(DatasetIngestionError):
        parse_timestamp(raw)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0", TestOutcome.PASSED),
        ("PASSED", TestOutcome.PASSED),
        ("success", TestOutcome.PASSED),
        ("1.0", TestOutcome.FAILED),
        ("FAILURE", TestOutcome.FAILED),
        ("skip", TestOutcome.SKIPPED),
        ("unknown", TestOutcome.UNKNOWN),
    ],
)
def test_normalize_outcome_aliases(raw: str, expected: TestOutcome) -> None:
    assert normalize_outcome(raw) is expected


def test_normalize_outcome_handles_empty_and_invalid() -> None:
    assert normalize_outcome("", allow_empty=True) is None
    with pytest.raises(DatasetIngestionError, match="empty"):
        normalize_outcome("")
    with pytest.raises(DatasetIngestionError, match="unsupported"):
        normalize_outcome("flaky-ish")


def test_load_lrts_dataset_reads_metadata_and_nested_zip(tmp_path: Path) -> None:
    root = tmp_path / "processed_test_result"
    _write_archive(root)
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata, [_metadata_row()])

    loaded = load_lrts_dataset(metadata, root)

    assert len(loaded.runs) == 1
    run = loaded.runs[0]
    assert run.build.record_id == "kafka/PR-1/1/0"
    assert run.build.timestamp == datetime.fromtimestamp(1700000000, tz=UTC)
    assert run.build.test_suite_duration_seconds == 1.5
    assert run.tests[0].test_id == "pkg.TestA"
    assert run.tests[0].duration_seconds == 1.5
    assert run.tests[0].outcome is TestOutcome.FAILED
    assert run.tests[0].previous_outcome is TestOutcome.PASSED


def test_load_lrts_requires_metadata_columns(tmp_path: Path) -> None:
    metadata = tmp_path / "bad.csv"
    metadata.write_text("project,build_id\nkafka,1\n", encoding="utf-8")
    with pytest.raises(DatasetIngestionError, match="missing required columns"):
        load_lrts_dataset(metadata, tmp_path)


def test_load_lrts_missing_archive_is_strict_or_reported(tmp_path: Path) -> None:
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata, [_metadata_row()])
    with pytest.raises(DatasetIngestionError, match="not found"):
        load_lrts_dataset(metadata, tmp_path / "missing")

    result = load_lrts_dataset(metadata, tmp_path / "missing", strict=False)
    assert result.runs == ()
    assert len(result.skipped_records) == 1
    assert "not found" in result.skipped_records[0]


def test_load_lrts_rejects_path_traversal(tmp_path: Path) -> None:
    metadata = tmp_path / "dataset.csv"
    row = _metadata_row()
    row["project"] = "../outside"
    _write_metadata(metadata, [row])
    with pytest.raises(DatasetIngestionError, match="unsafe"):
        load_lrts_dataset(metadata, tmp_path)


def test_load_lrts_rejects_duplicate_build_stage_rows(tmp_path: Path) -> None:
    root = tmp_path / "results"
    _write_archive(root)
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata, [_metadata_row(), _metadata_row()])
    with pytest.raises(DatasetIngestionError, match="duplicate"):
        load_lrts_dataset(metadata, root)


def test_load_lrts_rejects_missing_test_columns(tmp_path: Path) -> None:
    root = tmp_path / "results"
    folder = root / "kafka" / "PR-1_build1" / "stage_0"
    folder.mkdir(parents=True)
    archive_path = folder / "test_class.csv.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("test_class.csv", "name,time,status\nA,1,pass\n")
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata, [_metadata_row()])
    with pytest.raises(DatasetIngestionError, match="missing required columns"):
        load_lrts_dataset(metadata, root)


def test_load_lrts_rejects_duplicate_test_ids(tmp_path: Path) -> None:
    root = tmp_path / "results"
    duplicate_rows = [
        {"testclass": "same", "duration": "1", "outcome": "0", "last_outcome": "0"},
        {"testclass": "same", "duration": "2", "outcome": "1", "last_outcome": "0"},
    ]
    _write_archive(root, rows=duplicate_rows)
    metadata = tmp_path / "dataset.csv"
    _write_metadata(metadata, [_metadata_row()])
    with pytest.raises(DatasetIngestionError, match="duplicate"):
        load_lrts_dataset(metadata, root)


def _make_run(build_id: str, day: int, outcome: TestOutcome) -> BuildRun:
    record = BuildRecord(
        "project",
        "PR-1",
        build_id,
        "0",
        datetime(2024, 1, day, tzinfo=UTC),
    )
    return BuildRun(record, (TestExecution("pkg.Test", 1, outcome),))


def test_history_features_only_use_prior_runs() -> None:
    runs = (
        _make_run("1", 1, TestOutcome.PASSED),
        _make_run("2", 2, TestOutcome.FAILED),
        _make_run("3", 3, TestOutcome.PASSED),
    )
    enriched = enrich_history_features(runs)
    assert enriched[0].tests[0].previous_outcome is None
    assert enriched[0].tests[0].last_failure_age_builds is None
    assert enriched[1].tests[0].previous_outcome is TestOutcome.PASSED
    assert enriched[1].tests[0].last_failure_age_builds is None
    assert enriched[2].tests[0].previous_outcome is TestOutcome.FAILED
    assert enriched[2].tests[0].last_failure_age_builds == 1


def test_history_features_treat_equal_timestamps_as_simultaneous() -> None:
    first = _make_run("1", 1, TestOutcome.FAILED)
    same_time = _make_run("2", 1, TestOutcome.PASSED)
    later = _make_run("3", 2, TestOutcome.PASSED)
    enriched = enrich_history_features((first, same_time, later))
    assert enriched[0].tests[0].last_failure_age_builds is None
    assert enriched[1].tests[0].last_failure_age_builds is None
    assert enriched[2].tests[0].last_failure_age_builds == 1
    assert enriched[2].tests[0].previous_outcome is TestOutcome.UNKNOWN
