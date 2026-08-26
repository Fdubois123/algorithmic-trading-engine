import numpy as np
import pandas as pd
import pytest

from trading_engine.stat_arb import (
    PairPosition,
    PairsTradingStrategy,
    backtest_pair_walk_forward,
    construct_spread,
    estimate_hedge_ratio,
    residual_adf_statistic,
    rolling_spread_zscore,
    validate_price_series,
    walk_forward_zscore,
)
from trading_engine.stat_arb.walk_forward import (
    _validate_positive_number,
)


def series(values):
    return pd.Series(
        values,
        index=pd.date_range(
            "2026-01-01",
            periods=len(values),
            freq="D",
        ),
        dtype=float,
    )


# ---------------------------------------------------------------------------
# hedge.py
# ---------------------------------------------------------------------------


def test_hedge_constant_dependent_series_has_finite_r_squared():
    x = series([1, 2, 3, 4, 5])

    y = series([10, 10, 10, 10, 10])

    result = estimate_hedge_ratio(
        y,
        x,
    )

    assert np.isfinite(result.r_squared)


def test_no_intercept_constant_dependent_series():
    x = series([1, 2, 3, 4, 5])

    y = series([10, 10, 10, 10, 10])

    result = estimate_hedge_ratio(
        y,
        x,
        include_intercept=False,
    )

    assert np.isfinite(result.beta)


# ---------------------------------------------------------------------------
# spread.py
# ---------------------------------------------------------------------------


def test_intercept_must_be_finite():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        construct_spread(
            series([10, 11, 12]),
            series([5, 6, 7]),
            hedge_ratio=1.0,
            intercept=np.inf,
        )


def test_spread_must_be_series_for_zscore():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        rolling_spread_zscore(
            [1, 2, 3],
            window=2,
        )


def test_empty_spread_rejected_for_zscore():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        rolling_spread_zscore(
            pd.Series(dtype=float),
            window=2,
        )


def test_non_numeric_spread_rejected_for_zscore():
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        rolling_spread_zscore(
            pd.Series(["a", "b", "c"]),
            window=2,
        )


def test_non_finite_spread_rejected_for_zscore():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        rolling_spread_zscore(
            pd.Series([1.0, np.inf, 2.0]),
            window=2,
        )


@pytest.mark.parametrize(
    "minimum_periods",
    [
        True,
        2.5,
        "2",
    ],
)
def test_minimum_periods_must_be_integer(
    minimum_periods,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_spread_zscore(
            series([1, 2, 3, 4]),
            window=3,
            minimum_periods=minimum_periods,
        )


# ---------------------------------------------------------------------------
# pairs.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "minimum",
    [
        True,
        2.5,
        "2",
    ],
)
def test_minimum_observations_must_be_integer(
    minimum,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        validate_price_series(
            series([1, 2, 3]),
            minimum_observations=minimum,
        )


def test_minimum_observations_must_be_positive():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        validate_price_series(
            series([1, 2, 3]),
            minimum_observations=0,
        )


def test_price_series_requires_minimum_length():
    with pytest.raises(
        ValueError,
        match="at least",
    ):
        validate_price_series(
            series([1, 2]),
            minimum_observations=3,
        )


# ---------------------------------------------------------------------------
# cointegration.py
# ---------------------------------------------------------------------------


def test_positive_gamma_branch_returns_non_stationary():
    values = [1.0]

    for _ in range(20):
        values.append(1.2 * values[-1] + 0.5)

    result = residual_adf_statistic(
        series(values),
        critical_value=-2.0,
    )

    assert not result.stationary


def test_zeroish_gamma_branch_is_finite_or_infinite():
    values = np.linspace(
        1,
        2,
        30,
    )

    result = residual_adf_statistic(
        series(values),
        critical_value=-2.0,
    )

    assert np.isfinite(result.statistic) or np.isinf(result.statistic)


# ---------------------------------------------------------------------------
# strategy.py
# ---------------------------------------------------------------------------


def test_flat_signal_inside_entry_band_does_not_change():
    strategy = PairsTradingStrategy(
        entry_z=2.0,
        exit_z=0.5,
    )

    signal = strategy.update(0.2)

    assert signal.position is PairPosition.FLAT
    assert not signal.changed


def test_short_position_can_remain_open():
    strategy = PairsTradingStrategy(
        entry_z=2.0,
        exit_z=0.5,
    )

    strategy.update(2.5)

    signal = strategy.update(1.0)

    assert signal.position is PairPosition.SHORT_SPREAD
    assert not signal.changed


# ---------------------------------------------------------------------------
# walk_forward.py
# ---------------------------------------------------------------------------


def test_walk_forward_zscore_requires_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        walk_forward_zscore(
            [1, 2, 3],
            window=2,
        )


def test_walk_forward_zscore_rejects_empty_series():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        walk_forward_zscore(
            pd.Series(dtype=float),
            window=2,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "1",
    ],
)
def test_validate_positive_number_rejects_non_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        _validate_positive_number(
            value,
            name="value",
        )


def test_validate_positive_number_rejects_non_finite():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        _validate_positive_number(
            np.inf,
            name="value",
        )


def test_validate_positive_number_rejects_negative_when_zero_allowed():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        _validate_positive_number(
            -1,
            name="value",
            allow_zero=True,
        )


def test_walk_forward_negative_transaction_cost_rejected():
    dependent = series(
        np.linspace(
            100,
            130,
            80,
        )
    )

    independent = series(
        np.linspace(
            50,
            70,
            80,
        )
    )

    with pytest.raises(
        ValueError,
        match="negative",
    ):
        backtest_pair_walk_forward(
            dependent,
            independent,
            estimation_window=20,
            zscore_window=5,
            transaction_cost_rate=-0.01,
        )


def test_walk_forward_negative_gross_exposure_rejected():
    dependent = series(
        np.linspace(
            100,
            130,
            80,
        )
    )

    independent = series(
        np.linspace(
            50,
            70,
            80,
        )
    )

    with pytest.raises(
        ValueError,
        match="negative",
    ):
        backtest_pair_walk_forward(
            dependent,
            independent,
            estimation_window=20,
            zscore_window=5,
            gross_exposure=-1,
        )
