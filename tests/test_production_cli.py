import json

import numpy as np
import pandas as pd
import pytest

from trading_engine.production.cli import (
    _load_benchmark,
    _load_prices,
    _load_strategy_returns,
    main,
)


def _index(
    observations: int = 80,
) -> pd.DatetimeIndex:
    return pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )


def _write_prices(
    path,
    observations: int = 80,
):
    index = _index(observations)

    frame = pd.DataFrame(
        {
            "price": np.linspace(
                100.0,
                130.0,
                observations,
            )
            + np.sin(np.arange(observations) / 4.0),
        },
        index=index,
    )

    frame.to_csv(path)

    return index


def _write_strategies(
    path,
    index,
):
    x = np.arange(
        len(index),
        dtype=float,
    )

    frame = pd.DataFrame(
        {
            "trend": (np.sin(x / 6.0) * 0.01),
            "momentum": (np.cos(x / 8.0) * 0.01),
            "mean_reversion": (-np.sin(x / 5.0) * 0.008),
            "volatility": (np.sin(x / 3.0) * 0.005),
            "stat_arb": (np.cos(x / 4.0) * 0.006),
        },
        index=index,
    )

    frame.to_csv(path)


def _write_benchmark(
    path,
    index,
):
    frame = pd.DataFrame(
        {"benchmark": (np.sin(np.arange(len(index)) / 9.0) * 0.005)},
        index=index,
    )

    frame.to_csv(path)


def test_load_prices(
    tmp_path,
):
    path = tmp_path / "prices.csv"

    _write_prices(path)

    result = _load_prices(path)

    assert isinstance(
        result,
        pd.Series,
    )

    assert len(result) == 80


def test_load_strategy_returns(
    tmp_path,
):
    price_path = tmp_path / "prices.csv"

    index = _write_prices(price_path)

    path = tmp_path / "strategies.csv"

    _write_strategies(
        path,
        index,
    )

    result = _load_strategy_returns(path)

    assert isinstance(
        result,
        pd.DataFrame,
    )

    assert result.shape == (
        80,
        5,
    )


def test_load_benchmark_none():
    assert _load_benchmark(None) is None


def test_load_benchmark(
    tmp_path,
):
    price_path = tmp_path / "prices.csv"

    index = _write_prices(price_path)

    path = tmp_path / "benchmark.csv"

    _write_benchmark(
        path,
        index,
    )

    result = _load_benchmark(path)

    assert isinstance(
        result,
        pd.Series,
    )

    assert len(result) == 80


def test_missing_csv_returns_error(
    tmp_path,
    capsys,
):
    code = main(
        [
            "run",
            "--prices",
            str(tmp_path / "missing.csv"),
            "--strategies",
            str(tmp_path / "strategies.csv"),
        ]
    )

    captured = capsys.readouterr()

    assert code == 2

    assert "does not exist" in (captured.err)


def test_prices_requires_one_column(
    tmp_path,
):
    path = tmp_path / "prices.csv"

    index = _index(5)

    pd.DataFrame(
        {
            "a": np.ones(5),
            "b": np.ones(5),
        },
        index=index,
    ).to_csv(path)

    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        _load_prices(path)


def test_benchmark_requires_one_column(
    tmp_path,
):
    path = tmp_path / "benchmark.csv"

    index = _index(5)

    pd.DataFrame(
        {
            "a": np.zeros(5),
            "b": np.zeros(5),
        },
        index=index,
    ).to_csv(path)

    with pytest.raises(
        ValueError,
        match="exactly one",
    ):
        _load_benchmark(path)


def test_csv_index_must_be_unique(
    tmp_path,
):
    path = tmp_path / "prices.csv"

    frame = pd.DataFrame(
        {
            "price": [
                100.0,
                101.0,
            ],
        },
        index=[
            "2026-01-01",
            "2026-01-01",
        ],
    )

    frame.to_csv(path)

    with pytest.raises(
        ValueError,
        match="unique",
    ):
        _load_prices(path)


def test_csv_index_must_be_sorted(
    tmp_path,
):
    path = tmp_path / "prices.csv"

    frame = pd.DataFrame(
        {
            "price": [
                101.0,
                100.0,
            ],
        },
        index=[
            "2026-01-02",
            "2026-01-01",
        ],
    )

    frame.to_csv(path)

    with pytest.raises(
        ValueError,
        match="sorted",
    ):
        _load_prices(path)


