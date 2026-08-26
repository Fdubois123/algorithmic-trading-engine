import numpy as np
import pandas as pd
import pytest

from trading_engine.regime import (
    TrendRegime,
    classify_trend_regime,
    rolling_trend_regime,
    rolling_trend_strength,
)


def price_series(
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


def test_uptrend_has_positive_strength():
    prices = price_series(
        np.linspace(
            100,
            150,
            50,
        )
    )

    result = rolling_trend_strength(
        prices,
        window=10,
    )

    assert result.iloc[-1] > 0


def test_downtrend_has_negative_strength():
    prices = price_series(
        np.linspace(
            150,
            100,
            50,
        )
    )

    result = rolling_trend_strength(
        prices,
        window=10,
    )

    assert result.iloc[-1] < 0


def test_trend_strength_has_warmup():
    prices = price_series(
        np.linspace(
            100,
            120,
            20,
        )
    )

    result = rolling_trend_strength(
        prices,
        window=5,
    )

    assert result.iloc[:4].isna().all()
    assert result.iloc[4:].notna().all()


def test_bull_classification():
    assert (
        classify_trend_regime(
            0.01,
            threshold=0.001,
        )
        is TrendRegime.BULL
    )


def test_bear_classification():
    assert (
        classify_trend_regime(
            -0.01,
            threshold=0.001,
        )
        is TrendRegime.BEAR
    )


def test_sideways_classification():
    assert (
        classify_trend_regime(
            0.0001,
            threshold=0.001,
        )
        is TrendRegime.SIDEWAYS
    )


def test_negative_threshold_rejected():
    with pytest.raises(
        ValueError,
        match="negative",
    ):
        classify_trend_regime(
            0.01,
            threshold=-0.1,
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        "0.01",
    ],
)
def test_trend_strength_requires_numeric(
    value,
):
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        classify_trend_regime(value)


def test_prices_must_be_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        rolling_trend_strength([100, 101])


def test_empty_prices_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        rolling_trend_strength(pd.Series(dtype=float))


def test_non_numeric_prices_rejected():
    with pytest.raises(
        TypeError,
        match="numeric",
    ):
        rolling_trend_strength(pd.Series(["a", "b"]))


def test_non_finite_prices_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        rolling_trend_strength(
            price_series(
                [
                    100,
                    np.inf,
                ]
            )
        )


def test_non_positive_prices_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        rolling_trend_strength(
            price_series(
                [
                    100,
                    0,
                ]
            )
        )


def test_rolling_trend_regime():
    prices = price_series(
        np.linspace(
            100,
            160,
            50,
        )
    )

    result = rolling_trend_regime(
        prices,
        window=10,
        threshold=0.0001,
    )

    valid = result.dropna()

    assert not valid.empty

    assert valid.iloc[-1] == TrendRegime.BULL.value
