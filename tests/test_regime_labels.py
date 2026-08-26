import pytest

from trading_engine.regime import (
    MarketRegime,
    TrendRegime,
    VolatilityRegime,
    combine_regimes,
)


@pytest.mark.parametrize(
    ("volatility", "trend", "expected"),
    [
        (
            VolatilityRegime.LOW,
            TrendRegime.BEAR,
            MarketRegime.LOW_VOL_BEAR,
        ),
        (
            VolatilityRegime.LOW,
            TrendRegime.SIDEWAYS,
            MarketRegime.LOW_VOL_SIDEWAYS,
        ),
        (
            VolatilityRegime.LOW,
            TrendRegime.BULL,
            MarketRegime.LOW_VOL_BULL,
        ),
        (
            VolatilityRegime.NORMAL,
            TrendRegime.BEAR,
            MarketRegime.NORMAL_VOL_BEAR,
        ),
        (
            VolatilityRegime.NORMAL,
            TrendRegime.SIDEWAYS,
            MarketRegime.NORMAL_VOL_SIDEWAYS,
        ),
        (
            VolatilityRegime.NORMAL,
            TrendRegime.BULL,
            MarketRegime.NORMAL_VOL_BULL,
        ),
        (
            VolatilityRegime.HIGH,
            TrendRegime.BEAR,
            MarketRegime.HIGH_VOL_BEAR,
        ),
        (
            VolatilityRegime.HIGH,
            TrendRegime.SIDEWAYS,
            MarketRegime.HIGH_VOL_SIDEWAYS,
        ),
        (
            VolatilityRegime.HIGH,
            TrendRegime.BULL,
            MarketRegime.HIGH_VOL_BULL,
        ),
    ],
)
def test_combine_regimes(
    volatility,
    trend,
    expected,
):
    assert (
        combine_regimes(
            volatility,
            trend,
        )
        is expected
    )


def test_invalid_volatility_regime_rejected():
    with pytest.raises(
        TypeError,
        match="VolatilityRegime",
    ):
        combine_regimes(
            "high",
            TrendRegime.BULL,
        )


def test_invalid_trend_regime_rejected():
    with pytest.raises(
        TypeError,
        match="TrendRegime",
    ):
        combine_regimes(
            VolatilityRegime.HIGH,
            "bull",
        )