def test_run_command_creates_artifacts(
    tmp_path,
    capsys,
):
    prices_path = tmp_path / "prices.csv"

    strategies_path = tmp_path / "strategies.csv"

    benchmark_path = tmp_path / "benchmark.csv"

    output_path = tmp_path / "artifacts"

    index = _write_prices(prices_path)

    _write_strategies(
        strategies_path,
        index,
    )

    _write_benchmark(
        benchmark_path,
        index,
    )

    code = main(
        [
            "run",
            "--prices",
            str(prices_path),
            "--strategies",
            str(strategies_path),
            "--benchmark",
            str(benchmark_path),
            "--output",
            str(output_path),
            "--experiment-name",
            "cli-test",
            "--benchmark-name",
            "synthetic",
        ]
    )

    captured = capsys.readouterr()

    assert code == 0

    assert "Experiment: cli-test" in captured.out

    directories = [path for path in output_path.iterdir() if path.is_dir()]

    assert len(directories) == 1

    directory = directories[0]

    assert (directory / "manifest.json").exists()

    assert (directory / "metadata.json").exists()

    assert (directory / "result.json").exists()

    assert (directory / "report.json").exists()

    assert (directory / "summary.json").exists()


def test_verify_command_passes(
    tmp_path,
    capsys,
):
    prices_path = tmp_path / "prices.csv"

    strategies_path = tmp_path / "strategies.csv"

    output_path = tmp_path / "artifacts"

    index = _write_prices(prices_path)

    _write_strategies(
        strategies_path,
        index,
    )

    run_code = main(
        [
            "run",
            "--prices",
            str(prices_path),
            "--strategies",
            str(strategies_path),
            "--output",
            str(output_path),
        ]
    )

    assert run_code == 0

    capsys.readouterr()

    directory = next(output_path.iterdir())

    verify_code = main(
        [
            "verify",
            str(directory),
        ]
    )

    captured = capsys.readouterr()

    assert verify_code == 0

    assert "verification passed" in captured.out


def test_verify_command_detects_tampering(
    tmp_path,
    capsys,
):
    prices_path = tmp_path / "prices.csv"

    strategies_path = tmp_path / "strategies.csv"

    output_path = tmp_path / "artifacts"

    index = _write_prices(prices_path)

    _write_strategies(
        strategies_path,
        index,
    )

    run_code = main(
        [
            "run",
            "--prices",
            str(prices_path),
            "--strategies",
            str(strategies_path),
            "--output",
            str(output_path),
        ]
    )

    assert run_code == 0

    capsys.readouterr()

    directory = next(output_path.iterdir())

    (directory / "result.json").write_text(
        json.dumps({}),
        encoding="utf-8",
    )

    verify_code = main(
        [
            "verify",
            str(directory),
        ]
    )

    captured = capsys.readouterr()

    assert verify_code == 1

    assert "verification failed" in captured.err


def test_run_existing_experiment_fails_without_overwrite(
    tmp_path,
    capsys,
):
    prices_path = tmp_path / "prices.csv"

    strategies_path = tmp_path / "strategies.csv"

    output_path = tmp_path / "artifacts"

    index = _write_prices(prices_path)

    _write_strategies(
        strategies_path,
        index,
    )

    arguments = [
        "run",
        "--prices",
        str(prices_path),
        "--strategies",
        str(strategies_path),
        "--output",
        str(output_path),
    ]

    assert main(arguments) == 0

    capsys.readouterr()

    second = main(arguments)

    captured = capsys.readouterr()

    assert second == 2

    assert "already exists" in captured.err


def test_run_overwrite_succeeds(
    tmp_path,
):
    prices_path = tmp_path / "prices.csv"

    strategies_path = tmp_path / "strategies.csv"

    output_path = tmp_path / "artifacts"

    index = _write_prices(prices_path)

    _write_strategies(
        strategies_path,
        index,
    )

    arguments = [
        "run",
        "--prices",
        str(prices_path),
        "--strategies",
        str(strategies_path),
        "--output",
        str(output_path),
    ]

    assert main(arguments) == 0

    assert (
        main(
            [
                *arguments,
                "--overwrite",
            ]
        )
        == 0
    )
