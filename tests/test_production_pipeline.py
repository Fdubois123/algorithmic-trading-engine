import numpy as np
import pandas as pd
import pytest

from trading_engine.production import (
    EngineConfig,
    EngineResult,
    run_engine,
)
from trading_engine.research import (
    ResearchConfig,
)


def prices(
    observations: int = 120,
) -> pd.Series:
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    values = np.linspace(
        100.0,
        150.0,
        observations,
    ) + 2.0 * np.sin(np.arange(observations) / 5.0)

    return pd.Series(
        values,
        index=index,
        dtype=float,
    )


def strategy_returns(
    index: pd.Index,
) -> pd.DataFrame:
    x = np.arange(
        len(index),
        dtype=float,
    )

    return pd.DataFrame(
        {
            "trend": (np.sin(x / 8.0) * 0.01),
            "momentum": (np.cos(x / 10.0) * 0.01),
            "mean_reversion": (-np.sin(x / 6.0) * 0.008),
            "volatility": (np.sin(x / 3.0) * 0.005),
            "stat_arb": (np.cos(x / 4.0) * 0.006),
        },
        index=index,
    )


def benchmark_returns(
    index: pd.Index,
) -> pd.Series:
    values = np.sin(np.arange(len(index)) / 9.0) * 0.005

    return pd.Series(
        values,
        index=index,
        dtype=float,
    )


def engine_config() -> EngineConfig:
    return EngineConfig(
        research=ResearchConfig(
            volatility_window=10,
            trend_window=20,
            momentum_lookback=10,
            transaction_cost_bps=5.0,
        ),
        benchmark_name="synthetic",
        experiment_name="phase12",
    )


def test_run_engine():
    price_data = prices()

    result = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=engine_config(),
    )

    assert isinstance(
        result,
        EngineResult,
    )

    assert result.observations == len(price_data)

    assert np.isfinite(result.final_equity)


def test_run_engine_with_benchmark():
    price_data = prices()

    result = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        benchmark_returns=benchmark_returns(price_data.index),
        config=engine_config(),
    )

    assert result.summary.benchmark is not None


def test_run_engine_without_config():
    price_data = prices()

    result = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
    )

    assert isinstance(
        result,
        EngineResult,
    )


def test_result_contains_report():
    price_data = prices()

    result = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=engine_config(),
    )

    assert not result.report.overview.empty


def test_result_contains_metadata():
    price_data = prices()

    result = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=engine_config(),
    )

    assert len(result.experiment_id) == 64


def test_metadata_is_deterministic():
    price_data = prices()

    first = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=engine_config(),
    )

    second = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=engine_config(),
    )

    assert first.experiment_id == second.experiment_id


def test_first_applied_weights_are_zero():
    price_data = prices()

    result = run_engine(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=engine_config(),
    )

    assert np.allclose(
        result.research.applied_weights.iloc[0].to_numpy(),
        0.0,
    )


def test_prices_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        run_engine(
            prices=[],
            strategy_returns=pd.DataFrame(),
        )


def test_empty_prices_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        run_engine(
            prices=pd.Series(dtype=float),
            strategy_returns=pd.DataFrame(),
        )


def test_non_numeric_prices_rejected():
    values = pd.Series(
        [
            "a",
            "b",
        ]
    )

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        run_engine(
            prices=values,
            strategy_returns=pd.DataFrame(),
        )


def test_non_finite_prices_rejected():
    values = pd.Series(
        [
            100.0,
            np.inf,
        ]
    )

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        run_engine(
            prices=values,
            strategy_returns=pd.DataFrame(),
        )


def test_non_positive_prices_rejected():
    values = pd.Series(
        [
            100.0,
            0.0,
        ]
    )

    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        run_engine(
            prices=values,
            strategy_returns=pd.DataFrame(),
        )


def test_duplicate_price_index_rejected():
    values = pd.Series(
        [
            100.0,
            101.0,
        ],
        index=[
            0,
            0,
        ],
    )

    with pytest.raises(
        ValueError,
        match="unique",
    ):
        run_engine(
            prices=values,
            strategy_returns=pd.DataFrame(),
        )


def test_unsorted_price_index_rejected():
    values = pd.Series(
        [
            100.0,
            101.0,
        ],
        index=[
            2,
            1,
        ],
    )

    with pytest.raises(
        ValueError,
        match="sorted",
    ):
        run_engine(
            prices=values,
            strategy_returns=pd.DataFrame(),
        )


def test_invalid_engine_config_rejected():
    price_data = prices()

    with pytest.raises(
        TypeError,
        match="EngineConfig",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=strategy_returns(price_data.index),
            config="bad",
        )


def test_strategy_returns_requires_dataframe():
    price_data = prices()

    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=[],
            config=engine_config(),
        )


def test_strategy_return_index_must_match():
    price_data = prices()

    returns = strategy_returns(price_data.index).reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="index",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=returns,
            config=engine_config(),
        )


def test_duplicate_strategy_columns_rejected():
    price_data = prices()

    returns = strategy_returns(price_data.index)

    returns.columns = [
        "trend",
        "trend",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="unique",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=returns,
            config=engine_config(),
        )


def test_empty_strategy_name_rejected():
    price_data = prices()

    returns = strategy_returns(price_data.index)

    returns.columns = [
        "",
        "momentum",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="non-empty",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=returns,
            config=engine_config(),
        )


def test_non_numeric_strategy_returns_rejected():
    price_data = prices()

    returns = strategy_returns(price_data.index).astype(object)

    returns.iloc[
        0,
        0,
    ] = "bad"

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=returns,
            config=engine_config(),
        )


def test_non_finite_strategy_returns_rejected():
    price_data = prices()

    returns = strategy_returns(price_data.index)

    returns.iloc[
        0,
        0,
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=returns,
            config=engine_config(),
        )


def test_benchmark_requires_series():
    price_data = prices()

    with pytest.raises(
        TypeError,
        match="Series",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=strategy_returns(price_data.index),
            benchmark_returns=[],
            config=engine_config(),
        )


def test_benchmark_index_must_match():
    price_data = prices()

    benchmark = benchmark_returns(price_data.index).reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="index",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=strategy_returns(price_data.index),
            benchmark_returns=benchmark,
            config=engine_config(),
        )


def test_non_numeric_benchmark_rejected():
    price_data = prices()

    benchmark = pd.Series(
        ["bad"] * len(price_data),
        index=price_data.index,
    )

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=strategy_returns(price_data.index),
            benchmark_returns=benchmark,
            config=engine_config(),
        )


def test_non_finite_benchmark_rejected():
    price_data = prices()

    benchmark = benchmark_returns(price_data.index)

    benchmark.iloc[0] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        run_engine(
            prices=price_data,
            strategy_returns=strategy_returns(price_data.index),
            benchmark_returns=benchmark,
            config=engine_config(),
        )
