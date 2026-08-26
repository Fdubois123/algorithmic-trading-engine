import numpy as np
import pandas as pd
import pytest

from trading_engine.research import (
    ResearchConfig,
    ResearchResult,
    run_research_experiment,
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
        100,
        150,
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


def test_run_research_experiment():
    price_data = prices()

    result = run_research_experiment(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=ResearchConfig(
            volatility_window=10,
            trend_window=20,
            momentum_lookback=10,
            transaction_cost_bps=5.0,
        ),
    )

    assert isinstance(
        result,
        ResearchResult,
    )

    assert result.observations == len(price_data)

    assert np.isfinite(result.final_equity)


def test_result_contains_regime_features():
    price_data = prices()

    result = run_research_experiment(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=ResearchConfig(
            volatility_window=10,
            trend_window=20,
            momentum_lookback=10,
        ),
    )

    assert {
        "market_regime",
        "regime_confidence",
        "momentum_regime",
        "drawdown_regime",
    }.issubset(result.regime_frame.columns)


def test_first_applied_weights_are_zero():
    price_data = prices()

    result = run_research_experiment(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=ResearchConfig(
            volatility_window=10,
            trend_window=20,
            momentum_lookback=10,
        ),
    )

    assert np.allclose(
        result.applied_weights.iloc[0].to_numpy(),
        0.0,
    )


def test_default_config_supported():
    price_data = prices()

    result = run_research_experiment(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
    )

    assert isinstance(
        result,
        ResearchResult,
    )


def test_invalid_config_rejected():
    price_data = prices()

    with pytest.raises(
        TypeError,
        match="ResearchConfig",
    ):
        run_research_experiment(
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
        run_research_experiment(
            prices=price_data,
            strategy_returns=[],
            config=ResearchConfig(
                volatility_window=10,
                trend_window=20,
            ),
        )


def test_strategy_returns_index_must_match():
    price_data = prices()

    returns = strategy_returns(price_data.index).reset_index(drop=True)

    with pytest.raises(
        ValueError,
        match="index",
    ):
        run_research_experiment(
            prices=price_data,
            strategy_returns=returns,
            config=ResearchConfig(
                volatility_window=10,
                trend_window=20,
            ),
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
        run_research_experiment(
            prices=price_data,
            strategy_returns=returns,
            config=ResearchConfig(
                volatility_window=10,
                trend_window=20,
            ),
        )


def test_transaction_costs_are_recorded():
    price_data = prices()

    result = run_research_experiment(
        prices=price_data,
        strategy_returns=strategy_returns(price_data.index),
        config=ResearchConfig(
            volatility_window=10,
            trend_window=20,
            momentum_lookback=10,
            transaction_cost_bps=20.0,
        ),
    )

    assert result.total_transaction_cost >= 0.0
