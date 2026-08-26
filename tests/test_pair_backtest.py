import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    PairBacktestResult,
    backtest_pair,
)


def pair_prices(
    observations: int = 120,
) -> tuple[pd.Series, pd.Series]:
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    independent_values = np.linspace(
        50.0,
        80.0,
        observations,
    )

    spread = 2.0 * np.sin(np.arange(observations) / 4.0)

    dependent_values = 5.0 + 1.5 * independent_values + spread

    dependent = pd.Series(
        dependent_values,
        index=index,
    )

    independent = pd.Series(
        independent_values,
        index=index,
    )

    return (
        dependent,
        independent,
    )


def test_pair_backtest_result():
    dependent, independent = pair_prices()

    result = backtest_pair(
        dependent,
        independent,
        window=10,
        entry_z=1.0,
        exit_z=0.2,
    )

    assert isinstance(
        result,
        PairBacktestResult,
    )

    assert result.observations == 120

    assert result.initial_capital == pytest.approx(100_000.0)

    assert np.isfinite(result.final_equity)

    assert np.isfinite(result.total_return)


def test_backtest_frame_columns():
    dependent, independent = pair_prices()

    result = backtest_pair(
        dependent,
        independent,
        window=10,
        entry_z=1.0,
    )

    assert set(result.frame.columns) == {
        "dependent_price",
        "independent_price",
        "spread",
        "zscore",
        "position",
        "dependent_weight",
        "independent_weight",
        "turnover",
        "gross_return",
        "transaction_cost",
        "strategy_return",
        "equity",
    }


def test_backtest_hedge_ratio_is_positive():
    dependent, independent = pair_prices()

    result = backtest_pair(
        dependent,
        independent,
        window=10,
    )

    assert result.hedge_ratio > 0


def test_initial_period_has_no_exposure():
    dependent, independent = pair_prices()

    result = backtest_pair(
        dependent,
        independent,
        window=10,
        entry_z=1.0,
    )

    assert result.frame["dependent_weight"].iloc[0] == 0

    assert result.frame["independent_weight"].iloc[0] == 0


def test_transaction_costs_reduce_equity():
    dependent, independent = pair_prices()

    without_cost = backtest_pair(
        dependent,
        independent,
        window=10,
        entry_z=1.0,
        exit_z=0.2,
        transaction_cost_rate=0.0,
    )

    with_cost = backtest_pair(
        dependent,
        independent,
        window=10,
        entry_z=1.0,
        exit_z=0.2,
        transaction_cost_rate=0.001,
    )

    assert with_cost.final_equity <= without_cost.final_equity


def test_zero_gross_exposure_preserves_capital():
    dependent, independent = pair_prices()

    result = backtest_pair(
        dependent,
        independent,
        window=10,
        gross_exposure=0.0,
    )

    assert result.final_equity == pytest.approx(100_000.0)


def test_custom_initial_capital():
    dependent, independent = pair_prices()

    result = backtest_pair(
        dependent,
        independent,
        window=10,
        initial_capital=50_000,
    )

    assert result.initial_capital == pytest.approx(50_000)


@pytest.mark.parametrize(
    "capital",
    [
        0,
        -1,
        np.inf,
    ],
)
def test_invalid_initial_capital_rejected(
    capital,
):
    dependent, independent = pair_prices()

    with pytest.raises(ValueError):
        backtest_pair(
            dependent,
            independent,
            window=10,
            initial_capital=capital,
        )


def test_transaction_cost_rate_below_one():
    dependent, independent = pair_prices()

    with pytest.raises(
        ValueError,
        match="smaller than 1",
    ):
        backtest_pair(
            dependent,
            independent,
            window=10,
            transaction_cost_rate=1.0,
        )


def test_negative_transaction_cost_rejected():
    dependent, independent = pair_prices()

    with pytest.raises(ValueError):
        backtest_pair(
            dependent,
            independent,
            window=10,
            transaction_cost_rate=-0.1,
        )


def test_insufficient_history_rejected():
    dependent, independent = pair_prices(observations=5)

    with pytest.raises(
        ValueError,
        match="at least",
    ):
        backtest_pair(
            dependent,
            independent,
            window=10,
        )


def test_negative_hedge_relationship_rejected():
    index = pd.date_range(
        "2026-01-01",
        periods=30,
        freq="D",
    )

    independent = pd.Series(
        np.linspace(
            10,
            20,
            30,
        ),
        index=index,
    )

    dependent = pd.Series(
        100 - 2 * independent.to_numpy(),
        index=index,
    )

    with pytest.raises(
        ValueError,
        match="positive hedge ratio",
    ):
        backtest_pair(
            dependent,
            independent,
            window=5,
        )
