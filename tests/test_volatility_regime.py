import numpy as np
import pandas as pd
import pytest

from trading_engine.regime import (
    VolatilityRegime,
    classify_volatility_regime,
    rolling_realized_volatility,
    rolling_volatility_regime,
)


def returns_series(
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


def test_rolling_realized_volatility():
    returns = returns_series(
        [
            0.01,
            -0.01,
            0.02,
            -0.02,
            0.01,
        ]
    )

    result = rolling_realized_volatility(
        returns,
        window=3,
        periods_per_year=252,
    )

    assert result.iloc[:2].isna().all()
    assert result.iloc[2:].notna().all()
    assert result.name == "realized_volatility"


def test_low_volatility_classification():
    assert (
        classify_volatility_regime(
            0.10,
            low_threshold=0.15,
            high_threshold=0.25,
        )
        is VolatilityRegime.LOW
    )


def test_normal_volatility_classification():
    assert (
        classify_volatility_regime(
            0.20,
            low_threshold=0.15,
            high_threshold=0.25,
        )
        is VolatilityRegime.NORMAL
    )


def test_high_volatility_classification():
    assert (
        classify_volatility_regime(
            0.30,
            low_threshold=0.15,
            high_threshold=0.25,
        )
        is VolatilityRegime.HIGH
    )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "0.2",
    ],
)
def test_volatility_classification_requires_numeric_value(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        classify_volatility_regime(
            value,
            low_threshold=0.15,
            high_threshold=0.25,
        )


def test_negative_volatility_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        classify_volatility_regime(
            -0.1,
            low_threshold=0.15,
            high_threshold=0.25,
        )


def test_invalid_threshold_order_rejected():
    with pytest.raises(
        ValueError,
        match="greater",
    ):
        classify_volatility_regime(
            0.2,
            low_threshold=0.3,
            high_threshold=0.2,
        )


def test_returns_must_be_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        rolling_realized_volatility([0.1, 0.2])


def test_empty_returns_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        rolling_realized_volatility(pd.Series(dtype=float))


def test_non_numeric_returns_rejected():
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        rolling_realized_volatility(pd.Series(["a", "b"]))


def test_non_finite_returns_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        rolling_realized_volatility(
            returns_series(
                [
                    0.01,
                    np.inf,
                ]
            )
        )


@pytest.mark.parametrize(
    "window",
    [
        True,
        2.5,
        "20",
    ],
)
def test_window_requires_integer(
    window,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_realized_volatility(
            returns_series([0.1, 0.2, 0.3]),
            window=window,
        )


def test_window_requires_at_least_two():
    with pytest.raises(
        ValueError,
        match="at least 2",
    ):
        rolling_realized_volatility(
            returns_series([0.1, 0.2]),
            window=1,
        )


@pytest.mark.parametrize(
    "periods",
    [
        True,
        252.5,
        "252",
    ],
)
def test_periods_per_year_requires_integer(
    periods,
):
    with pytest.raises(
        TypeError,
        match="integer",
    ):
        rolling_realized_volatility(
            returns_series([0.1, 0.2]),
            periods_per_year=periods,
        )


def test_periods_per_year_requires_positive_value():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        rolling_realized_volatility(
            returns_series([0.1, 0.2]),
            periods_per_year=0,
        )


def test_rolling_volatility_regime():
    values = np.concatenate(
        [
            np.full(
                20,
                0.001,
            ),
            np.sin(np.arange(40)) * 0.01,
            np.sin(np.arange(40)) * 0.05,
        ]
    )

    result = rolling_volatility_regime(
        returns_series(values),
        window=10,
    )

    valid = result.dropna()

    assert not valid.empty

    assert set(valid.unique()).issubset(
        {
            "low",
            "normal",
            "high",
        }
    )


@pytest.mark.parametrize(
    ("low", "high"),
    [
        (
            0,
            0.75,
        ),
        (
            0.25,
            1,
        ),
        (
            0.8,
            0.2,
        ),
    ],
)
def test_invalid_quantiles_rejected(
    low,
    high,
):
    with pytest.raises(ValueError):
        rolling_volatility_regime(
            returns_series(
                np.linspace(
                    -0.01,
                    0.01,
                    30,
                )
            ),
            window=5,
            low_quantile=low,
            high_quantile=high,
        )
