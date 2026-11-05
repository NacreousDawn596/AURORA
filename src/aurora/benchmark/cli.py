"""Command-line interface for LRTS inspection and baseline replay."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from aurora.benchmark.lrts import enrich_history_features, load_lrts_dataset
from aurora.benchmark.manifest import ExperimentManifest, write_manifest
from aurora.benchmark.replay import replay
from aurora.benchmark.schema import BuildRun
from aurora.benchmark.strategies import Strategy


def _add_dataset_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--metadata", required=True, help="Path to LRTS metadata/dataset.csv")
    parser.add_argument(
        "--test-results-root",
        required=True,
        help="Path to the processed_test_result directory",
    )
    parser.add_argument("--project", help="Optional project slug filter")
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip malformed/missing rows and report them instead of failing",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aurora-benchmark")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect-lrts", help="Validate and summarize an LRTS dataset")
    _add_dataset_arguments(inspect)
    inspect.add_argument("--output", default="-", help="JSON output path, or - for stdout")

    run = commands.add_parser("replay-lrts", help="Replay baseline strategies under a time budget")
    _add_dataset_arguments(run)
    run.add_argument(
        "--strategy",
        choices=[item.value for item in Strategy],
        default=Strategy.RECENT_FAILURE_FIRST.value,
    )
    run.add_argument("--budget-seconds", type=float, required=True)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--output", default="-", help="JSON output path, or - for stdout")
    run.add_argument("--manifest", help="Optional path for a reproducibility manifest")
    return parser


def _load_runs(
    args: argparse.Namespace,
) -> tuple[tuple[BuildRun, ...], tuple[str, ...]]:
    loaded = load_lrts_dataset(
        args.metadata,
        args.test_results_root,
        strict=not args.skip_missing,
    )
    runs = enrich_history_features(loaded.runs)
    if args.project:
        runs = tuple(item for item in runs if item.build.project == args.project)
    if not runs:
        raise ValueError("no build-stage records remain after filtering")
    return runs, loaded.skipped_records


def _write_json(payload: object, destination: str) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if destination == "-":
        sys.stdout.write(rendered)
        return
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        runs, skipped = _load_runs(args)
        if args.command == "inspect-lrts":
            projects = sorted({item.build.project for item in runs})
            _write_json(
                {
                    "dataset": "LRTS",
                    "granularity": "test class within build stage",
                    "build_stage_runs": len(runs),
                    "projects": projects,
                    "test_executions": sum(item.test_count for item in runs),
                    "failed_test_executions": sum(item.failed_test_count for item in runs),
                    "skipped_metadata_records": list(skipped),
                },
                args.output,
            )
            return 0

        strategy = Strategy(args.strategy)
        results = [
            replay(
                run.tests,
                strategy,
                budget_seconds=args.budget_seconds,
                seed=args.seed + index,
            )
            for index, run in enumerate(runs)
        ]
        rows = []
        for run, result in zip(runs, results, strict=True):
            rows.append(
                {
                    "record_id": run.build.record_id,
                    "timestamp": run.build.timestamp.isoformat(),
                    "test_count": run.test_count,
                    "observed_failed_tests": result.observed_failed_tests,
                    "executed_test_count": len(result.executed_test_ids),
                    "consumed_seconds": result.consumed_seconds,
                    "test_failure_recall": result.test_failure_recall,
                    "time_to_first_failure_seconds": result.time_to_first_failure_seconds,
                    "executed_test_ids": list(result.executed_test_ids),
                }
            )
        recall_values = [
            item.test_failure_recall for item in results if item.test_failure_recall is not None
        ]
        _write_json(
            {
                "dataset": "LRTS",
                "strategy": strategy.value,
                "budget_seconds": args.budget_seconds,
                "seed": args.seed,
                "build_stage_runs": len(results),
                "mean_test_failure_recall": (
                    sum(recall_values) / len(recall_values) if recall_values else None
                ),
                "runs": rows,
                "skipped_metadata_records": list(skipped),
                "interpretation": (
                    "Test-failure recall is an observed failing-test proxy, not causal "
                    "regression-fault recall."
                ),
            },
            args.output,
        )
        if args.manifest:
            manifest = ExperimentManifest.create(
                dataset_name="LRTS",
                metadata_path=args.metadata,
                test_results_root=args.test_results_root,
                strategy=strategy.value,
                budget_seconds=args.budget_seconds,
                seed=args.seed,
                code_revision=os.getenv("GITHUB_SHA") or os.getenv("AURORA_REVISION"),
            )
            write_manifest(manifest, args.manifest)
        return 0
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
