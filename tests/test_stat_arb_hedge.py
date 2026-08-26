import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    HedgeRatioResult,
    estimate_hedge_ratio,
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


def test_hedge_ratio_recovers_linear_relationship():
    x = series([10, 11, 12, 13, 14])

    y = 5.0 + 2.0 * x

    result = estimate_hedge_ratio(
        y,
        x,
    )

    assert isinstance(
        result,
        HedgeRatioResult,
    )

    assert result.alpha == pytest.approx(5.0)

    assert result.beta == pytest.approx(2.0)

    assert result.r_squared == pytest.approx(1.0)

    assert result.residual_variance == pytest.approx(
        0.0,
        abs=1e-20,
    )


def test_hedge_ratio_without_intercept():
    x = series([10, 11, 12, 13])

    y = 3.0 * x

    result = estimate_hedge_ratio(
        y,
        x,
        include_intercept=False,
    )

    assert result.alpha == 0.0

    assert result.beta == pytest.approx(3.0)


def test_constant_independent_series_rejected():
    x = series([10, 10, 10, 10])

    y = series([20, 21, 22, 23])

    with pytest.raises(
        ValueError,
        match="non-zero variance",
    ):
        estimate_hedge_ratio(
            y,
            x,
        )


def test_observation_count_is_recorded():
    x = series([10, 11, 12, 13])

    y = 2.0 * x

    result = estimate_hedge_ratio(
        y,
        x,
    )

    assert result.observations == 4


def test_no_intercept_r_squared_is_finite():
    x = series([10, 11, 12, 13, 14])

    y = series([21, 22, 25, 26, 29])

    result = estimate_hedge_ratio(
        y,
        x,
        include_intercept=False,
    )

    assert np.isfinite(result.r_squared)
