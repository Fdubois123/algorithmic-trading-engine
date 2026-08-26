import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _write_market_inputs(
    root: Path,
    *,
    observations: int = 120,
) -> tuple[
    Path,
    Path,
    Path,
]:
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    x = np.arange(
        observations,
        dtype=float,
    )

    prices = pd.DataFrame(
        {"price": (100.0 + 0.2 * x + 2.0 * np.sin(x / 8.0))},
        index=index,
    )

    strategies = pd.DataFrame(
        {
            "trend": (0.0004 + 0.008 * np.sin(x / 10.0)),
            "momentum": (0.0003 + 0.007 * np.cos(x / 12.0)),
            "mean_reversion": (-0.006 * np.sin(x / 6.0)),
            "volatility": (0.004 * np.sin(x / 4.0)),
            "stat_arb": (0.0002 + 0.004 * np.cos(x / 5.0)),
        },
        index=index,
    )

    benchmark = pd.DataFrame(
        {"benchmark": (0.0002 + 0.003 * np.sin(x / 14.0))},
        index=index,
    )

    prices_path = root / "prices.csv"

    strategies_path = root / "strategies.csv"

    benchmark_path = root / "benchmark.csv"

    prices.to_csv(prices_path)

    strategies.to_csv(strategies_path)

    benchmark.to_csv(benchmark_path)

    return (
        prices_path,
        strategies_path,
        benchmark_path,
    )


def _run_cli(
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "trading_engine",
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_help_end_to_end():
    result = _run_cli("--help")

    assert result.returncode == 0

    assert "trading-engine" in result.stdout

    assert "run" in result.stdout

    assert "verify" in result.stdout


def test_cli_run_and_verify_end_to_end(
    tmp_path,
):
    (
        prices_path,
        strategies_path,
        benchmark_path,
    ) = _write_market_inputs(tmp_path)

    output = tmp_path / "artifacts"

    run_result = _run_cli(
        "run",
        "--prices",
        str(prices_path),
        "--strategies",
        str(strategies_path),
        "--benchmark",
        str(benchmark_path),
        "--output",
        str(output),
        "--experiment-name",
        "v1-cli-e2e",
        "--benchmark-name",
        "synthetic",
    )

    assert run_result.returncode == 0

    assert "Experiment: v1-cli-e2e" in run_result.stdout

    assert "Experiment ID:" in run_result.stdout

    assert "Final equity:" in run_result.stdout

    directories = [path for path in output.iterdir() if path.is_dir()]

    assert len(directories) == 1

    experiment_directory = directories[0]

    verify_result = _run_cli(
        "verify",
        str(experiment_directory),
    )

    assert verify_result.returncode == 0

    assert "verification passed" in verify_result.stdout


def test_cli_verify_detects_real_file_tampering(
    tmp_path,
):
    (
        prices_path,
        strategies_path,
        _,
    ) = _write_market_inputs(tmp_path)

    output = tmp_path / "artifacts"

    run_result = _run_cli(
        "run",
        "--prices",
        str(prices_path),
        "--strategies",
        str(strategies_path),
        "--output",
        str(output),
    )

    assert run_result.returncode == 0

    experiment_directory = next(path for path in output.iterdir() if path.is_dir())

    result_path = experiment_directory / "result.json"

    result_path.write_text(
        "{}",
        encoding="utf-8",
    )

    verify_result = _run_cli(
        "verify",
        str(experiment_directory),
    )

    assert verify_result.returncode == 1

    assert "verification failed" in verify_result.stderr


def test_cli_duplicate_run_requires_overwrite(
    tmp_path,
):
    (
        prices_path,
        strategies_path,
        _,
    ) = _write_market_inputs(tmp_path)

    output = tmp_path / "artifacts"

    arguments = (
        "run",
        "--prices",
        str(prices_path),
        "--strategies",
        str(strategies_path),
        "--output",
        str(output),
        "--experiment-name",
        "repeat-test",
    )

    first = _run_cli(*arguments)

    assert first.returncode == 0

    second = _run_cli(*arguments)

    assert second.returncode == 2

    assert "already exists" in second.stderr

    third = _run_cli(
        *arguments,
        "--overwrite",
    )

    assert third.returncode == 0


def test_cli_missing_prices_fails_cleanly(
    tmp_path,
):
    strategies_path = tmp_path / "strategies.csv"

    pd.DataFrame(
        {
            "trend": [
                0.0,
            ]
        }
    ).to_csv(strategies_path)

    result = _run_cli(
        "run",
        "--prices",
        str(tmp_path / "missing.csv"),
        "--strategies",
        str(strategies_path),
    )

    assert result.returncode == 2

    assert "does not exist" in result.stderr


def test_cli_verify_missing_directory_fails_cleanly(
    tmp_path,
):
    result = _run_cli(
        "verify",
        str(tmp_path / "missing"),
    )

    assert result.returncode == 2

    assert "does not exist" in result.stderr
