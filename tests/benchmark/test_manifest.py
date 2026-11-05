import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aurora.benchmark.manifest import ExperimentManifest, sha256_file, write_manifest


def test_sha256_file_matches_standard_digest(tmp_path: Path) -> None:
    source = tmp_path / "metadata.csv"
    source.write_bytes(b"a,b\n1,2\n")
    assert sha256_file(source) == hashlib.sha256(b"a,b\n1,2\n").hexdigest()


def test_manifest_creation_records_checksum_and_reproducibility_fields(tmp_path: Path) -> None:
    metadata = tmp_path / "dataset.csv"
    metadata.write_text("project,build_id\nkafka,1\n", encoding="utf-8")
    manifest = ExperimentManifest.create(
        dataset_name="LRTS",
        metadata_path=metadata,
        test_results_root=tmp_path / "results",
        strategy="fastest_first",
        budget_seconds=120,
        seed=42,
        code_revision="abc123",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    assert manifest.metadata_sha256 == sha256_file(metadata)
    assert manifest.seed == 42
    assert manifest.code_revision == "abc123"
    assert manifest.created_at == "2024-01-01T00:00:00+00:00"


@pytest.mark.parametrize("budget", [-1.0, float("nan"), float("inf")])
def test_manifest_rejects_invalid_budget(budget: float) -> None:
    with pytest.raises(ValueError, match="budget_seconds"):
        ExperimentManifest(
            "1", "LRTS", "dataset.csv", "0" * 64, "results",
            "fastest_first", budget, 1, None, "2024-01-01T00:00:00+00:00",
        )


def test_manifest_rejects_invalid_digest_and_timezone() -> None:
    with pytest.raises(ValueError, match="hexadecimal"):
        ExperimentManifest(
            "1", "LRTS", "dataset.csv", "x" * 64, "results",
            "fastest_first", 1, 1, None, "2024-01-01T00:00:00+00:00",
        )
    with pytest.raises(ValueError, match="timezone"):
        ExperimentManifest(
            "1", "LRTS", "dataset.csv", "0" * 64, "results",
            "fastest_first", 1, 1, None, "2024-01-01T00:00:00",
        )


def test_write_manifest_is_valid_json_and_creates_parent(tmp_path: Path) -> None:
    metadata = tmp_path / "data.csv"
    metadata.write_text("x\n", encoding="utf-8")
    manifest = ExperimentManifest.create(
        dataset_name="test",
        metadata_path=metadata,
        test_results_root=tmp_path,
        strategy="random",
        budget_seconds=3,
        seed=4,
    )
    destination = tmp_path / "nested" / "manifest.json"
    assert write_manifest(manifest, destination) == destination
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["dataset_name"] == "test"
    assert payload["seed"] == 4
    assert not list(destination.parent.glob("*.tmp"))
