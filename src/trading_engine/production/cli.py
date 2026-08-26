from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from trading_engine.production.artifacts import (
    persist_engine_result,
    verify_experiment_artifacts,
)
from trading_engine.production.config import EngineConfig
from trading_engine.production.pipeline import run_engine


def _read_csv(
    path: str | Path,
    *,
    name: str,
) -> pd.DataFrame:
    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(f"{name} CSV does not exist: {csv_path}")

    if not csv_path.is_file():
        raise ValueError(f"{name} path must point to a file.")

    try:
        frame = pd.read_csv(
            csv_path,
            index_col=0,
            parse_dates=True,
        )
    except (OSError, pd.errors.ParserError) as error:
        raise ValueError(f"could not read {name} CSV.") from error

    if frame.empty:
        raise ValueError(f"{name} CSV cannot be empty.")

    if not frame.index.is_unique:
        raise ValueError(f"{name} CSV index must be unique.")

    if not frame.index.is_monotonic_increasing:
        raise ValueError(f"{name} CSV index must be sorted.")

    return frame


def _load_prices(
    path: str | Path,
) -> pd.Series:
    frame = _read_csv(
        path,
        name="prices",
    )

    if frame.shape[1] != 1:
        raise ValueError("prices CSV must contain exactly one data column.")

    series = frame.iloc[:, 0].copy()
    series.name = str(frame.columns[0])

    return series


def _load_strategy_returns(
    path: str | Path,
) -> pd.DataFrame:
    frame = _read_csv(
        path,
        name="strategy returns",
    )

    if frame.shape[1] < 1:
        raise ValueError("strategy returns CSV must contain at least one strategy.")

    return frame


def _load_benchmark(
    path: str | Path | None,
) -> pd.Series | None:
    if path is None:
        return None

    frame = _read_csv(
        path,
        name="benchmark",
    )

    if frame.shape[1] != 1:
        raise ValueError("benchmark CSV must contain exactly one data column.")

    series = frame.iloc[:, 0].copy()
    series.name = str(frame.columns[0])

    return series


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-engine",
        description=("Production interface for the algorithmic trading engine."),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run a production research experiment.",
    )

    run_parser.add_argument(
        "--prices",
        required=True,
        help="CSV containing the price series.",
    )

    run_parser.add_argument(
        "--strategies",
        required=True,
        help="CSV containing strategy returns.",
    )

    run_parser.add_argument(
        "--benchmark",
        default=None,
        help="Optional benchmark-return CSV.",
    )

    run_parser.add_argument(
        "--output",
        default="artifacts",
        help="Artifact output directory.",
    )

    run_parser.add_argument(
        "--experiment-name",
        default="default",
        help="Human-readable experiment name.",
    )

    run_parser.add_argument(
        "--benchmark-name",
        default="benchmark",
        help="Human-readable benchmark name.",
    )

    run_parser.add_argument(
        "--initial-equity",
        type=float,
        default=1_000_000.0,
        help="Initial portfolio equity.",
    )

    run_parser.add_argument(
        "--periods-per-year",
        type=int,
        default=252,
        help="Annualization periods.",
    )

    run_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing experiment directory.",
    )

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify persisted experiment artifacts.",
    )

    verify_parser.add_argument(
        "path",
        help="Experiment artifact directory.",
    )

    return parser


def _run_command(
    args: argparse.Namespace,
) -> int:
    prices = _load_prices(args.prices)

    strategy_returns = _load_strategy_returns(args.strategies)

    benchmark_returns = _load_benchmark(args.benchmark)

    config = EngineConfig(
        initial_equity=args.initial_equity,
        periods_per_year=args.periods_per_year,
        experiment_name=args.experiment_name,
        benchmark_name=args.benchmark_name,
    )

    result = run_engine(
        prices=prices,
        strategy_returns=strategy_returns,
        benchmark_returns=benchmark_returns,
        config=config,
    )

    destination = persist_engine_result(
        root=args.output,
        result=result,
        overwrite=args.overwrite,
    )

    print(f"Experiment: {result.experiment_name}")
    print(f"Experiment ID: {result.experiment_id}")
    print(f"Observations: {result.observations}")
    print(f"Final equity: {result.final_equity:.6f}")
    print(f"Total return: {result.total_return:.6%}")
    print(f"Artifacts: {destination}")

    return 0


def _verify_command(
    args: argparse.Namespace,
) -> int:
    valid = verify_experiment_artifacts(args.path)

    if valid:
        print(f"Artifact verification passed: {args.path}")
        return 0

    print(
        f"Artifact verification failed: {args.path}",
        file=sys.stderr,
    )

    return 1


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = _build_parser()

    try:
        args = parser.parse_args(argv)

        if args.command == "run":
            return _run_command(args)

        if args.command == "verify":
            return _verify_command(args)

        parser.error("unknown command")
    except (
        FileExistsError,
        FileNotFoundError,
        TypeError,
        ValueError,
    ) as error:
        print(
            f"error: {error}",
            file=sys.stderr,
        )

        return 2

    return 2
