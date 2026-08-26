import numpy as np
import pandas as pd
import pytest

from trading_engine.production import (
    EngineConfig,
    ProductionValidationResult,
    sanitize_missing_data,
    validate_initial_equity,
    validate_production_inputs,
)
from trading_engine.research import (
    ResearchConfig,
)


def index(
    observations: int = 80,
) -> pd.DatetimeIndex:
    return pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )


def prices(
    observations: int = 80,
) -> pd.Series:
    values = np.linspace(
        100.0,
        130.0,
        observations,
    )

    return pd.Series(
        values,
        index=index(observations),
        dtype=float,
    )


def strategy_returns(
    observations: int = 80,
) -> pd.DataFrame:
    x = np.arange(
        observations,
        dtype=float,
    )

    return pd.DataFrame(
        {
            "trend": np.sin(x / 5.0) * 0.01,
            "momentum": np.cos(x / 6.0) * 0.01,
            "mean_reversion": -np.sin(x / 7.0) * 0.008,
            "volatility": np.sin(x / 3.0) * 0.005,
            "stat_arb": np.cos(x / 4.0) * 0.006,
        },
        index=index(observations),
    )


def benchmark_returns(
    observations: int = 80,
) -> pd.Series:
    return pd.Series(
        np.zeros(observations),
        index=index(observations),
        dtype=float,
    )


def config(
    *,
    fail_on_missing_data: bool = True,
) -> EngineConfig:
    return EngineConfig(
        research=ResearchConfig(
            volatility_window=10,
            trend_window=20,
            momentum_lookback=10,
        ),
        fail_on_missing_data=(fail_on_missing_data),
    )


def test_validate_production_inputs():
    result = validate_production_inputs(
        prices=prices(),
        strategy_returns=strategy_returns(),
        benchmark_returns=benchmark_returns(),
        config=config(),
    )

    assert isinstance(
        result,
        ProductionValidationResult,
    )

    assert result.observations == 80
    assert result.strategy_count == 5
    assert result.benchmark_present
    assert not result.has_missing_data


def test_validation_without_benchmark():
    result = validate_production_inputs(
        prices=prices(),
        strategy_returns=strategy_returns(),
        config=config(),
    )

    assert not result.benchmark_present
    assert result.missing_benchmark_values == 0


def test_config_requires_engine_config():
    with pytest.raises(
        TypeError,
        match="EngineConfig",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=strategy_returns(),
            config="bad",
        )


def test_prices_require_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        validate_production_inputs(
            prices=[],
            strategy_returns=strategy_returns(),
            config=config(),
        )


def test_strategy_returns_require_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=[],
            config=config(),
        )


def test_prices_require_datetime_index():
    values = prices().reset_index(drop=True)

    with pytest.raises(
        TypeError,
        match="DatetimeIndex",
    ):
        validate_production_inputs(
            prices=values,
            strategy_returns=strategy_returns(),
            config=config(),
        )


def test_strategy_returns_require_datetime_index():
    values = strategy_returns().reset_index(drop=True)

    with pytest.raises(
        TypeError,
        match="DatetimeIndex",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=values,
            config=config(),
        )


def test_indexes_must_match():
    values = strategy_returns()

    values.index = pd.date_range(
        "2027-01-01",
        periods=len(values),
        freq="D",
    )

    with pytest.raises(
        ValueError,
        match="matching indexes",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=values,
            config=config(),
        )


def test_duplicate_timestamp_rejected():
    values = prices()

    duplicate_index = list(values.index)

    duplicate_index[1] = duplicate_index[0]

    values.index = pd.DatetimeIndex(duplicate_index)

    with pytest.raises(
        ValueError,
        match="unique",
    ):
        validate_production_inputs(
            prices=values,
            strategy_returns=strategy_returns(),
            config=config(),
        )


def test_unsorted_timestamp_rejected():
    values = prices()

    values = values.sort_index(ascending=False)

    with pytest.raises(
        ValueError,
        match="sorted",
    ):
        validate_production_inputs(
            prices=values,
            strategy_returns=strategy_returns(),
            config=config(),
        )


def test_non_positive_prices_rejected():
    values = prices()

    values.iloc[10] = 0.0

    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        validate_production_inputs(
            prices=values,
            strategy_returns=strategy_returns(),
            config=config(),
        )


def test_non_finite_price_rejected():
    values = prices()

    values.iloc[10] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        validate_production_inputs(
            prices=values,
            strategy_returns=strategy_returns(),
            config=config(),
        )


def test_non_finite_strategy_return_rejected():
    values = strategy_returns()

    values.iloc[
        5,
        0,
    ] = np.inf

    with pytest.raises(
        ValueError,
        match="finite",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=values,
            config=config(),
        )


