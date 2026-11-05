"""Reader for the public LRTS processed dataset layout.

The adapter reads metadata/dataset.csv and the per-stage
processed_test_result/<project>/<pr>_build<build>/stage_<stage>/test_class.csv.zip files.
It uses the source artifact's test-class granularity and does not infer causal bug labels.
"""

from __future__ import annotations

import csv
import io
import math
import zipfile
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from aurora.benchmark.schema import BuildRecord, BuildRun, TestExecution, TestOutcome


class DatasetIngestionError(ValueError):
    """Raised when a dataset record cannot be normalized safely."""


@dataclass(frozen=True, slots=True)
class DatasetLoadResult:
    runs: tuple[BuildRun, ...]
    skipped_records: tuple[str, ...] = ()


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp or Unix seconds/milliseconds into UTC."""
    raw = value.strip()
    if not raw:
        raise DatasetIngestionError("build_timestamp is empty")
    try:
        numeric = float(raw)
    except ValueError:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DatasetIngestionError(f"invalid build_timestamp: {value!r}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    if not math.isfinite(numeric):
        raise DatasetIngestionError(f"invalid build_timestamp: {value!r}")
    if abs(numeric) >= 100_000_000_000:
        numeric /= 1000.0
    try:
        return datetime.fromtimestamp(numeric, tz=UTC)
    except (OverflowError, OSError, ValueError) as exc:
        raise DatasetIngestionError(f"timestamp out of range: {value!r}") from exc


def normalize_outcome(value: str | None, *, allow_empty: bool = False) -> TestOutcome | None:
    if value is None or not value.strip():
        if allow_empty:
            return None
        raise DatasetIngestionError("test outcome is empty")
    normalized = value.strip().casefold()
    aliases = {
        "0": TestOutcome.PASSED,
        "0.0": TestOutcome.PASSED,
        "pass": TestOutcome.PASSED,
        "passed": TestOutcome.PASSED,
        "success": TestOutcome.PASSED,
        "1": TestOutcome.FAILED,
        "1.0": TestOutcome.FAILED,
        "fail": TestOutcome.FAILED,
        "failed": TestOutcome.FAILED,
        "failure": TestOutcome.FAILED,
        "skipped": TestOutcome.SKIPPED,
        "skip": TestOutcome.SKIPPED,
        "not executed": TestOutcome.SKIPPED,
        "unknown": TestOutcome.UNKNOWN,
    }
    try:
        return aliases[normalized]
    except KeyError as exc:
        raise DatasetIngestionError(f"unsupported test outcome: {value!r}") from exc


def _safe_component(value: str, field_name: str) -> str:
    component = value.strip()
    if not component or component in {".", ".."} or "/" in component or "\\" in component:
        raise DatasetIngestionError(f"unsafe {field_name} path component: {value!r}")
    return component


def _parse_nonnegative_float(value: str | None, field_name: str) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise DatasetIngestionError(f"invalid {field_name}: {value!r}") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise DatasetIngestionError(f"{field_name} must be finite and non-negative")
    return parsed


def _read_test_class_zip(path: Path) -> tuple[TestExecution, ...]:
    if not path.is_file():
        raise DatasetIngestionError(f"test result archive not found: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            csv_names = [name for name in archive.namelist() if name.casefold().endswith(".csv")]
            preferred = [name for name in csv_names if Path(name).name == "test_class.csv"]
            if len(preferred) == 1:
                csv_name = preferred[0]
            elif len(csv_names) == 1:
                csv_name = csv_names[0]
            else:
                raise DatasetIngestionError(
                    f"expected one test-class CSV in {path.name}, found {len(csv_names)}"
                )
            with archive.open(csv_name) as binary_file:
                text_file = io.TextIOWrapper(binary_file, encoding="utf-8-sig", newline="")
                return _parse_test_rows(text_file, archive_path=path)
    except zipfile.BadZipFile as exc:
        raise DatasetIngestionError(f"invalid ZIP archive: {path}") from exc


def _parse_test_rows(stream: TextIO, *, archive_path: Path) -> tuple[TestExecution, ...]:
    reader = csv.DictReader(stream)
    if reader.fieldnames is None:
        raise DatasetIngestionError(f"empty CSV in {archive_path}")
    normalized_headers = {name.strip().casefold() for name in reader.fieldnames if name}
    required = {"testclass", "duration", "outcome"}
    missing = required - normalized_headers
    if missing:
        raise DatasetIngestionError(
            f"{archive_path} is missing required columns: {', '.join(sorted(missing))}"
        )

    header_map = {name.strip().casefold(): name for name in reader.fieldnames if name}
    tests: list[TestExecution] = []
    for row_number, row in enumerate(reader, start=2):
        test_id = (row.get(header_map["testclass"]) or "").strip()
        if not test_id:
            raise DatasetIngestionError(f"empty testclass at {archive_path}:{row_number}")
        duration = _parse_nonnegative_float(row.get(header_map["duration"]), "duration")
        outcome = normalize_outcome(row.get(header_map["outcome"]))
        previous = normalize_outcome(
            row.get(header_map.get("last_outcome", "")), allow_empty=True
        )
        assert duration is not None and outcome is not None
        try:
            tests.append(
                TestExecution(
                    test_id=test_id,
                    duration_seconds=duration,
                    outcome=outcome,
                    previous_outcome=previous,
                )
            )
        except ValueError as exc:
            raise DatasetIngestionError(
                f"invalid test row at {archive_path}:{row_number}: {exc}"
            ) from exc
    if not tests:
        raise DatasetIngestionError(f"no test executions found in {archive_path}")
    return tuple(tests)


def _lrts_archive_path(root: Path, row: dict[str, str]) -> Path:
    components = [
        _safe_component(row["project"], "project"),
        f"{_safe_component(row['pr_name'], 'pr_name')}_build"
        f"{_safe_component(row['build_id'], 'build_id')}",
        f"stage_{_safe_component(row['stage_id'], 'stage_id')}",
        "test_class.csv.zip",
    ]
    path = root.joinpath(*components).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise DatasetIngestionError("test result path escapes the supplied dataset root") from exc
    return path


def load_lrts_dataset(
    metadata_csv: str | Path,
    processed_results_root: str | Path,
    *,
    strict: bool = True,
) -> DatasetLoadResult:
    """Load normalized LRTS build-stage records and test-class executions.

    In strict mode, any malformed or missing stage artifact fails the load. In
    permissive mode, invalid rows are reported in skipped_records; they are never
    silently discarded.
    """
    metadata_path = Path(metadata_csv)
    results_root = Path(processed_results_root)
    if not metadata_path.is_file():
        raise FileNotFoundError(metadata_path)
    required = {"project", "pr_name", "build_id", "stage_id", "build_timestamp"}
    runs: list[BuildRun] = []
    skipped: list[str] = []
    seen: set[str] = set()

    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DatasetIngestionError("metadata CSV is empty")
        headers = {name.strip() for name in reader.fieldnames if name}
        missing = required - headers
        if missing:
            raise DatasetIngestionError(
                f"metadata CSV is missing required columns: {', '.join(sorted(missing))}"
            )
        for line_number, raw_row in enumerate(reader, start=2):
            row = {key.strip(): (value or "").strip() for key, value in raw_row.items() if key}
            try:
                project = _safe_component(row["project"], "project")
                pr_name = _safe_component(row["pr_name"], "pr_name")
                build_id = _safe_component(row["build_id"], "build_id")
                stage_id = _safe_component(row["stage_id"], "stage_id")
                timestamp = parse_timestamp(row["build_timestamp"])
                duration = _parse_nonnegative_float(
                    row.get("test_suite_duration_s"), "test_suite_duration_s"
                )
                record = BuildRecord(
                    project=project,
                    pr_name=pr_name,
                    build_id=build_id,
                    stage_id=stage_id,
                    timestamp=timestamp,
                    test_suite_duration_seconds=duration,
                )
                if record.record_id in seen:
                    raise DatasetIngestionError(f"duplicate build-stage record: {record.record_id}")
                archive_path = _lrts_archive_path(results_root, row)
                tests = _read_test_class_zip(archive_path)
                runs.append(BuildRun(build=record, tests=tests))
                seen.add(record.record_id)
            except (KeyError, ValueError, OSError, csv.Error) as exc:
                message = f"metadata line {line_number}: {exc}"
                if strict:
                    if isinstance(exc, DatasetIngestionError):
                        raise
                    raise DatasetIngestionError(message) from exc
                skipped.append(message)

    if not runs and not skipped:
        raise DatasetIngestionError("metadata CSV contains no build-stage records")
    return DatasetLoadResult(runs=tuple(sorted(
        runs, key=lambda item: (
            item.build.project, item.build.stage_id, item.build.timestamp, item.build.build_id
        )
    )), skipped_records=tuple(skipped))


def enrich_history_features(runs: tuple[BuildRun, ...]) -> tuple[BuildRun, ...]:
    """Add prior-outcome and last-failure-age features without using current outcomes.

    Age is measured in distinct observed timestamp buckets for a (project, stage)
    pair. Records sharing a timestamp are treated as simultaneous and update history
    only after the whole bucket has been enriched.
    """
    grouped: dict[tuple[str, str, datetime], list[BuildRun]] = {}
    for run in runs:
        key = (run.build.project, run.build.stage_id, run.build.timestamp)
        grouped.setdefault(key, []).append(run)

    history: dict[tuple[str, str, str], tuple[TestOutcome, int | None]] = {}
    bucket_counts: dict[tuple[str, str], int] = {}
    output: list[BuildRun] = []

    for key in sorted(grouped):
        project, stage, _timestamp = key
        group = grouped[key]
        history_index = bucket_counts.get((project, stage), 0) + 1
        bucket_counts[(project, stage)] = history_index
        pending_updates: dict[tuple[str, str, str], list[TestOutcome]] = {}
        for run in sorted(group, key=lambda item: item.build.record_id):
            enriched: list[TestExecution] = []
            for test in run.tests:
                test_key = (project, stage, test.test_id)
                previous_state = history.get(test_key)
                previous_outcome = test.previous_outcome
                last_failure_index: int | None = None
                if previous_state is not None:
                    previous_outcome_from_history, last_failure_index = previous_state
                    if previous_outcome is None:
                        previous_outcome = previous_outcome_from_history
                age = (
                    history_index - last_failure_index
                    if last_failure_index is not None
                    else None
                )
                enriched.append(
                    replace(
                        test,
                        previous_outcome=previous_outcome,
                        last_failure_age_builds=age,
                    )
                )
                pending_updates.setdefault(test_key, []).append(test.outcome)
            output.append(replace(run, tests=tuple(enriched)))

        for test_key, outcomes in pending_updates.items():
            known = {value for value in outcomes if value in {TestOutcome.PASSED, TestOutcome.FAILED}}
            if len(known) == 1:
                current = next(iter(known))
                prior_failure = history.get(test_key, (TestOutcome.UNKNOWN, None))[1]
                last_failure = history_index if current is TestOutcome.FAILED else prior_failure
                history[test_key] = (current, last_failure)
            elif len(known) > 1:
                # Conflicting same-time observations are not ordered arbitrarily.
                history[test_key] = (TestOutcome.UNKNOWN, history.get(test_key, (TestOutcome.UNKNOWN, None))[1])

    return tuple(sorted(
        output, key=lambda item: (
            item.build.project, item.build.stage_id, item.build.timestamp, item.build.build_id
        )
    ))
