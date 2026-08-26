import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb.rolling import (
    RollingHedgeResult,
    expanding_hedge_ratio,
    rolling_hedge_ratio,
    walk_forward_spread,
)


def pair_data(
    observations: int = 50,
):
    index = pd.date_range(
        "2026-01-01",
        periods=observations,
        freq="D",
    )

    independent = pd.Series(
        np.linspace(
            10,
            30,
            observations,
        ),
        index=index,
    )

    dependent = pd.Series(
        5.0 + 2.0 * independent.to_numpy(),
        index=index,
    )

    return dependent, independent


def test_rolling_hedge_recovers_beta():
    dependent, independent = pair_data()

    result = rolling_hedge_ratio(
        dependent,
        independent,
        window=10,
    )

    assert isinstance(
        result,
        RollingHedgeResult,
    )

    assert result.beta.iloc[-1] == pytest.approx(2.0)

    assert result.alpha.iloc[-1] == pytest.approx(5.0)


def test_rolling_hedge_has_warmup_nans():
    dependent, independent = pair_data()

    result = rolling_hedge_ratio(
        dependent,
        independent,
        window=10,
    )

    assert result.beta.iloc[:9].isna().all()
    assert result.beta.iloc[9:].notna().all()


def test_expanding_hedge_recovers_beta():
    dependent, independent = pair_data()

    result = expanding_hedge_ratio(
        dependent,
        independent,
        minimum_observations=10,
    )

    assert result.beta.iloc[-1] == pytest.approx(2.0)


def test_expanding_hedge_has_expected_warmup():
    dependent, independent = pair_data()

    result = expanding_hedge_ratio(
        dependent,
        independent,
        minimum_observations=10,
    )

    assert result.beta.iloc[:9].isna().all()


def test_walk_forward_spread_is_zero_for_exact_pair():
    dependent, independent = pair_data()

    hedge = rolling_hedge_ratio(
        dependent,
        independent,
        window=10,
    )

    spread = walk_forward_spread(
        dependent,
        independent,
        hedge=hedge,
    )

    assert np.allclose(
        spread.dropna(),
        0.0,
        atol=1e-10,
    )


def test_rolling_result_observation_count():
    dependent, independent = pair_data(30)

    result = rolling_hedge_ratio(
        dependent,
        independent,
        window=5,
    )

    assert result.observations == 30


@pytest.mark.parametrize(
    "window",
    [
        True,
        3.5,
        "10",
    ],
)
def test_rolling_window_requires_integer(
    window,
):
    dependent, independent = pair_data()

    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_hedge_ratio(
            dependent,
            independent,
            window=window,
        )


@pytest.mark.parametrize(
    "window",
    [
        0,
        1,
        2,
    ],
)
def test_rolling_window_requires_minimum_three(
    window,
):
    dependent, independent = pair_data()

    with pytest.raises(
        ValueError,
        match="at least 3",
    ):
        rolling_hedge_ratio(
            dependent,
            independent,
            window=window,
        )