def test_missing_values_fail_when_strict():
    values = strategy_returns()

    values.iloc[
        5,
        0,
    ] = np.nan

    with pytest.raises(
        ValueError,
        match="missing",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=values,
            config=config(fail_on_missing_data=True),
        )


def test_missing_values_allowed_when_configured():
    values = strategy_returns()

    values.iloc[
        5,
        0,
    ] = np.nan

    result = validate_production_inputs(
        prices=prices(),
        strategy_returns=values,
        config=config(fail_on_missing_data=False),
    )

    assert result.has_missing_data
    assert result.missing_strategy_values == 1


def test_missing_price_is_counted():
    values = prices()

    values.iloc[3] = np.nan

    result = validate_production_inputs(
        prices=values,
        strategy_returns=strategy_returns(),
        config=config(fail_on_missing_data=False),
    )

    assert result.missing_price_values == 1


def test_missing_benchmark_is_counted():
    benchmark = benchmark_returns()

    benchmark.iloc[7] = np.nan

    result = validate_production_inputs(
        prices=prices(),
        strategy_returns=strategy_returns(),
        benchmark_returns=benchmark,
        config=config(fail_on_missing_data=False),
    )

    assert result.missing_benchmark_values == 1


def test_benchmark_index_must_match():
    benchmark = benchmark_returns()

    benchmark.index = pd.date_range(
        "2027-01-01",
        periods=len(benchmark),
        freq="D",
    )

    with pytest.raises(
        ValueError,
        match="match prices index",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=strategy_returns(),
            benchmark_returns=benchmark,
            config=config(),
        )


def test_insufficient_history_rejected():
    observations = 10

    with pytest.raises(
        ValueError,
        match="insufficient observations",
    ):
        validate_production_inputs(
            prices=prices(observations),
            strategy_returns=strategy_returns(observations),
            config=config(),
        )


def test_duplicate_strategy_columns_rejected():
    values = strategy_returns()

    values.columns = [
        "trend",
        "trend",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="columns must be unique",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=values,
            config=config(),
        )


def test_empty_strategy_name_rejected():
    values = strategy_returns()

    values.columns = [
        "",
        "momentum",
        "mean_reversion",
        "volatility",
        "stat_arb",
    ]

    with pytest.raises(
        ValueError,
        match="non-empty strings",
    ):
        validate_production_inputs(
            prices=prices(),
            strategy_returns=values,
            config=config(),
        )


def test_sanitize_missing_data():
    price_values = prices()
    strategy_values = strategy_returns()
    benchmark = benchmark_returns()

    price_values.iloc[2] = np.nan

    strategy_values.iloc[
        3,
        0,
    ] = np.nan

    benchmark.iloc[4] = np.nan

    (
        clean_prices,
        clean_strategies,
        clean_benchmark,
    ) = sanitize_missing_data(
        prices=price_values,
        strategy_returns=strategy_values,
        benchmark_returns=benchmark,
    )

    assert len(clean_prices) == 77

    assert len(clean_strategies) == 77

    assert clean_benchmark is not None

    assert len(clean_benchmark) == 77

    assert not clean_prices.isna().any()

    assert not clean_strategies.isna().any().any()

    assert not clean_benchmark.isna().any()


def test_sanitize_without_benchmark():
    values = prices()
    strategies = strategy_returns()

    strategies.iloc[
        0,
        0,
    ] = np.nan

    (
        clean_prices,
        clean_strategies,
        clean_benchmark,
    ) = sanitize_missing_data(
        prices=values,
        strategy_returns=strategies,
    )

    assert len(clean_prices) == 79

    assert len(clean_strategies) == 79

    assert clean_benchmark is None


def test_sanitize_requires_price_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        sanitize_missing_data(
            prices=[],
            strategy_returns=strategy_returns(),
        )


def test_sanitize_requires_strategy_dataframe():
    with pytest.raises(
        TypeError,
        match="DataFrame",
    ):
        sanitize_missing_data(
            prices=prices(),
            strategy_returns=[],
        )


def test_sanitize_benchmark_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        sanitize_missing_data(
            prices=prices(),
            strategy_returns=strategy_returns(),
            benchmark_returns=[],
        )


def test_sanitize_rejects_all_missing():
    price_values = prices(5)

    strategy_values = strategy_returns(5)

    strategy_values.iloc[:, :] = np.nan

    with pytest.raises(
        ValueError,
        match="no observations remain",
    ):
        sanitize_missing_data(
            prices=price_values,
            strategy_returns=strategy_values,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "1000",
    ],
)
def test_initial_equity_requires_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        validate_initial_equity(value)


def test_initial_equity_must_be_finite():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        validate_initial_equity(np.inf)


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        -1.0,
    ],
)
def test_initial_equity_must_be_positive(
    value,
):
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        validate_initial_equity(value)


def test_initial_equity_returns_float():
    assert validate_initial_equity(1000) == pytest.approx(1000.0)
