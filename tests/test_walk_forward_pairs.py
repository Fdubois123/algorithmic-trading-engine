import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb.walk_forward import (
    WalkForwardPairResult,
    backtest_pair_walk_forward,
    walk_forward_zscore,
)


def pair_prices(
    observations: int = 180,
):
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    independent = np.linspace(
        50.0,
        100.0,
        observations,
    )

    spread = 2.0 * np.sin(np.arange(observations) / 5.0)

    dependent = 5.0 + 1.5 * independent + spread

    return (
        pd.Series(
            dependent,
            index=index,
        ),
        pd.Series(
            independent,
            index=index,
        ),
    )


def test_walk_forward_zscore_has_warmup():
    spread = pd.Series(
        np.arange(
            20,
            dtype=float,
        ),
        index=pd.date_range(
            "2026-01-01",
            periods=20,
            freq="D",
        ),
    )

    result = walk_forward_zscore(
        spread,
        window=5,
    )

    assert result.iloc[:4].isna().all()
    assert result.iloc[4:].notna().all()


def test_constant_spread_produces_nan_zscores():
    spread = pd.Series(
        np.ones(20),
        index=pd.date_range(
            "2026-01-01",
            periods=20,
            freq="D",
        ),
    )

    result = walk_forward_zscore(
        spread,
        window=5,
    )

    assert result.isna().all()


@pytest.mark.parametrize(
    "window",
    [
        True,
        2.5,
        "5",
    ],
)
def test_zscore_window_requires_integer(
    window,
):
    spread = pd.Series(
        np.arange(
            10,
            dtype=float,
        )
    )

    with pytest.raises(
        TypeError,
        match="integer",
    ):
        walk_forward_zscore(
            spread,
            window=window,
        )


def test_zscore_window_must_be_at_least_two():
    with pytest.raises(
        ValueError,
        match="at least 2",
    ):
        walk_forward_zscore(
            pd.Series([1.0, 2.0]),
            window=1,
        )


def test_walk_forward_backtest_result():
    dependent, independent = pair_prices()

    result = backtest_pair_walk_forward(
        dependent,
        independent,
        estimation_window=40,
        zscore_window=10,
        entry_z=1.0,
        exit_z=0.2,
    )

    assert isinstance(
        result,
        WalkForwardPairResult,
    )

    assert result.observations == 180
    assert np.isfinite(result.final_equity)

    assert np.isfinite(result.total_return)


def test_rolling_method_is_recorded():
    dependent, independent = pair_prices()

    result = backtest_pair_walk_forward(
        dependent,
        independent,
        hedge_method="rolling",
        estimation_window=40,
        zscore_window=10,
    )

    assert result.hedge_method == "rolling"


def test_expanding_method_runs():
    dependent, independent = pair_prices()

    result = backtest_pair_walk_forward(
        dependent,
        independent,
        hedge_method="expanding",
        estimation_window=40,
        zscore_window=10,
    )

    assert result.hedge_method == "expanding"


def test_invalid_hedge_method_rejected():
    dependent, independent = pair_prices()

    with pytest.raises(
        ValueError,
        match="rolling.*expanding",
    ):
        backtest_pair_walk_forward(
            dependent,
            independent,
            hedge_method="future",
            estimation_window=40,
            zscore_window=10,
        )


def test_first_bar_has_zero_exposure():
    dependent, independent = pair_prices()

    result = backtest_pair_walk_forward(
        dependent,
        independent,
        estimation_window=40,
        zscore_window=10,
        entry_z=1.0,
    )

    assert result.frame["dependent_weight"].iloc[0] == 0

    assert result.frame["independent_weight"].iloc[0] == 0


def test_transaction_costs_reduce_equity():
    dependent, independent = pair_prices()

    frictionless = backtest_pair_walk_forward(
        dependent,
        independent,
        estimation_window=40,
        zscore_window=10,
        entry_z=1.0,
        exit_z=0.2,
        transaction_cost_rate=0.0,
    )

    costly = backtest_pair_walk_forward(
        dependent,
        independent,
        estimation_window=40,
        zscore_window=10,
        entry_z=1.0,
        exit_z=0.2,
        transaction_cost_rate=0.001,
    )

    assert costly.final_equity <= frictionless.final_equity


def test_zero_exposure_preserves_capital():
    dependent, independent = pair_prices()

    result = backtest_pair_walk_forward(
        dependent,
        independent,
        estimation_window=40,
        zscore_window=10,
        gross_exposure=0.0,
    )

    assert result.final_equity == pytest.approx(100_000.0)


def test_frame_contains_walk_forward_parameters():
    dependent, independent = pair_prices()

    result = backtest_pair_walk_forward(
        dependent,
        independent,
        estimation_window=40,
        zscore_window=10,
    )

    assert {
        "alpha",
        "beta",
        "spread",
        "zscore",
        "equity",
    }.issubset(result.frame.columns)


def test_invalid_initial_capital_rejected():
    dependent, independent = pair_prices()

    with pytest.raises(ValueError):
        backtest_pair_walk_forward(
            dependent,
            independent,
            estimation_window=40,
            initial_capital=0,
        )


def test_invalid_transaction_cost_rejected():
    dependent, independent = pair_prices()

    with pytest.raises(
        ValueError,
        match="smaller than 1",
    ):
        backtest_pair_walk_forward(
            dependent,
            independent,
            estimation_window=40,
            transaction_cost_rate=1.0,
        )
