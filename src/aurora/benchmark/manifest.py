"""Reproducibility manifests for benchmark runs."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Compute a streaming SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    schema_version: str
    dataset_name: str
    metadata_path: str
    metadata_sha256: str
    test_results_root: str
    strategy: str
    budget_seconds: float
    seed: int
    code_revision: str | None
    created_at: str

    def __post_init__(self) -> None:
        if not self.dataset_name.strip() or not self.strategy.strip():
            raise ValueError("dataset_name and strategy must not be empty")
        if not math.isfinite(self.budget_seconds) or self.budget_seconds < 0:
            raise ValueError("budget_seconds must be finite and non-negative")
        if len(self.metadata_sha256) != 64:
            raise ValueError("metadata_sha256 must be a 64-character SHA-256 digest")
        try:
            int(self.metadata_sha256, 16)
        except ValueError as exc:
            raise ValueError("metadata_sha256 must be hexadecimal") from exc
        parsed = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("created_at must include a timezone")

    @classmethod
    def create(
        cls,
        *,
        dataset_name: str,
        metadata_path: str | Path,
        test_results_root: str | Path,
        strategy: str,
        budget_seconds: float,
        seed: int,
        code_revision: str | None = None,
        created_at: datetime | None = None,
    ) -> ExperimentManifest:
        timestamp = (created_at or datetime.now(UTC)).astimezone(UTC).isoformat()
        path = Path(metadata_path)
        return cls(
            schema_version="1",
            dataset_name=dataset_name,
            metadata_path=str(path),
            metadata_sha256=sha256_file(path),
            test_results_root=str(Path(test_results_root)),
            strategy=strategy,
            budget_seconds=budget_seconds,
            seed=seed,
            code_revision=code_revision,
            created_at=timestamp,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def write_manifest(manifest: ExperimentManifest, destination: str | Path) -> Path:
    """Write JSON atomically so interrupted runs do not leave a partial manifest."""
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise
    return target
