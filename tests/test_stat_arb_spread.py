import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    construct_spread,
    rolling_spread_zscore,
)


def series(
    values,
):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


def test_construct_spread():
    x = series([10, 11, 12])

    y = series([25, 27, 29])

    result = construct_spread(
        y,
        x,
        hedge_ratio=2.0,
        intercept=5.0,
    )

    assert np.allclose(
        result,
        0.0,
    )

    assert result.name == "spread"


@pytest.mark.parametrize(
    "name,value",
    [
        (
            "hedge_ratio",
            True,
        ),
        (
            "hedge_ratio",
            "2",
        ),
        (
            "intercept",
            True,
        ),
        (
            "intercept",
            "1",
        ),
    ],
)
def test_spread_parameters_must_be_numeric(
    name,
    value,
):
    kwargs = {
        "hedge_ratio": 2.0,
        "intercept": 1.0,
    }

    kwargs[name] = value

    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        construct_spread(
            series([10, 11]),
            series([5, 6]),
            **kwargs,
        )


def test_non_finite_hedge_ratio_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        construct_spread(
            series([10, 11]),
            series([5, 6]),
            hedge_ratio=np.inf,
        )


def test_rolling_zscore():
    spread = series([1, 2, 3, 4, 5])

    result = rolling_spread_zscore(
        spread,
        window=3,
    )

    assert result.isna().sum() == 2

    assert result.iloc[-1] == pytest.approx(1.0)


def test_constant_window_produces_nan_zscore():
    result = rolling_spread_zscore(
        series([1, 1, 1, 1]),
        window=2,
    )

    assert result.isna().all()


@pytest.mark.parametrize(
    "window",
    [
        True,
        2.5,
        "2",
    ],
)
def test_window_must_be_integer(
    window,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_spread_zscore(
            series([1, 2, 3]),
            window=window,
        )


def test_window_must_be_at_least_two():
    with pytest.raises(
        ValueError,
        match="at least 2",
    ):
        rolling_spread_zscore(
            series([1, 2, 3]),
            window=1,
        )


def test_minimum_periods_must_be_valid():
    with pytest.raises(
        ValueError,
        match="between 2 and window",
    ):
        rolling_spread_zscore(
            series([1, 2, 3]),
            window=3,
            minimum_periods=1,
        )
