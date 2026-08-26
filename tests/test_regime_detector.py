import numpy as np
import pandas as pd
import pytest

from trading_engine.regime import (
    MarketRegime,
    RegimeDetectionResult,
    detect_market_regimes,
    price_returns,
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


def market_prices(
    observations: int = 150,
) -> pd.Series:
    trend = np.linspace(
        100,
        140,
        observations,
    )

    oscillation = np.sin(np.arange(observations) / 4.0) * 2.0

    return price_series(trend + oscillation)


def test_price_returns():
    prices = price_series(
        [
            100,
            110,
            121,
        ]
    )

    result = price_returns(prices)

    assert len(result) == 2

    assert np.allclose(
        result,
        [
            0.10,
            0.10,
        ],
    )


def test_detect_market_regimes():
    result = detect_market_regimes(
        market_prices(),
        volatility_window=10,
        trend_window=20,
        trend_threshold=0.0001,
    )

    assert isinstance(
        result,
        RegimeDetectionResult,
    )

    assert result.observations == 150

    assert {
        "price",
        "return",
        "realized_volatility",
        "volatility_regime",
        "trend_strength",
        "trend_regime",
        "market_regime",
    } == set(result.frame.columns)


def test_latest_regime():
    result = detect_market_regimes(
        market_prices(),
        volatility_window=10,
        trend_window=20,
        trend_threshold=0.0001,
    )

    assert isinstance(
        result.latest_regime,
        MarketRegime,
    )


def test_market_regimes_are_valid_values():
    result = detect_market_regimes(
        market_prices(),
        volatility_window=10,
        trend_window=20,
    )

    valid = result.frame["market_regime"].dropna()

    assert not valid.empty

    allowed = {regime.value for regime in MarketRegime}

    assert set(valid.unique()).issubset(allowed)


def test_regime_detector_preserves_index():
    prices = market_prices()

    result = detect_market_regimes(
        prices,
        volatility_window=10,
        trend_window=20,
    )

    assert result.frame.index.equals(prices.index)


def test_prices_must_be_series():
    with pytest.raises(
        TypeError,
        match="Series",
    ):
        detect_market_regimes([100, 101, 102])


def test_empty_prices_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        detect_market_regimes(pd.Series(dtype=float))


def test_non_finite_prices_rejected():
    with pytest.raises(
        ValueError,
        match="finite",
    ):
        detect_market_regimes(
            price_series(
                [
                    100,
                    101,
                    np.inf,
                ]
            )
        )


def test_non_positive_prices_rejected():
    with pytest.raises(
        ValueError,
        match="strictly positive",
    ):
        detect_market_regimes(
            price_series(
                [
                    100,
                    0,
                    101,
                ]
            )
        )


def test_duplicate_index_rejected():
    prices = pd.Series(
        [
            100.0,
            101.0,
        ],
        index=pd.DatetimeIndex(
            [
                "2026-01-01",
                "2026-01-01",
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match="duplicates",
    ):
        detect_market_regimes(prices)


def test_unsorted_index_rejected():
    prices = pd.Series(
        [
            100.0,
            101.0,
        ],
        index=pd.DatetimeIndex(
            [
                "2026-01-02",
                "2026-01-01",
            ]
        ),
    )

    with pytest.raises(
        ValueError,
        match="sorted",
    ):
        detect_market_regimes(prices)


def test_insufficient_history_rejected():
    prices = price_series(
        np.linspace(
            100,
            110,
            10,
        )
    )

    with pytest.raises(
        ValueError,
        match="enough observations",
    ):
        detect_market_regimes(
            prices,
            volatility_window=10,
            trend_window=20,
        )


def test_result_without_valid_regime_returns_none():
    frame = pd.DataFrame(
        {
            "market_regime": [
                pd.NA,
                pd.NA,
            ]
        }
    )

    result = RegimeDetectionResult(frame=frame)

    assert result.latest_regime is None
